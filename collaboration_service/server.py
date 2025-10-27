import logging
import os
import socketio
from socketio import AsyncRedisManager  # NEW: cluster manager
from aiohttp import web
import redis.asyncio as aioredis
import aiohttp
import asyncio
from schemas import CodeChangeData, CursorData, ErrorData, RoomJoinData

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

EXPIRY_TIME = 1800  # 30 minutes
INACTIVE_SESSION_TIMEOUT = 300  # 5 minutes in seconds
SESSION_SERVICE_URL = os.getenv("SESSION_SERVICE_URL", "http://session-service:8000")

SERVICE_PREFIX = os.getenv("SERVICE_PREFIX", "/collaboration-service-api")
if SERVICE_PREFIX and not SERVICE_PREFIX.startswith("/"):
    SERVICE_PREFIX = "/" + SERVICE_PREFIX
SERVICE_PREFIX = SERVICE_PREFIX.rstrip("/")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")  # centralize

# Track background tasks for ending sessions
session_end_tasks = {}


@web.middleware
async def fixed_prefix_middleware(request, handler):
    """
    Strip a configured prefix so the service can respond on both the root path
    and the prefixed path (e.g. behind nginx /collaboration-service-api).
    Also re-prefix Location headers on redirects.
    """
    target_request = request
    if SERVICE_PREFIX and request.path.startswith(SERVICE_PREFIX):
        stripped_path = request.path[len(SERVICE_PREFIX):] or "/"
        rel_url = request.rel_url.with_path(stripped_path)
        clone_kwargs = {"rel_url": rel_url, "headers": request.headers.copy()}
        target_request = request.clone(**clone_kwargs)
        logging.info("prefix rewrite: %s -> %s", request.path_qs, target_request.path_qs)

    response = await handler(target_request)

    logging.info(
        "REQ %s %s -> %s",
        request.method,
        target_request.path_qs if target_request is not request else request.path_qs,
        response.status,
    )

    if SERVICE_PREFIX:
        location = response.headers.get("Location")
        if location and location.startswith("/") and not location.startswith(SERVICE_PREFIX):
            response.headers["Location"] = f"{SERVICE_PREFIX}{location}"

    return response


async def health_check(request):
    """Health check endpoint for ALB"""
    return web.json_response({"status": "healthy"})


# --- Socket.IO server clustered with Redis ---
sio = socketio.AsyncServer(
    cors_allowed_origins="*",
    logger=True,
    engineio_logger=True,
    client_manager=AsyncRedisManager(REDIS_URL),  # <--- KEY LINE: cross-pod fanout
    ping_interval=25,
    ping_timeout=60,
)

# Create main app and ATTACH ONCE. Register middleware.
app = web.Application()
sio.attach(app, socketio_path="socket.io")

# Health routes (work at both /health and /{prefix}/health thanks to middleware)
app.router.add_get("/health", health_check)
app.router.add_get("/health/", health_check)

# Create prefixed subapp, attach socket.io again (so /prefix/socket.io works)
prefixed_app = web.Application()
sio.attach(prefixed_app, socketio_path="socket.io")
prefixed_app.router.add_get("/health", health_check)
prefixed_app.router.add_get("/health/", health_check)
app.add_subapp(SERVICE_PREFIX, prefixed_app)


# Initialize Redis connection (for cached code snapshots)
redis = None

async def init_redis():
    """Initialize Redis connection."""
    global redis
    try:
        redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        logger.info(f"Connected to Redis at {REDIS_URL}")
    except Exception as e:
        logger.exception("Failed to connect to Redis")
        # Fail fast so the container restarts rather than running half-broken
        raise


async def cleanup_on_startup():
    """Clean up all collaboration-related data on server startup."""
    try:
        # Get all room code keys
        room_keys = await redis.keys("room:*:code")
        if room_keys:
            await redis.delete(*room_keys)
            logger.info(f"Cleaned up {len(room_keys)} room code entries on startup")

        # Get all room users keys
        user_keys = await redis.keys("collab_room_users:*")
        if user_keys:
            await redis.delete(*user_keys)
            logger.info(f"Cleaned up {len(user_keys)} room user entries on startup")

        # Get all inactive session keys
        inactive_keys = await redis.keys("inactive_collab_session:*")
        if inactive_keys:
            await redis.delete(*inactive_keys)
            logger.info(f"Cleaned up {len(inactive_keys)} inactive session entries on startup")

        logger.info("Startup cleanup completed")
    except Exception as e:
        logger.error(f"Error during startup cleanup: {e}")


async def end_session_after_timeout(session_id: str):
    """End a session after the timeout if no users rejoin."""
    try:
        logger.info(f"Waiting {INACTIVE_SESSION_TIMEOUT}s before ending session {session_id}")
        await asyncio.sleep(INACTIVE_SESSION_TIMEOUT)
        
        # Check if room still has no users
        room_users_key = f"collab_room_users:{session_id}"
        user_count = await redis.scard(room_users_key)
        
        if user_count == 0:
            # First check if session is already ended
            async with aiohttp.ClientSession() as session:
                try:
                    # Check session status first
                    check_url = f"{SESSION_SERVICE_URL}/api/session"
                    async with session.get(check_url, params={"session_id": session_id}) as check_resp:
                        if check_resp.status == 200:
                            session_data = await check_resp.json()
                            
                            # If session already has ended_at, don't try to end it again
                            if session_data.get("ended_at"):
                                logger.info(f"Session {session_id} already ended, skipping")
                                await redis.delete(room_users_key)
                                await redis.delete(f"room:{session_id}:code")
                                await redis.delete(f"inactive_collab_session:{session_id}")
                                return
                        elif check_resp.status == 404:
                            logger.info(f"Session {session_id} not found, skipping")
                            return
                    
                    # Call session service to end the session
                    url = f"{SESSION_SERVICE_URL}/api/session/end"
                    params = {"session_id": session_id}
                    async with session.post(url, params=params) as resp:
                        if resp.status == 200:
                            logger.info(f"Successfully ended inactive session {session_id}")
                            # Clean up Redis data
                            await redis.delete(room_users_key)
                            await redis.delete(f"room:{session_id}:code")
                            await redis.delete(f"inactive_collab_session:{session_id}")
                        elif resp.status == 400:
                            # Session already ended
                            logger.info(f"Session {session_id} already ended")
                            await redis.delete(room_users_key)
                            await redis.delete(f"room:{session_id}:code")
                            await redis.delete(f"inactive_collab_session:{session_id}")
                        else:
                            logger.error(f"Failed to end session {session_id}: {resp.status}")
                except Exception as e:
                    logger.error(f"Error calling session service for {session_id}: {e}")
        else:
            logger.info(f"Session {session_id} has active users, not ending")
            await redis.delete(f"inactive_collab_session:{session_id}")
    except asyncio.CancelledError:
        logger.info(f"Session end task for {session_id} was cancelled")
    finally:
        # Clean up task reference
        if session_id in session_end_tasks:
            del session_end_tasks[session_id]


async def schedule_session_end(room: str):
    """Schedule a session to end after timeout if room becomes empty."""
    # Cancel existing task if any
    if room in session_end_tasks:
        session_end_tasks[room].cancel()
    
    # Check if session is already ended before scheduling
    try:
        async with aiohttp.ClientSession() as session:
            check_url = f"{SESSION_SERVICE_URL}/api/session"
            async with session.get(check_url, params={"session_id": room}) as resp:
                if resp.status == 200:
                    session_data = await resp.json()
                    if session_data.get("ended_at"):
                        logger.info(f"Session {room} already ended, not scheduling timeout")
                        # Clean up Redis immediately
                        await redis.delete(f"collab_room_users:{room}")
                        await redis.delete(f"room:{room}:code")
                        return
                elif resp.status == 404:
                    logger.info(f"Session {room} not found, not scheduling timeout")
                    return
    except Exception as e:
        logger.error(f"Error checking session status for {room}: {e}")
    
    # Mark session as inactive in Redis
    inactive_key = f"inactive_collab_session:{room}"
    await redis.set(inactive_key, "1", ex=INACTIVE_SESSION_TIMEOUT + 60)
    
    # Create new task
    task = asyncio.create_task(end_session_after_timeout(room))
    session_end_tasks[room] = task
    logger.info(f"Scheduled session end for {room} in {INACTIVE_SESSION_TIMEOUT}s")


async def cancel_session_end(room: str):
    """Cancel scheduled session end when users rejoin."""
    if room in session_end_tasks:
        session_end_tasks[room].cancel()
        del session_end_tasks[room]
    
    # Remove inactive marker
    inactive_key = f"inactive_collab_session:{room}"
    await redis.delete(inactive_key)
    logger.info(f"Cancelled session end for {room}")


@sio.event
async def connect(sid, environ):
    """
    Handle a new WebSocket connection.
    """
    logger.info(f"WebSocket: connect called for SID {sid}")
    print(f"WebSocket: connect called for SID {sid}")


@sio.event
async def join(sid, data):
    """
    Handle a user joining a room.
    """
    # Create structured join data
    join_data = RoomJoinData.from_request(data, sid)

    if not join_data.room:
        error = ErrorData("room is required")
        await sio.emit("error", error.to_dict(), to=sid)
        return

    await sio.enter_room(sid, join_data.room)
    
    # Track user in room
    room_users_key = f"collab_room_users:{join_data.room}"
    await redis.sadd(room_users_key, sid)
    await redis.expire(room_users_key, EXPIRY_TIME)
    
    # Cancel any scheduled session end
    await cancel_session_end(join_data.room)
    
    logger.info(f"SID {sid} joined room {join_data.room}")
    print(f"SID {sid} joined room {join_data.room}")

    # Send cached code if it exists
    cache_key = f"room:{join_data.room}:code"
    try:
        cached_code = await redis.get(cache_key)
    except Exception:
        cached_code = None
        logger.exception("Redis GET failed for %s", cache_key)

    if cached_code:
        print(f"Found cached code for room {join_data.room}, sending to SID {sid}")
        code_data = CodeChangeData(code=cached_code)
        await sio.emit("receive", code_data.to_dict(), to=sid)


@sio.event
async def change(sid, data):
    room = data.get("room")
    code = data.get("code")

    print(f"Received change event from SID {sid} for room {room} with code: {code}")

    if not room or code is None:
        error = ErrorData("room and code are required")
        await sio.emit("error", error.to_dict(), to=sid)
        return

    code_change = CodeChangeData(code=code)

    # Cache the new code in Redis for late joiners
    cache_key = f"room:{room}:code"
    try:
        await redis.setex(cache_key, EXPIRY_TIME, code)
    except Exception:
        logger.exception("Redis SETEX failed for %s", cache_key)

    # Broadcast the code change to others in the room, across pods
    await sio.emit("receive", code_change.to_dict(), room=room, skip_sid=sid)
    logger.info(f"Code change broadcasted to room {room} by SID {sid}")


@sio.event
async def leave(sid, data):
    room = data.get("room")
    if not room:
        error = ErrorData("room is required")
        await sio.emit("error", error.to_dict(), to=sid)
        return

    # Remove user from room tracking
    room_users_key = f"collab_room_users:{room}"
    await redis.srem(room_users_key, sid)

    # Notify other users in the room that this user left
    await sio.emit("user_left", {"userId": sid}, room=room, skip_sid=sid)

    await sio.leave_room(sid, room)
    logger.info(f"SID {sid} left room {room}")
    print(f"SID {sid} left room {room}")
    
    # Check if room is now empty
    remaining_users = await redis.scard(room_users_key)
    if remaining_users == 0:
        logger.info(f"Room {room} is now empty, scheduling session end in {INACTIVE_SESSION_TIMEOUT}s")
        await schedule_session_end(room)


@sio.event
async def disconnect(sid):
    """
    Handle WebSocket disconnection.
    """
    # Notify all rooms that this user disconnected
    rooms = sio.manager.get_rooms(sid, namespace='/')
    for room in rooms:
        if room != sid:  # Skip the user's own room
            # Remove from room tracking
            room_users_key = f"collab_room_users:{room}"
            await redis.srem(room_users_key, sid)
            
            # Notify others
            await sio.emit("user_left", {"userId": sid}, room=room, skip_sid=sid)
            
            # Check if room is now empty
            remaining_users = await redis.scard(room_users_key)
            if remaining_users == 0:
                logger.info(f"Room {room} is now empty after disconnect, scheduling session end")
                await schedule_session_end(room)

    logger.info(f"WebSocket: disconnect called for SID {sid}")
    print(f"WebSocket: disconnect called for SID {sid}")


@sio.event
async def cursor(sid, data):
    """Handle cursor position updates with line/character coordinates."""
    room = data.get("room")
    if not room:
        error = ErrorData("room is required")
        await sio.emit("error", error.to_dict(), to=sid)
        return

    cursor_data = CursorData.from_dict(data, sid)

    # Volatile broadcast; no persistence
    await sio.emit("cursor", cursor_data.to_dict(), room=room, skip_sid=sid)
    logger.info(f"Cursor update from {sid} in room {room} at line {cursor_data.line}, ch {cursor_data.ch}")


async def startup_sequence(app):
    """Run startup sequence."""
    await init_redis()
    await cleanup_on_startup()

# Run the server
if __name__ == "__main__":
    app.on_startup.append(startup_sequence)
    port = int(os.environ.get("PORT", 8005))  # Read from env or default to 8005
    web.run_app(app, port=port)

import logging
import os
import socketio
from socketio import AsyncRedisManager  # NEW: cluster manager
from aiohttp import web
import redis.asyncio as aioredis
from schemas import CodeChangeData, CursorData, ErrorData, RoomJoinData

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

logger = logging.getLogger(__name__)

EXPIRY_TIME = 1800  # 30 minutes

SERVICE_PREFIX = os.getenv("SERVICE_PREFIX", "/collaboration-service-api")
if SERVICE_PREFIX and not SERVICE_PREFIX.startswith("/"):
    SERVICE_PREFIX = "/" + SERVICE_PREFIX
SERVICE_PREFIX = SERVICE_PREFIX.rstrip("/")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")  # centralize


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

async def init_redis(app):
    global redis
    try:
        redis = await aioredis.from_url(REDIS_URL, decode_responses=True)
        logger.info(f"Connected to Redis at {REDIS_URL}")
    except Exception as e:
        logger.exception("Failed to connect to Redis")
        # Fail fast so the container restarts rather than running half-broken
        raise


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

    await sio.leave_room(sid, room)
    logger.info(f"SID {sid} left room {room}")
    print(f"SID {sid} left room {room}")


@sio.event
async def disconnect(sid):
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


# Run the server
if __name__ == "__main__":
    # Ensure Redis connection is ready before serving
    app.on_startup.append(init_redis)
    port = int(os.environ.get("PORT", 8005))
    web.run_app(app, port=port)

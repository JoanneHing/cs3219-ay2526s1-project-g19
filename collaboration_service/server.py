import logging
import os
import socketio
from aiohttp import web
import redis.asyncio as aioredis
from schemas import CodeChangeData, CursorData, ErrorData, RoomJoinData

logger = logging.getLogger(__name__)

EXPIRY_TIME = 1800  # 30 minutes

SERVICE_PREFIX = os.getenv("SERVICE_PREFIX", "/collaboration-service-api")
if SERVICE_PREFIX and not SERVICE_PREFIX.startswith("/"):
    SERVICE_PREFIX = "/" + SERVICE_PREFIX
SERVICE_PREFIX = SERVICE_PREFIX.rstrip("/")


@web.middleware
async def fixed_prefix_middleware(request, handler):
    """
    Strip a configured prefix so the service can respond on both the root path
    and the prefixed path (e.g. behind nginx /collaboration-service-api).
    """
    if SERVICE_PREFIX and request.path.startswith(SERVICE_PREFIX):
        stripped_path = request.path[len(SERVICE_PREFIX):] or "/"
        new_request = request.clone(rel_url=request.rel_url.with_path(stripped_path))
        response = await handler(new_request)
        location = response.headers.get("Location")
        if location and location.startswith("/") and not location.startswith(SERVICE_PREFIX):
            response.headers["Location"] = f"{SERVICE_PREFIX}{location}"
        return response
    return await handler(request)


async def health_check(request):
    """Health check endpoint for ALB"""
    return web.json_response({"status": "healthy"})


sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application(middlewares=[fixed_prefix_middleware])
sio.attach(app)

app.router.add_get("/health", health_check)
app.router.add_get("/health/", health_check)

logger.info("Application configured to run at '/' and '%s/'", SERVICE_PREFIX or "/")


# # Sub-app with prefix
# api_app = web.Application()
# sio.attach(api_app)
# api_app.router.add_get('/health', health_check)

# # Mount under prefix
# app.add_subapp('/collaboration-service-api', api_app)

# # Also mount same app at root
# root_app = web.Application()
# sio.attach(root_app)
# root_app.router.add_get('/health', health_check)
# app.add_subapp('/', root_app)

# Add health check route directly to main app


# Initialize Redis connection
redis = None


async def init_redis():
    global redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis = await aioredis.from_url(redis_url, decode_responses=True)
    logger.info(f"Connected to Redis at {redis_url}")

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
    cached_code = await redis.get(cache_key)
    if cached_code:
        print(f"Found cached code for room {join_data.room}, sending to SID {sid}")
        code_data = CodeChangeData(code=cached_code)
        await sio.emit("receive", code_data.to_dict(), to=sid)

@sio.event
async def change(sid, data):
    """
    Handle code changes and broadcast them to the room.
    """
    room = data.get("room")
    code = data.get("code")

    print(f"Received change event from SID {sid} for room {room} with code: {code}")

    if not room or code is None:
        error = ErrorData("room and code are required")
        await sio.emit("error", error.to_dict(), to=sid)
        return

    # Create structured code change data
    code_change = CodeChangeData(code=code)

    # Cache the new code in Redis
    cache_key = f"room:{room}:code"
    await redis.setex(cache_key, EXPIRY_TIME, code)

    # Broadcast the code change to others in the room, except the sender
    await sio.emit("receive", code_change.to_dict(), room=room, skip_sid=sid)
    logger.info(f"Code change broadcasted to room {room} by SID {sid}")

@sio.event
async def leave(sid, data):
    """
    Handle a user leaving a room.
    """
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
    """
    Handle WebSocket disconnection.
    """
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

    # Create structured cursor data
    cursor_data = CursorData.from_dict(data, sid)

    # Broadcast cursor position to all other users in the room
    await sio.emit("cursor", cursor_data.to_dict(), room=room, skip_sid=sid)

    logger.info(f"Cursor update from {sid} in room {room} at line {cursor_data.line}, ch {cursor_data.ch}")


# Run the server
if __name__ == "__main__":
    app.on_startup.append(lambda app: init_redis())  # Initialize Redis on startup
    port = int(os.environ.get("PORT", 8005))  # Read from env or default to 8005
    web.run_app(app, port=port)

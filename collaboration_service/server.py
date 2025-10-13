import os
import socketio
from aiohttp import web
import logging
import redis.asyncio as aioredis
from schemas import CodeChangeData, CursorData, ErrorData, RoomJoinData

logger = logging.getLogger(__name__)

EXPIRY_TIME = 1800  # 30 minutes

# Create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Initialize Redis connection
redis = None

async def init_redis():
    """Initialize Redis connection."""
    global redis
    redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
    redis = await aioredis.from_url(redis_url, decode_responses=True)
    logger.info(f"Connected to Redis at {redis_url}")

async def cleanup_on_startup():
    """Clean up all collaboration-related data on server startup."""
    try:
        # Get all room code keys
        room_keys = await redis.keys("room:*:code")
        if room_keys:
            await redis.delete(*room_keys)
            logger.info(f"Cleaned up {len(room_keys)} room code entries on startup")

        # Get all other room-related keys (if any)
        other_room_keys = await redis.keys("room:*")
        if other_room_keys:
            # Filter out already deleted keys
            remaining_keys = [key for key in other_room_keys if key not in room_keys]
            if remaining_keys:
                await redis.delete(*remaining_keys)
                logger.info(f"Cleaned up {len(remaining_keys)} other room entries on startup")

        logger.info("Startup cleanup completed")
    except Exception as e:
        logger.error(f"Error during startup cleanup: {e}")

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

    # Notify other users in the room that this user left
    await sio.emit("user_left", {"userId": sid}, room=room, skip_sid=sid)

    await sio.leave_room(sid, room)
    logger.info(f"SID {sid} left room {room}")
    print(f"SID {sid} left room {room}")

@sio.event
async def disconnect(sid):
    """
    Handle WebSocket disconnection.
    """
    # Notify all rooms that this user disconnected
    rooms = sio.manager.get_rooms(sid, namespace='/')
    for room in rooms:
        if room != sid:  # Skip the user's own room
            await sio.emit("user_left", {"userId": sid}, room=room, skip_sid=sid)

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

async def startup_sequence(app):
    """Run startup sequence."""
    await init_redis()
    await cleanup_on_startup()

# Run the server
if __name__ == "__main__":
    app.on_startup.append(startup_sequence)
    port = int(os.environ.get("PORT", 8005))  # Read from env or default to 8005
    web.run_app(app, port=port)

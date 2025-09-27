import os
import time
import socketio
import logging
import json
from aiohttp import web
import redis.asyncio as redis

logger = logging.getLogger(__name__)

# Constants
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
EXPIRY_TIME = 1800  # 30 minutes - matching collaboration service

# Create a Socket.IO server
sio = socketio.AsyncServer(cors_allowed_origins="*")
app = web.Application()
sio.attach(app)

# Initialize Redis connection
redis_client = None

async def init_redis():
    """Initialize Redis connection."""
    global redis_client
    redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
    logger.info(f"Connected to Redis at {REDIS_URL}")

async def cleanup_on_startup():
    """Clean up all chat-related data on server startup."""
    try:
        # Get all chat history keys
        chat_keys = await redis_client.keys("chat_history_*")
        if chat_keys:
            await redis_client.delete(*chat_keys)
            logger.info(f"Cleaned up {len(chat_keys)} chat history entries on startup")
        
        # Get all room users keys
        user_keys = await redis_client.keys("room_users_*")
        if user_keys:
            await redis_client.delete(*user_keys)
            logger.info(f"Cleaned up {len(user_keys)} room user entries on startup")
            
        logger.info("Startup cleanup completed")
    except Exception as e:
        logger.error(f"Error during startup cleanup: {e}")

@sio.event
async def connect(sid, environ):
    """Handle new WebSocket connection."""
    logger.info(f"User connected to socket {sid}")
    print(f"User connected to socket {sid}")

@sio.event
async def join(sid, data):
    """Handle a user joining a chat room."""
    username = data.get("username")
    room = data.get("room")

    if not room or not username:
        await sio.emit("error", {"message": "username and room are required"}, to=sid)
        return

    await sio.enter_room(sid, room)
    logger.info(f"User {username} joined room: {room}")

    # Send chat history to the joining user
    cache_key = f"chat_history_{room}"
    history = await redis_client.lrange(cache_key, 0, -1)
    if history:
        for msg_str in history:
            msg_data = json.loads(msg_str)
            await sio.emit("receive", msg_data, to=sid)
    
    # Send notification of new user joining
    created_time = int(time.time() * 1000)
    await sio.emit("receive", {
        "message": f"{username} has joined the interview",
        "username": "ChatBot",
        "__createdtime__": created_time
    }, room=room)

@sio.event
async def send(sid, data):
    """Handle sending messages."""
    room = data.get("room")
    username = data.get("username")
    message = data.get("message")
    
    if not all([room, username, message]):
        await sio.emit("error", {"message": "room, username and message are required"}, to=sid)
        return

    # Store message in Redis as JSON string
    message_data = {
        "message": message,
        "username": username,
        "__createdtime__": int(time.time() * 1000)
    }
    cache_key = f"chat_history_{room}"
    await redis_client.rpush(cache_key, json.dumps(message_data))
    # Keep only last 100 messages
    await redis_client.ltrim(cache_key, -100, -1)

    # Broadcast message to room - fix: use message_data instead of data
    await sio.emit("receive", message_data, room=room)
    logger.info(f"Message from {username} in room {room}: {message}")

@sio.event
async def leave(sid, data):
    """Handle a user leaving a chat room."""
    username = data.get("username")
    room = data.get("room")

    if not room or not username:
        await sio.emit("error", {"message": "username and room are required"}, to=sid)
        return

    await sio.leave_room(sid, room)
    created_time = int(time.time() * 1000)

    # Notify others in the room
    await sio.emit("receive", {
        "message": f"{username} has left the interview",
        "username": "ChatBot",
        "__createdtime__": created_time
    }, room=room)

    logger.info(f"User {username} left room: {room}")

@sio.event
async def disconnect(sid):
    """Handle client disconnection."""
    logger.info(f"User disconnected: {sid}")
    print(f"User disconnected: {sid}")

async def startup_sequence(app):
    """Run startup sequence."""
    await init_redis()
    await cleanup_on_startup()

# Run the server
if __name__ == "__main__":
    app.on_startup.append(startup_sequence)
    web.run_app(app, port=8006)
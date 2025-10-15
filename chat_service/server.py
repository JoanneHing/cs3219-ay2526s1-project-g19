import os
import time
import socketio
import logging
import json
from aiohttp import web
import redis.asyncio as redis
from schemas import MessageData

logger = logging.getLogger(__name__)

# Constants
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
EXPIRY_TIME = 1800  # 30 minutes - matching collaboration service

# Initialize Redis connection
redis_client = None

async def health_check(request):
    """Health check endpoint for ALB"""
    return web.json_response({"status": "healthy"})


# 1. Create the CORE application that contains all routes and logic.
core_app = web.Application()
sio = socketio.AsyncServer(cors_allowed_origins="*")

# 2. Add HTTP routes AND attach Socket.IO to the CORE app.
#    This defines /health and /socket.io/ within the CORE app's routing table (implicitly includes HEAD).
core_app.router.add_get('/health', health_check)
sio.attach(core_app)

# 3. Create the MAIN application that will be run.
app = web.Application()

# 4. Mount the fully configured core_app under the desired prefix.
#    This handles requests to /collaboration-service-api/health and /collaboration-service-api/socket.io/
app.add_subapp('/chat-service-api', core_app) # Removed trailing '/' for cleaner routing

# 5. Handle Root Paths (The Fix for the /health 404 and the HEAD conflict):
# A. Explicitly add the /health endpoint to the ROOT router using only the GET method.
#    This fixes the root 404 issue and prevents the automatic duplicate registration of HEAD.
app.router.add_route('GET', '/health', health_check)

# B. Add the core app's routes (crucially, the /socket.io/ routes and the remaining HEAD route) to the root router.
#    This ensures WebSocket connections work at the root path (ws://host:port/) without conflict.
app.router.add_routes(core_app.router)  

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
            msg_dict = json.loads(msg_str)
            msg_data = MessageData.from_dict(msg_dict)
            await sio.emit("receive", msg_data.to_dict(), to=sid)

    # Send notification of new user joining using MessageData
    join_notification = MessageData(
        message=f"{username} has joined the interview",
        username="ChatBot"
    )
    await sio.emit("receive", join_notification.to_dict(), room=room)

@sio.event
async def send(sid, data):
    """Handle sending messages."""
    room = data.get("room")
    username = data.get("username")
    message = data.get("message")

    if not all([room, username, message]):
        await sio.emit("error", {"message": "room, username and message are required"}, to=sid)
        return

    # Create MessageData instance
    message_data = MessageData(
        message=message,
        username=username
    )

    # Store message in Redis as JSON string
    cache_key = f"chat_history_{room}"
    await redis_client.rpush(cache_key, json.dumps(message_data.to_dict()))
    # Keep only last 100 messages
    await redis_client.ltrim(cache_key, -100, -1)

    # Broadcast message to room using MessageData
    await sio.emit("receive", message_data.to_dict(), room=room)
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

    # Send leave notification using MessageData
    leave_notification = MessageData(
        message=f"{username} has left the interview",
        username="ChatBot"
    )
    await sio.emit("receive", leave_notification.to_dict(), room=room)

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
    port = int(os.environ.get("PORT", 8006))  # Read from env or default to 8006
    web.run_app(app, port=port)
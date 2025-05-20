import os
import logging # Import the logging module
from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
import sqlite3
import aiosqlite # For async database operations
from fastapi.responses import JSONResponse
from pyrogram import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid, UserNotParticipant, PeerIdInvalid, AuthKeyUnregistered # Import additional Pyrogram errors
from pyrogram.enums import ChatType
from pyrogram.types import Message as PyrogramMessage # To avoid name clash
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional, Any
from pydantic import BaseModel, Field # For request/response models

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Get a logger for this module

# Load environment variables from .env file
load_dotenv()

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
# PHONE_NUMBER = os.getenv("PHONE_NUMBER") # Optional, for development convenience

# Basic validation for API credentials
if not API_ID or not API_HASH:
    logger.error("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file") # Log error
    raise RuntimeError("TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")

# Database setup
DATABASE_URL = "./telegram_sessions.db"

async def get_db():
    db = await aiosqlite.connect(DATABASE_URL)
    db.row_factory = aiosqlite.Row
    return db

async def init_db():
    async with await aiosqlite.connect(DATABASE_URL) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            phone_number TEXT PRIMARY KEY,
            phone_code_hash TEXT NOT NULL,
            session_name TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """)
        await db.commit()
        logger.info("Database initialized.")

# temp_storage = {} # Replaced by SQLite

app = FastAPI(title="Telegram Channel Viewer API")

@app.on_event("startup")
async def startup_event():
    await init_db()

# --- Pydantic Models for API Data Structures ---
class RequestCodeBody(BaseModel):
    phone_number: str = Field(..., example="+12345678900")

class SubmitCodeBody(BaseModel):
    phone_number: str = Field(..., example="+12345678900")
    code: str = Field(..., example="12345")
    password: Optional[str] = Field(None, example="your2FApassword")

class DialogItem(BaseModel):
    id: int
    title: str
    type: str # e.g., "channel", "group", "private"

class MessageItem(BaseModel):
    id: int
    text: Optional[str] = None
    sender: Optional[str] = None # Or a more complex sender object
    date: int # Unix timestamp
    media_type: Optional[str] = None
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    # Add more fields here as needed: photo, video, poll, etc.

class SendMessageBody(BaseModel):
    phone_number: str = Field(..., example="+12345678900")
    chat_id: int = Field(..., description="ID of the chat (channel, group, or user) to send the message to")
    text: str = Field(..., description="The message text to send")

# --- Helper function to get an authenticated client ---
async def get_authenticated_client(phone_number: str) -> Client:
    logger.info(f"Attempting to get authenticated client for {phone_number}") # Log attempt
    session_name = f"user_session_{phone_number.replace('+', '')}"
    # Construct path relative to this file's directory
    script_dir = Path(__file__).parent
    session_file = script_dir / f"{session_name}.session" # Path object for session file

    if not session_file.exists(): # Check existence using the full path
        logger.warning(f"Session file not found for {phone_number}: {session_file}") # Log warning
        raise HTTPException(status_code=401, detail="User not authenticated or session expired. Please login first.")

    # Pyrogram's `name` is the session file name (without .session)
    # `workdir` is the directory where session files are stored.
    client = Client(name=session_name, api_id=int(API_ID), api_hash=API_HASH, workdir=str(script_dir))
    logger.info(f"Authenticated client created for {phone_number}") # Log success
    return client

# --- Authentication Endpoints ---
@app.get("/")
async def root():
    logger.info("Root endpoint accessed") # Log access
    return {"message": "Welcome to the Telegram Channel Viewer API"}

# Import necessary slowapi components
from slowapi import Limiter, _rate_limit_exts
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

@app.post("/api/auth/request_code")
@limiter.limit("5/minute") # Apply rate limit
async def request_code(request: Request, auth_request: AuthRequest):
    """
    Initiates the Telegram login process by sending a code to the user's phone.
    """
    phone_number = body.phone_number # Assign phone_number from the request body
    logger.info(f"Received request_code for {phone_number}") # Log request

    # Using a unique session name for each phone number to allow multiple users
    # or to easily clear sessions. For this app, we'll use the phone number
    # itself, but sanitized to be a valid file name.
    session_name = f"user_session_{phone_number.replace('+', '')}"
    
    # Create a new Pyrogram client instance for each login attempt or use an existing one
    # For this initial step, we create it on demand.
    # The `workdir` parameter tells Pyrogram where to store session files.
    script_dir = Path(__file__).parent
    client = Client(name=session_name, api_id=int(API_ID), api_hash=API_HASH, workdir=str(script_dir))

    try:
        await client.connect()
        sent_code_info = await client.send_code(phone_number)
        async with await get_db() as db:
            await db.execute(
                "INSERT OR REPLACE INTO sessions (phone_number, phone_code_hash, session_name) VALUES (?, ?, ?)",
                (phone_number, sent_code_info.phone_code_hash, session_name)
            )
            await db.commit()
        await client.disconnect()
        logger.info(f"Code sent to {phone_number}, session data stored in DB.")
        return JSONResponse(content={"message": "Verification code sent successfully.", "phone_code_hash_debug": sent_code_info.phone_code_hash})
    except PhoneNumberInvalid:
        if client.is_connected: # Ensure client is connected before trying to disconnect
            await client.disconnect()
        logger.warning(f"PhoneNumberInvalid for {phone_number}") # Log specific error
        raise HTTPException(status_code=400, detail="Invalid phone number format.")
    except Exception as e:
        if client.is_connected: # Ensure client is connected before trying to disconnect
            await client.disconnect()
        logger.error(f"An error occurred in request_code for {phone_number}: {e}", exc_info=True) # Log unexpected error with traceback
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")

@app.post("/api/auth/submit_code")
async def submit_telegram_code(body: SubmitCodeBody):
    """
    Submits the verification code (and password if 2FA is enabled) to complete login.
    """
    phone_number = body.phone_number
    code = body.code
    password_from_request = body.password # Renamed for clarity
    logger.info(f"Received submit_code for {phone_number}") # Log request

    async with await get_db() as db:
        cursor = await db.execute("SELECT phone_code_hash, session_name FROM sessions WHERE phone_number = ?", (phone_number,))
        session_data = await cursor.fetchone()
        await cursor.close()

    if not session_data:
        logger.warning(f"submit_code called without request_code for {phone_number} or session not found in DB")
        raise HTTPException(status_code=400, detail="Please request a code first or session expired/not found.")

    phone_code_hash = session_data["phone_code_hash"]
    session_name = session_data["session_name"]

    # Use the BASE_DIR for workdir
    # NOTE: BASE_DIR is not defined in this file. It should be script_dir.
    # Correcting this to use script_dir as defined earlier.
    script_dir = Path(__file__).parent
    client = Client(name=session_name, api_id=int(API_ID), api_hash=API_HASH, workdir=str(script_dir))
    
    try:
        await client.connect()
        logger.info(f"Attempting sign_in for {phone_number}") # Log attempt
        # Always attempt sign_in without password first
        await client.sign_in(
            phone_number=phone_number,
            phone_code_hash=phone_code_hash,
            phone_code=code
        )
        
        # If sign_in succeeds without SessionPasswordNeeded, 2FA was not required or already handled
        async with await get_db() as db:
            await db.execute("DELETE FROM sessions WHERE phone_number = ?", (phone_number,))
            await db.commit()
        me = await client.get_me()
        await client.disconnect()
        logger.info(f"Successfully signed in for {phone_number}, User ID: {me.id}. Session deleted from DB.")
        return {"message": "Successfully signed in!", "user_id": me.id, "username": me.username}

    except SessionPasswordNeeded:
        logger.warning(f"SessionPasswordNeeded for {phone_number}") # Log 2FA requirement
        if not password_from_request:
            # Password was needed, but not provided in this API call
            # No need to update DB here as the session is still pending password
            await client.disconnect()
            raise HTTPException(status_code=401, detail="Two-Factor Authentication password is required. Please provide your password.")
        else:
            # Password was provided in this API call, now try to check it
            logger.info(f"Attempting check_password for {phone_number}") # Log attempt
            try:
                await client.check_password(password_from_request)
                # If check_password succeeds
                async with await get_db() as db:
                    await db.execute("DELETE FROM sessions WHERE phone_number = ?", (phone_number,))
                    await db.commit()
                me = await client.get_me()
                await client.disconnect()
                logger.info(f"Successfully signed in with 2FA for {phone_number}, User ID: {me.id}. Session deleted from DB.")
                return {"message": "Successfully signed in with 2FA!", "user_id": me.id, "username": me.username}
            except Exception as e_pwd: # Catch errors from check_password (e.g., bad password)
                await client.disconnect()
                logger.error(f"Error during check_password for {phone_number}: {e_pwd}", exc_info=True) # Log 2FA error
                raise HTTPException(status_code=401, detail=f"Incorrect 2FA password or other 2FA error.")

    except PhoneCodeInvalid:
        logger.error(f"Invalid phone code for {phone_number}")
        async with await get_db() as db: # Clean up session if code is invalid
            await db.execute("DELETE FROM sessions WHERE phone_number = ?", (phone_number,))
            await db.commit()
        await client.disconnect()
        raise HTTPException(status_code=400, detail="Invalid phone code.")
    except PhoneNumberInvalid: # Should ideally be caught by request_code, but good to have
        await client.disconnect()
        logger.warning(f"PhoneNumberInvalid during submit_code for {phone_number}") # Log specific error
        raise HTTPException(status_code=400, detail="Invalid phone number format.")
    except Exception as e:
        logger.error(f"An unexpected error occurred during submit_code for {phone_number}: {e}")
        # Attempt to clean up session on unexpected error, but don't fail if DB operation itself errors
        try:
            async with await get_db() as db:
                await db.execute("DELETE FROM sessions WHERE phone_number = ?", (phone_number,))
                await db.commit()
        except Exception as db_err:
            logger.error(f"Failed to clean up session from DB for {phone_number} after error: {db_err}")
        if client.is_connected:
            await client.disconnect()
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")

# --- Data Fetching Endpoints ---
@app.get("/api/dialogs", response_model=List[DialogItem])
async def list_dialogs(phone_number: str = Query(..., description="Phone number of the authenticated user")):
    """
    Lists all dialogs (chats, channels, groups) for the authenticated user.
    Requires a valid session file for the given phone number.
    """
    logger.info(f"Received request for dialogs for {phone_number}") # Log request
    try:
        client = await get_authenticated_client(phone_number)
        dialog_items: List[DialogItem] = []
        async with client: # Handles connect and disconnect
            logger.info(f"Fetching dialogs for {phone_number}") # Log action
            async for dialog in client.get_dialogs():
                dialog_items.append(DialogItem(
                    id=dialog.chat.id,
                    title=dialog.chat.title if dialog.chat.title else (dialog.chat.first_name + (" " + dialog.chat.last_name if dialog.chat.last_name else "")),
                    type=dialog.chat.type.name.lower() # e.g., "channel", "private", "group"
                ))
        logger.info(f"Successfully fetched {len(dialog_items)} dialogs for {phone_number}") # Log success
        return dialog_items
    except HTTPException: # Re-raise HTTPExceptions from get_authenticated_client
        raise # HTTPException is already logged or handled by FastAPI
    except AuthKeyUnregistered:
        logger.warning(f"AuthKeyUnregistered for {phone_number} during dialog fetch.")
        raise HTTPException(status_code=401, detail="Authentication expired. Please login again.")
    except Exception as e:
        logger.error(f"Failed to list dialogs for {phone_number}: {e}", exc_info=True) # Log error
        # Provide a generic 500 error to the client for unexpected issues
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching dialogs.")

def format_message(msg: PyrogramMessage) -> MessageItem:
    """Helper to convert Pyrogram Message to our MessageItem model."""
    sender_name = None
    if msg.from_user:
        sender_name = msg.from_user.first_name
        if msg.from_user.last_name:
            sender_name += f" {msg.from_user.last_name}"
        if msg.from_user.username:
            sender_name += f" (@{msg.from_user.username})"
    elif msg.sender_chat: # For messages sent by channels
        sender_name = msg.sender_chat.title
    
    media_type_str = None
    file_id_str = None
    file_name_str = None
    mime_type_str = None

    if msg.media:
        media_type_str = msg.media.value # e.g., "photo", "video", "document"
        if msg.photo:
            file_id_str = msg.photo.file_id
        elif msg.video:
            file_id_str = msg.video.file_id
            file_name_str = msg.video.file_name
            mime_type_str = msg.video.mime_type
        elif msg.audio:
            file_id_str = msg.audio.file_id
            file_name_str = msg.audio.file_name
            mime_type_str = msg.audio.mime_type
        elif msg.voice:
            file_id_str = msg.voice.file_id
            mime_type_str = msg.voice.mime_type
        elif msg.sticker:
            file_id_str = msg.sticker.file_id
            file_name_str = msg.sticker.file_name # Stickers can have emoji as name
            mime_type_str = msg.sticker.mime_type
        elif msg.document:
            file_id_str = msg.document.file_id
            file_name_str = msg.document.file_name
            mime_type_str = msg.document.mime_type
        elif msg.poll:
            # For polls, we might want to include poll details in the text or a separate field
            # For now, let's just indicate it's a poll and potentially include the question
            media_type_str = "poll"
            # The poll object itself contains question, options, etc.
            # We could serialize the poll object or extract specific fields
            # For simplicity, let's add the question to the text if text is empty
            if not msg.text and msg.poll.question:
                 text = f"Poll: {msg.poll.question}"
            # We might need to add a dedicated 'poll' field to the MessageItem model
            # For now, we'll just rely on media_type and potentially updated text

    return MessageItem(
        id=msg.id,
        text=msg.text or (msg.caption if msg.caption else None),
        sender=sender_name,
        date=int(msg.date.timestamp()) if msg.date else 0,
        media_type=media_type_str,
        file_id=file_id_str,
        file_name=file_name_str,
        mime_type=mime_type_str
        # Add more fields here as needed

@app.post("/api/send_message")
async def send_message(body: SendMessageBody):
    """
    Sends a message to a specified chat (channel, group, or user).
    Requires a valid session file for the given phone number.
    """
    phone_number = body.phone_number
    chat_id = body.chat_id
    text = body.text
    logger.info(f"Received request to send message to chat {chat_id} for {phone_number}")

    try:
        client = await get_authenticated_client(phone_number)
        async with client:
            logger.info(f"Sending message to chat_id {chat_id} for {phone_number}")
            await client.send_message(chat_id=chat_id, text=text)
        logger.info(f"Successfully sent message to chat {chat_id} for {phone_number}")
        return {"message": "Message sent successfully!"}
    except HTTPException:
        raise
    except AuthKeyUnregistered:
        logger.warning(f"AuthKeyUnregistered for {phone_number} during send message.")
        raise HTTPException(status_code=401, detail="Authentication expired. Please login again.")
    except PeerIdInvalid:
         logger.warning(f"PeerIdInvalid for chat {chat_id} for user {phone_number}. Chat ID might be incorrect.")
         raise HTTPException(status_code=400, detail="Invalid chat ID provided.")
    except Exception as e:
        logger.error(f"Failed to send message to chat {chat_id} for {phone_number}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while sending the message.")

class ChannelInfoItem(BaseModel):
    id: int
    title: str
    type: str
    username: Optional[str] = None
    description: Optional[str] = None
    members_count: Optional[int] = None
    # Add more fields as needed

@app.get("/api/channels/{channel_id}/info", response_model=ChannelInfoItem)
async def get_channel_info(
    channel_id: int,
    phone_number: str = Query(..., description="Phone number of the authenticated user")
):
    """
    Fetches information about a specific channel.
    Requires a valid session file for the given phone number.
    """
    logger.info(f"Received request for channel info for channel {channel_id} for {phone_number}")

    try:
        client = await get_authenticated_client(phone_number)
        async with client:
            logger.info(f"Fetching chat info for chat_id {channel_id} for {phone_number}")
            chat = await client.get_chat(chat_id=channel_id)
            channel_info = ChannelInfoItem(
                id=chat.id,
                title=chat.title,
                type=chat.type.name.lower(),
                username=chat.username,
                description=chat.description,
                members_count=chat.members_count
            )
        logger.info(f"Successfully fetched info for channel {channel_id} for {phone_number}")
        return channel_info
    except HTTPException:
        raise
    except UserNotParticipant:
        logger.warning(f"User {phone_number} is not a participant of channel {channel_id} or channel not found.")
        raise HTTPException(status_code=403, detail="User is not a participant of this channel or channel does not exist.")
    except PeerIdInvalid:
         logger.warning(f"PeerIdInvalid for channel {channel_id} for user {phone_number}. Channel ID might be incorrect.")
         raise HTTPException(status_code=400, detail="Invalid channel ID provided.")
    except AuthKeyUnregistered:
        logger.warning(f"AuthKeyUnregistered for {phone_number} during channel info fetch.")
        raise HTTPException(status_code=401, detail="Authentication expired. Please login again.")
    except Exception as e:
        logger.error(f"Failed to get channel info for {channel_id} for {phone_number}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while fetching channel information.")

class JoinChannelBody(BaseModel):
    phone_number: str = Field(..., example="+12345678900")
    channel_id: int = Field(..., description="ID of the channel to join")

@app.post("/api/channels/join")
async def join_channel(body: JoinChannelBody):
    """
    Joins a specific channel.
    Requires a valid session file for the given phone number.
    """
    phone_number = body.phone_number
    channel_id = body.channel_id
    logger.info(f"Received request to join channel {channel_id} for {phone_number}")

    try:
        client = await get_authenticated_client(phone_number)
        async with client:
            logger.info(f"Joining channel {channel_id} for {phone_number}")
            await client.join_chat(chat_id=channel_id)
        logger.info(f"Successfully joined channel {channel_id} for {phone_number}")
        return {"message": "Successfully joined channel!"}
    except HTTPException:
        raise
    except AuthKeyUnregistered:
        logger.warning(f"AuthKeyUnregistered for {phone_number} during join channel.")
        raise HTTPException(status_code=401, detail="Authentication expired. Please login again.")
    except PeerIdInvalid:
         logger.warning(f"PeerIdInvalid for channel {channel_id} for user {phone_number}. Channel ID might be incorrect.")
         raise HTTPException(status_code=400, detail="Invalid channel ID provided.")
    except Exception as e:
        logger.error(f"Failed to join channel {channel_id} for {phone_number}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An unexpected error occurred while joining the channel.")

@app.get("/api/channels/{channel_id}/messages", response_model=List[MessageItem])
async def get_channel_messages(
    channel_id: int,
    phone_number: str = Query(..., description="Phone number of the authenticated user"),
    limit: int = Query(100, ge=1, le=1000, description="Number of messages to fetch (min 1, max 1000)"), # Adjusted max limit and default
    offset: int = Query(0, ge=0, description="Number of messages to skip (for pagination, must be non-negative)")
    # offset_id: Optional[int] = Query(None, description="Pass the message ID to start fetching from (older messages)"),
    # offset_date: Optional[int] = Query(None, description="Pass the message date (Unix timestamp) to start fetching from (older messages)")
):
    """
    Fetches messages from a specific channel.
    Requires a valid session file for the given phone number.
    """
    logger.info(f"Received request for messages from channel {channel_id} for {phone_number} with limit {limit} and offset {offset}") # Log request
    try:
        client = await get_authenticated_client(phone_number)
        messages_items: List[MessageItem] = []
        async with client: # Handles connect and disconnect
            logger.info(f"Fetching messages from chat_id {channel_id} for {phone_number}") # Log action
            async for message in client.get_chat_history(chat_id=channel_id, limit=limit, offset=offset):
                if isinstance(message, PyrogramMessage): # Ensure it's a message object
                    messages_items.append(format_message(message))
        logger.info(f"Successfully fetched {len(messages_items)} messages from channel {channel_id} for {phone_number}") # Log success
        return messages_items
    except HTTPException: # Re-raise HTTPExceptions from get_authenticated_client or previous specific handlers
        raise
    except UserNotParticipant:
        logger.warning(f"User {phone_number} is not a participant in channel {channel_id}.")
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a participant in this channel or the channel is private and you are not a member.")
    except PeerIdInvalid:
        logger.warning(f"Invalid channel_id (PeerIdInvalid): {channel_id} provided by user {phone_number}.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found. The provided ID is invalid or the chat does not exist.")
    except AuthKeyUnregistered:
        logger.warning(f"AuthKeyUnregistered for {phone_number} during message fetch from channel {channel_id}.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication key is unregistered. Session is invalid. Please login again.")
    except Exception as e:
        error_type = type(e).__name__
        logger.error(f"Failed to fetch messages for channel {channel_id} for user {phone_number}. Error type: {error_type}, Details: {e}", exc_info=True)
        # Example of checking specific error strings if Pyrogram lacks distinct exceptions:
        # if "CHANNEL_PRIVATE" in str(e) or "CHAT_ADMIN_REQUIRED" in str(e):
        #     raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Cannot access this channel. It might be private or require admin rights.")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An unexpected error occurred while fetching messages: {error_type}")

# To run this: uvicorn main:app --reload (from the backend directory with venv active)
import os
import io
import logging
from fastapi import FastAPI, HTTPException, Depends, status, Request, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pyrogram.client import Client
import pyrogram.enums # pyrogram.enums.MessageMediaType, pyrogram.enums.PollType
from pyrogram.errors import (
    UserNotParticipant, PeerIdInvalid, AuthKeyUnregistered, ChannelPrivate, ChannelInvalid,
    InviteHashExpired, InviteHashInvalid, FloodWait
)
from pyrogram.types import Message as PyrogramMessage, ChatPrivileges, Chat, ChatPreview, Poll
from dotenv import load_dotenv
from pathlib import Path
from typing import List, Optional, Any, AsyncGenerator, Union
from pydantic import BaseModel, Field
import datetime # For message date conversion

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables from .env file
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

API_ID_STR = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")

if not API_ID_STR or not API_HASH or not PHONE_NUMBER:
    error_msg = "TELEGRAM_API_ID, TELEGRAM_API_HASH, and PHONE_NUMBER must be set in .env file"
    logger.error(error_msg)
    raise RuntimeError(error_msg)

try:
    API_ID = int(API_ID_STR)
except ValueError:
    error_msg = "TELEGRAM_API_ID must be an integer."
    logger.error(error_msg)
    raise RuntimeError(error_msg)

app = FastAPI(title="Telegram Channel Viewer API")

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info(f"Application startup: Initializing Pyrogram client for {PHONE_NUMBER}")
    try:
        client = await get_authenticated_client()
        await client.connect()
        app.state.pyrogram_client = client
        logger.info(f"Pyrogram client connected and stored in app.state for {PHONE_NUMBER}")
    except AuthKeyUnregistered:
        logger.critical(f"CRITICAL: Authentication key unregistered for session {PHONE_NUMBER} during startup. The session might be revoked or expired.")
        session_file_path = Path(__file__).parent / f"user_session_{PHONE_NUMBER.replace('+', '')}.session"
        if session_file_path.exists():
            try:
                session_file_path.unlink()
                logger.info(f"Deleted potentially corrupt session file during startup: {session_file_path}")
            except OSError as e:
                logger.error(f"Error deleting session file {session_file_path} during startup: {e}")
        raise RuntimeError(f"Pyrogram client authentication failed for {PHONE_NUMBER} at startup: AuthKeyUnregistered. Please re-run create_session.py.")
    except FloodWait as e:
        logger.critical(f"CRITICAL: FloodWait encountered for {PHONE_NUMBER} during startup: {e.value} seconds. Application may not function correctly.")
        raise RuntimeError(f"Pyrogram client connection failed for {PHONE_NUMBER} at startup due to FloodWait: {e.value} seconds. Try again later.")
    except Exception as e:
        logger.critical(f"CRITICAL: Failed to initialize Pyrogram client for {PHONE_NUMBER} during startup: {e}", exc_info=True)
        raise RuntimeError(f"Pyrogram client initialization failed for {PHONE_NUMBER} at startup: {str(e)}")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info(f"Application shutdown: Disconnecting Pyrogram client for {PHONE_NUMBER}")
    client: Optional[Client] = getattr(app.state, "pyrogram_client", None)
    if client and client.is_connected:
        await client.disconnect()
        logger.info(f"Pyrogram client disconnected for {PHONE_NUMBER}")
    else:
        logger.info(f"Pyrogram client for {PHONE_NUMBER} was not found or not connected at shutdown.")

# --- Pydantic Models ---
class DialogItem(BaseModel):
    id: int
    title: str
    type: str

class PollOptionItem(BaseModel): # Renamed from PollOption to avoid clash if any
    text: str
    data: bytes # Raw data, pydantic will handle base64 if needed for json

class PollDetails(BaseModel):
    question: str
    options: List[PollOptionItem]
    total_voters: Optional[int] = None
    is_closed: bool
    is_anonymous: bool
    type: str # "regular", "quiz"
    allows_multiple_answers: bool
    quiz_correct_option_id: Optional[int] = None

class MessageItem(BaseModel):
    id: int
    text: Optional[str] = None
    sender: Optional[str] = None
    date: int # Unix timestamp
    media_type: Optional[str] = None # "photo", "video", "document", "poll", etc.
    file_id: Optional[str] = None
    file_name: Optional[str] = None
    mime_type: Optional[str] = None
    poll_data: Optional[PollDetails] = None
    is_outgoing: Optional[bool] = None # Added to indicate if the message is from the authenticated user

class SendMessageBody(BaseModel):
    chat_id: Union[int, str] = Field(..., description="ID or username of the chat to send the message to")
    text: str = Field(..., description="The message text to send")

class JoinChannelBody(BaseModel):
    invite_link: str = Field(..., description="The invite link or username (e.g., https://t.me/channelname, t.me/joinchat/XXXX, @channelusername)")

class ChannelInfo(BaseModel):
    id: int
    title: str
    username: Optional[str] = None
    description: Optional[str] = None
    members_count: Optional[int] = None
    type: str

# --- Helper function to get an authenticated client ---
async def get_authenticated_client() -> Client:
    logger.info(f"Attempting to get authenticated client for {PHONE_NUMBER}")
    assert PHONE_NUMBER is not None, "PHONE_NUMBER cannot be None here due to initial checks"
    session_name = f"user_session_{PHONE_NUMBER.replace('+', '')}"
    script_dir = Path(__file__).parent
    session_file = script_dir / f"{session_name}.session"

    if not API_ID or not API_HASH:
        logger.error("API_ID or API_HASH not configured for get_authenticated_client")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Server configuration error.")

    if not session_file.exists():
        logger.error(f"Session file not found for {PHONE_NUMBER}: {session_file}. Please run create_session.py first.")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Session for {PHONE_NUMBER} not found. Run session creation script.")

    client = Client(name=session_name, api_id=API_ID, api_hash=API_HASH, workdir=str(script_dir))
    logger.info(f"Authenticated client instance created for {PHONE_NUMBER}")
    return client

# --- Dependency to get the shared Pyrogram client ---
async def get_current_client(request: Request) -> Client:
    client: Optional[Client] = getattr(request.app.state, "pyrogram_client", None)
    if not client or not client.is_connected:
        logger.error("Pyrogram client not available or not connected in app.state.")
        # It's crucial that the client is available after startup.
        # If it's not, it indicates a severe issue during app initialization.
        # Service unavailable is appropriate here.
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Telegram client is not ready or encountered an issue during startup. Please check server logs."
        )
    return client
# --- Root Endpoint ---
@app.get("/")
async def root():
    logger.info("Root endpoint accessed")
    return {"message": "Welcome to the Telegram Channel Viewer API (Pre-authenticated)"}

# --- Rate Limiting (Optional, if needed) ---
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded):
    client_host = request.client.host if request.client else "Unknown Client"
    logger.warning(f"Rate limit exceeded for {client_host}: {exc.detail}")
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content={"detail": f"Rate limit exceeded: {exc.detail}"},
    )

# --- API Endpoints ---
@app.get("/api/dialogs", response_model=List[DialogItem])
async def list_dialogs(client: Client = Depends(get_current_client)): # MODIFIED
    logger.info(f"Received request for dialogs (using session for {PHONE_NUMBER})")
    dialog_items: List[DialogItem] = []
    try:
        # client is now injected by Depends(get_current_client)
        dialogs_iterable = client.get_dialogs()
        if dialogs_iterable: 
            async for dialog in dialogs_iterable: 
                dialog_type_str = "unknown"
                current_chat = dialog.chat
                if current_chat and current_chat.type and hasattr(current_chat.type, 'name'):
                    dialog_type_str = current_chat.type.name.lower()
                
                title = "N/A"
                if current_chat:
                    if hasattr(current_chat, 'title') and current_chat.title:
                        title = current_chat.title
                    elif hasattr(current_chat, 'first_name') and current_chat.first_name:
                        title = current_chat.first_name
                        if hasattr(current_chat, 'last_name') and current_chat.last_name:
                            title += f" {current_chat.last_name}"
                    elif hasattr(current_chat, 'username') and current_chat.username: 
                        title = current_chat.username
                
                if current_chat and hasattr(current_chat, 'id'):
                    dialog_items.append(DialogItem(
                        id=current_chat.id,
                        title=title,
                        type=dialog_type_str
                    ))
        logger.info(f"Successfully fetched {len(dialog_items)} dialogs for {PHONE_NUMBER}")
        return dialog_items
    except HTTPException: 
        raise
    except Exception as e: 
        logger.error(f"Error fetching dialogs for {PHONE_NUMBER}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch dialogs: {str(e)}")

@app.get("/api/channels/{channel_id_or_username}/info", response_model=ChannelInfo)
async def get_channel_info(channel_id_or_username: Union[int, str], client: Client = Depends(get_current_client)): # MODIFIED
    logger.info(f"Request for channel info: {channel_id_or_username} (session: {PHONE_NUMBER})")
    
    peer_to_get_info_for: Union[int, str]
    is_numeric_id = False

    if isinstance(channel_id_or_username, int):
        peer_to_get_info_for = channel_id_or_username
        is_numeric_id = True
    elif isinstance(channel_id_or_username, str):
        try:
            peer_to_get_info_for = int(channel_id_or_username)
            is_numeric_id = True
            logger.info(f"Parsed '{channel_id_or_username}' as numeric ID for get_channel_info: {peer_to_get_info_for}")
        except ValueError:
            peer_to_get_info_for = channel_id_or_username
            is_numeric_id = False
            logger.info(f"Treating '{channel_id_or_username}' as a username string for get_channel_info.")
    else:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel_id_or_username type for get_channel_info.")

    try:
        # client is now injected by Depends(get_current_client)
        chat_obj: Optional[Union[Chat, ChatPreview]] = None
        
        try:
            chat_obj = await client.get_chat(peer_to_get_info_for)
            logger.info(f"Successfully fetched chat info directly for {peer_to_get_info_for}")
        
        except PeerIdInvalid:
            logger.warning(f"PeerIdInvalid for {peer_to_get_info_for} in get_channel_info. Attempting to find in dialogs if numeric.")
            if is_numeric_id:
                numeric_id_to_find = int(peer_to_get_info_for) 
                dialogs_generator = client.get_dialogs()
                found_in_dialogs = False
                if dialogs_generator:
                    async for dialog in dialogs_generator:
                        if dialog.chat and dialog.chat.id == numeric_id_to_find:
                            logger.info(f"Found peer {numeric_id_to_find} in dialogs. Retrying get_chat for info.")
                            chat_obj = await client.get_chat(numeric_id_to_find)
                            found_in_dialogs = True
                            break
                if not found_in_dialogs:
                    logger.error(f"Peer {numeric_id_to_find} not found in dialogs after PeerIdInvalid.")
                    raise 
            else: 
                logger.warning(f"PeerIdInvalid for username '{peer_to_get_info_for}' in get_channel_info. Cannot resolve further.")
                raise
        
        if not chat_obj:
            logger.error(f"Chat object is None for {peer_to_get_info_for} after all attempts in get_channel_info.")
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Chat '{peer_to_get_info_for}' not found or inaccessible after resolution attempts.")

        chat_id_val = getattr(chat_obj, 'id', None)
        if chat_id_val is None:
             raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Could not retrieve chat ID from chat object.")

        title_val = getattr(chat_obj, 'title', None)
        if not title_val and isinstance(chat_obj, Chat): 
            title_val = getattr(chat_obj, 'first_name', None)
        if not title_val: 
             title_val = getattr(chat_obj, 'username', "N/A")

        username_val = getattr(chat_obj, 'username', None)
        description_val = getattr(chat_obj, 'description', None)
        members_count_val = getattr(chat_obj, 'members_count', None)
        
        chat_type_str_val = "unknown"
        if hasattr(chat_obj, 'type') and chat_obj.type and isinstance(chat_obj.type, pyrogram.enums.ChatType) and hasattr(chat_obj.type, 'name'):
             chat_type_str_val = chat_obj.type.name.lower()

        return ChannelInfo(
            id=chat_id_val,
            title=title_val,
            username=username_val,
            description=description_val,
            members_count=members_count_val,
            type=chat_type_str_val
        )
    except (ChannelPrivate, ChannelInvalid, PeerIdInvalid, UserNotParticipant) as e: 
        logger.warning(f"Channel not accessible or invalid for get_channel_info '{channel_id_or_username}': {type(e).__name__} - {e}", exc_info=False) 
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Channel '{channel_id_or_username}' not found, not accessible, or you are not a participant.")
    except HTTPException: 
        raise
    except Exception as e: 
        logger.error(f"Unexpected error fetching channel info for '{channel_id_or_username}': {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch channel info due to an unexpected error: {str(e)}")

@app.get("/api/channels/{channel_id_or_username}/messages", response_model=List[MessageItem])
async def get_channel_messages(
    channel_id_or_username: Union[int, str],
    limit: int = Query(20, ge=1, le=100),
    offset_message_id: int = Query(0),
    client: Client = Depends(get_current_client) # MODIFIED
):
    logger.info(f"Request for messages from {channel_id_or_username}, limit {limit}, offset_id {offset_message_id} (session: {PHONE_NUMBER})")
    messages_data: List[MessageItem] = []
    
    peer_to_process: Union[int, str]
    is_numeric_id = False

    if isinstance(channel_id_or_username, int):
        peer_to_process = channel_id_or_username
        is_numeric_id = True
    elif isinstance(channel_id_or_username, str):
        try:
            peer_to_process = int(channel_id_or_username)
            is_numeric_id = True
            logger.info(f"Successfully parsed '{channel_id_or_username}' as numeric ID: {peer_to_process}")
        except ValueError:
            peer_to_process = channel_id_or_username # Treat as username
            is_numeric_id = False
            logger.info(f"Treating '{channel_id_or_username}' as a username string.")
    else:
        # Should not happen with Union[int, str] type hint, but as a safeguard
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid channel_id_or_username type.")

    try:
        # client is now injected by Depends(get_current_client)
        resolved_peer_for_history: Union[int, str] = peer_to_process

        if is_numeric_id:
            current_numeric_id = int(peer_to_process) 
            logger.info(f"Processing numeric ID: {current_numeric_id}")
            try:
                await client.get_chat(current_numeric_id)
                logger.info(f"Successfully 'met' peer {current_numeric_id} directly.")
                resolved_peer_for_history = current_numeric_id
            except PeerIdInvalid:
                logger.info(f"Direct peer resolution failed for {current_numeric_id}, trying to find in dialogs...")
                peer_found_in_dialogs = False
                dialogs_generator_inner = client.get_dialogs()
                if dialogs_generator_inner:
                    async for dialog in dialogs_generator_inner:
                        if dialog.chat and dialog.chat.id == current_numeric_id:
                            resolved_peer_for_history = dialog.chat.id
                            peer_found_in_dialogs = True
                            logger.info(f"Found peer {current_numeric_id} in dialogs.")
                            break
                if not peer_found_in_dialogs:
                    logger.warning(f"Peer {current_numeric_id} not found in dialogs.")
                    raise HTTPException(
                        status_code=status.HTTP_404_NOT_FOUND,
                        detail=f"Channel/Peer ID {current_numeric_id} not found in your dialogs. Ensure access."
                    )
            except (ChannelInvalid, ChannelPrivate, UserNotParticipant) as e:
                logger.warning(f"Failed to 'meet' peer {current_numeric_id} due to: {type(e).__name__} - {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Channel/Peer ID {current_numeric_id} is invalid, private, or not accessible: {str(e)}"
                )
        else: # Is a username string
            current_username = str(peer_to_process)
            logger.info(f"Processing username: {current_username}")
            try:
                await client.get_chat(current_username)
                logger.info(f"Successfully 'met' peer (username) {current_username} before fetching history.")
                resolved_peer_for_history = current_username
            except (PeerIdInvalid, ChannelInvalid, ChannelPrivate, UserNotParticipant) as e:
                logger.warning(f"Failed to 'meet' peer (username) {current_username} due to: {type(e).__name__} - {e}")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Channel/Username {current_username} is invalid, private, or not accessible: {str(e)}"
                )
        
        history_params: dict[str, Any] = {"chat_id": resolved_peer_for_history, "limit": limit}
        if offset_message_id > 0:
            history_params["offset_id"] = offset_message_id

        messages_generator = client.get_chat_history(**history_params) 
        if messages_generator:
            async for msg in messages_generator:
                if not isinstance(msg, PyrogramMessage): continue

                sender_str = "N/A"
                if msg.from_user:
                    sender_str = msg.from_user.first_name or str(msg.from_user.id)
                    if msg.from_user.last_name:
                        sender_str += f" {msg.from_user.last_name}"
                elif msg.sender_chat: 
                    sender_str = msg.sender_chat.title or str(msg.sender_chat.id)
                
                media_type_str: Optional[str] = None
                file_id_str: Optional[str] = None
                file_name_str: Optional[str] = None
                mime_type_str: Optional[str] = None
                poll_data_obj: Optional[PollDetails] = None

                if msg.media and isinstance(msg.media, pyrogram.enums.MessageMediaType):
                    media_type_str = msg.media.name.lower() 

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
                    elif msg.document:
                        file_id_str = msg.document.file_id
                        file_name_str = msg.document.file_name
                        mime_type_str = msg.document.mime_type
                    elif msg.poll and isinstance(msg.poll, Poll): 
                        pyro_poll = msg.poll
                        poll_type_name = "unknown"
                        if pyro_poll.type and hasattr(pyro_poll.type, 'name'):
                             poll_type_name = pyro_poll.type.name.lower()

                        poll_data_obj = PollDetails(
                            question=pyro_poll.question,
                            options=[PollOptionItem(text=opt.text, data=opt.data) for opt in pyro_poll.options],
                            total_voters=getattr(pyro_poll, 'total_voters', None),
                            is_closed=pyro_poll.is_closed,
                            is_anonymous=pyro_poll.is_anonymous,
                            type=poll_type_name,
                            allows_multiple_answers=pyro_poll.allows_multiple_answers,
                            quiz_correct_option_id=pyro_poll.correct_option_id
                        )
                
                msg_date_timestamp = 0
                if msg.date and isinstance(msg.date, datetime.datetime):
                    msg_date_timestamp = int(msg.date.timestamp())
                
                is_outgoing_msg = getattr(msg, 'outgoing', None) 

                messages_data.append(MessageItem(
                    id=msg.id,
                    text=msg.text or msg.caption, 
                    sender=sender_str,
                    date=msg_date_timestamp,
                    media_type=media_type_str,
                    file_id=file_id_str,
                    file_name=file_name_str,
                    mime_type=mime_type_str,
                    poll_data=poll_data_obj,
                    is_outgoing=is_outgoing_msg
                ))
        logger.info(f"Fetched {len(messages_data)} messages from {channel_id_or_username} for {PHONE_NUMBER}")
        return messages_data
    except (ChannelPrivate, ChannelInvalid, PeerIdInvalid, UserNotParticipant):
        logger.warning(f"Channel not accessible or invalid for messages: {channel_id_or_username}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found, not accessible, or you are not a participant.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching messages from {channel_id_or_username} for {PHONE_NUMBER}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to fetch messages: {str(e)}")

@app.post("/api/channels/join", status_code=status.HTTP_200_OK)
async def join_telegram_channel(body: JoinChannelBody, client: Client = Depends(get_current_client)): # MODIFIED
    logger.info(f"Request to join channel/group: {body.invite_link} (session: {PHONE_NUMBER})")
    try:
        # client is now injected by Depends(get_current_client)
        joined_chat = await client.join_chat(body.invite_link) 
        logger.info(f"Successfully joined chat: {getattr(joined_chat, 'title', joined_chat.id)} for {PHONE_NUMBER}")
        
        chat_type_name = "unknown"
        if joined_chat.type and hasattr(joined_chat.type, 'name'):
            chat_type_name = joined_chat.type.name.lower()

        return {
            "message": "Successfully joined chat",
            "chat_id": joined_chat.id,
            "title": getattr(joined_chat, 'title', None) or getattr(joined_chat, 'first_name', "N/A"),
            "type": chat_type_name
        }
    except (InviteHashExpired, InviteHashInvalid):
        logger.warning(f"Invalid or expired invite link: {body.invite_link}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invite link is invalid or has expired.")
    except PeerIdInvalid:
        logger.warning(f"Cannot find chat by invite link/username: {body.invite_link}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat not found with the provided link/username.")
    except UserNotParticipant: 
        logger.warning(f"User already a participant or other issue with joining {body.invite_link}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Could not join chat. User might already be a participant or other restriction.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error joining channel {body.invite_link} for {PHONE_NUMBER}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to join channel: {str(e)}")

@app.post("/api/send_message", status_code=status.HTTP_201_CREATED)
async def send_message_to_chat(body: SendMessageBody, client: Client = Depends(get_current_client)): # MODIFIED
    logger.info(f"Request to send message to {body.chat_id} (session: {PHONE_NUMBER})")
    try:
        # client is now injected by Depends(get_current_client)
        sent_message = await client.send_message(chat_id=body.chat_id, text=body.text) 
        logger.info(f"Message sent to {body.chat_id} by {PHONE_NUMBER}, message_id: {sent_message.id}")
        return {
            "message": "Message sent successfully",
            "chat_id": sent_message.chat.id, 
            "message_id": sent_message.id
        }
    except PeerIdInvalid:
        logger.warning(f"Cannot send message, invalid chat_id: {body.chat_id}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat ID not found or invalid.")
    except UserNotParticipant:
        logger.warning(f"Cannot send message to {body.chat_id}, user not a participant.", exc_info=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a participant of this chat or sending messages is restricted.")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending message to {body.chat_id} for {PHONE_NUMBER}: {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to send message: {str(e)}")

@app.get("/api/media/{chat_id}/{message_id}/{file_id_or_type}")
async def get_media_file_endpoint(
    chat_id: Union[int, str],
    message_id: int,
    file_id_or_type: str,
    client: Client = Depends(get_current_client) # MODIFIED
):
    logger.info(f"Request for media: chat_id={chat_id}, msg_id={message_id}, file_id/type='{file_id_or_type}' (session: {PHONE_NUMBER})")
    try:
        # client is now injected by Depends(get_current_client)
        message_obj = await client.get_messages(chat_id=chat_id, message_ids=message_id) 
        
        if not message_obj or not isinstance(message_obj, PyrogramMessage):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Message not found or inaccessible.")

        actual_file_id_to_download: Optional[str] = None
        file_name_for_response = "downloaded_media"
        mime_type_for_response = "application/octet-stream"

        if message_obj.media:
            requested_type_lower = file_id_or_type.lower()
            if requested_type_lower == "photo" and message_obj.photo:
                actual_file_id_to_download = message_obj.photo.file_id
                file_name_for_response = f"{message_obj.photo.file_unique_id}.jpg"
                mime_type_for_response = "image/jpeg"
            elif requested_type_lower == "video" and message_obj.video:
                actual_file_id_to_download = message_obj.video.file_id
                file_name_for_response = message_obj.video.file_name or f"{message_obj.video.file_unique_id}.mp4"
                mime_type_for_response = message_obj.video.mime_type or "video/mp4"
            elif requested_type_lower == "document" and message_obj.document:
                actual_file_id_to_download = message_obj.document.file_id
                file_name_for_response = message_obj.document.file_name or f"{message_obj.document.file_unique_id}.dat"
                mime_type_for_response = message_obj.document.mime_type or "application/octet-stream"
            elif requested_type_lower == "audio" and message_obj.audio:
                actual_file_id_to_download = message_obj.audio.file_id
                file_name_for_response = message_obj.audio.file_name or f"{message_obj.audio.file_unique_id}.mp3"
                mime_type_for_response = message_obj.audio.mime_type or "audio/mpeg"
            
            if not actual_file_id_to_download:
                media_attributes = ['photo', 'video', 'audio', 'document', 'voice', 'video_note', 'sticker', 'animation']
                for attr_name in media_attributes:
                    media_attr_obj = getattr(message_obj, attr_name, None)
                    if media_attr_obj and hasattr(media_attr_obj, 'file_id') and media_attr_obj.file_id == file_id_or_type:
                        actual_file_id_to_download = media_attr_obj.file_id
                        if hasattr(media_attr_obj, 'file_name') and media_attr_obj.file_name:
                            file_name_for_response = media_attr_obj.file_name
                        elif hasattr(media_attr_obj, 'file_unique_id'):
                            ext_map = {"photo": ".jpg", "video": ".mp4", "audio": ".mp3"}
                            ext = ext_map.get(attr_name, ".dat")
                            file_name_for_response = f"{media_attr_obj.file_unique_id}{ext}"
                        if hasattr(media_attr_obj, 'mime_type') and media_attr_obj.mime_type:
                            mime_type_for_response = media_attr_obj.mime_type
                        break
        
        if not actual_file_id_to_download:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Media '{file_id_or_type}' not found on message, or message has no such media, or type is not downloadable directly.")

        logger.info(f"Attempting to download file_id: {actual_file_id_to_download}")
        
        downloaded_object = await client.download_media(
            message=actual_file_id_to_download,
            in_memory=True
        )

        if not downloaded_object:
            logger.error(f"Download_media returned None for file_id: {actual_file_id_to_download}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Error processing media file after download (returned None).")

        if not isinstance(downloaded_object, io.BytesIO):
            logger.error(f"Download_media did not return BytesIO for file_id: {actual_file_id_to_download}. Type: {type(downloaded_object)}")
            if isinstance(downloaded_object, str) and os.path.exists(downloaded_object):
                try:
                    os.remove(downloaded_object)
                    logger.info(f"Cleaned up unexpected file on disk: {downloaded_object}")
                except OSError as e_os:
                    logger.error(f"Error cleaning up unexpected file {downloaded_object}: {e_os}")
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Media download resulted in an unexpected type.")
        
        file_stream: io.BytesIO = downloaded_object 
        file_stream.seek(0)

        return StreamingResponse(
            file_stream,
            media_type=mime_type_for_response,
            headers={"Content-Disposition": f"attachment; filename=\"{file_name_for_response}\""}
        )

    except PeerIdInvalid:
        logger.warning(f"Media download: Invalid chat_id: {chat_id}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Chat ID not found or invalid.")
    except UserNotParticipant:
        logger.warning(f"Media download: User not participant in chat {chat_id}", exc_info=False)
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User is not a participant of this chat.")
    except HTTPException: 
        raise
    except Exception as e:
        logger.error(f"Error downloading media (chat: {chat_id}, msg: {message_id}, file: {file_id_or_type}): {e}", exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to download media: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    logger.info("Starting Uvicorn server directly from main.py (for debugging)")
    if not all([API_ID_STR, API_HASH, PHONE_NUMBER]):
        print("ERROR: TELEGRAM_API_ID, TELEGRAM_API_HASH, and PHONE_NUMBER must be set in .env or environment.")
    else:
        uvicorn.run(app, host="0.0.0.0", port=8000)

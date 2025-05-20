# Telegram Channel Web Viewer (User Account) - AI Handoff

This document summarizes the current state of the project, intended for AI collaboration.

## Project Overview

This project aims to build a responsive web application that allows a user to view content from their subscribed Telegram channels directly in a web browser using their personal account.

**Disclaimer:** Accessing user account data via the Telegram API requires handling sensitive information like phone numbers and verification codes. Ensure you understand the security and privacy implications and comply with Telegram's Terms of Service.

## Technology Stack

*   **Frontend:** Vue.js
*   **Backend:** Python with FastAPI
*   **Telegram API Library:** Pyrogram
*   **Database:** SQLite (for session persistence)
*   **Styling:** Tailwind CSS

## File Structure

```
.
├── .gitignore
├── README.md
├── README_AI.md  <-- This file
└── backend/
    ├── .env
    ├── main.py
    ├── requirements.txt
    ├── test_auth.bat
    └── venv/
        └── ... (Python virtual environment files)
```

## Backend Development Status (Python/FastAPI)

*   **Completed:**
    *   Basic FastAPI application structure.
    *   Environment variable loading (`.env`).
    *   Pyrogram client setup and session management.
    *   Authentication endpoints (`/api/auth/request_code`, `/api/auth/submit_code`) implemented and tested with <mcfile name="test_auth.bat" path="c:\Users\HP\Desktop\Code\test\backend\test_auth.bat"></mcfile>.
    *   Endpoint to list user dialogs (`/api/dialogs`).
    *   Endpoint to fetch messages from a specific channel (`/api/channels/{channel_id}/messages`).
    *   Basic error handling for Pyrogram exceptions (e.g., `SessionPasswordNeeded`, `PhoneCodeInvalid`, `UserNotParticipant`).
    *   Logging configured.
    *   `requirements.txt` and `.gitignore` updated.
    *   Implemented pagination for the message fetching endpoint (`/api/channels/{channel_id}/messages`) using `limit` and `offset` parameters.

*   **Completed:**
    *   Basic FastAPI application structure.
    *   Environment variable loading (`.env`).
    *   Pyrogram client setup and session management.
    *   Authentication endpoints (`/api/auth/request_code`, `/api/auth/submit_code`) implemented and tested with <mcfile name="test_auth.bat" path="c:\Users\HP\Desktop\Code\test\backend\test_auth.bat"></mcfile>.
    *   Endpoint to list user dialogs (`/api/dialogs`).
    *   Endpoint to fetch messages from a specific channel (`/api/channels/{channel_id}/messages`).
    *   Basic error handling for Pyrogram exceptions (e.g., `SessionPasswordNeeded`, `PhoneCodeInvalid`, `UserNotParticipant`).
    *   Logging configured.
    *   `requirements.txt` and `.gitignore` updated.
    *   Implemented pagination for the message fetching endpoint (`/api/channels/{channel_id}/messages`) using `limit` and `offset` parameters.
    *   Handling of different message media types in the `format_message` helper and API response (photos, documents completed; video, audio, voice, sticker, and polls support added).

*   **Pending:**
    *   Adding endpoints for other potential features (e.g., joining channels, getting channel info) completed. Sending messages endpoint added.
    *   Implementing a database layer for caching or persistent storage. Replaced in-memory `temp_storage` for login hash with SQLite for session persistence.
    *   More robust error handling and input validation (enhanced for `/api/channels/{channel_id}/messages` endpoint, including specific Pyrogram error handling and validation for `limit` and `offset` query parameters).
    *   Security considerations (e.g., rate limiting, proper session management beyond simple file storage).

## Frontend Development Status (Vue.js)

*   **Status:** Basic structure set up with Vite and Vue.js, Tailwind CSS integrated.

## Next Steps for AI

Based on the project plan and current status, potential next steps for AI assistance could include:

1.  Implementing the handling of remaining message media types (e.g., polls) in the backend.
2.  Setting up the basic Vue.js frontend structure.
3.  Integrating the frontend with the existing backend endpoints.
4.  Adding endpoints for other potential features (e.g., sending messages, joining channels, getting channel info).

Feel free to pick a task or ask for clarification on any of the pending items.
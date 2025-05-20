# Telegram Web Viewer (User Account) - Developer Handoff & AI Collaboration Guide

**Version:** 1.1.0 (As of 2025-05-20 - *Please update with current date upon major handoff*)
**Last Updated By:** Cline (AI Assistant)
**Reason for Update:** Refactored to session-based authentication, removing phone number from API calls and frontend auth flow.

## 1. Introduction for Collaborators

Welcome! This document serves as a comprehensive handoff guide for developers and AI collaborators taking over or contributing to the "Telegram Channel Web Viewer" project. Its purpose is to provide a clear understanding of the project's architecture, current status, setup procedures, and key areas for future development.

Our goal is to enable a smooth transition and facilitate productive contributions. Please read through this document carefully.

## 2. Project Overview

This project aims to build a responsive web application that allows a user to view content from their subscribed Telegram channels directly in a web browser using their personal account. Authentication is handled by creating a session file on the backend, which is then used for all API interactions.

**Typical User Flow:**
1.  **Session Creation (One-time or as needed):** User runs `backend/create_session.py` to generate a Telegram session file (e.g., `user_session_YOUR_PHONE_NUMBER.session`). This involves entering their phone number and a login code received via Telegram.
2.  **Application Launch:** User starts the backend and frontend servers.
3.  **View Dialogs:** The web application (`src/App.vue`) directly loads `DialogList.vue`.
4.  `DialogList.vue` fetches and displays the user's Telegram dialogs using the pre-authenticated session on the backend.
5.  User selects a channel/dialog.
6.  `ChannelMessages.vue` fetches and displays messages from the selected channel, again using the backend's authenticated session.

**Disclaimer:** Accessing user account data via the Telegram API requires handling sensitive information. Ensure you understand the security and privacy implications and comply with Telegram's Terms of Service. Session files are sensitive and must be protected.

## 3. Technology Stack & Key Libraries

*   **Frontend:** Vue.js (v3 with Composition API)
    *   **Key Libraries:**
        *   `axios`: For making HTTP requests to the backend API.
*   **Backend:** Python with FastAPI
    *   **Key Libraries:**
        *   `uvicorn`: ASGI server for running the FastAPI application.
        *   `pyrogram` & `TgCrypto`: For interacting with the Telegram API.
        *   `python-dotenv`: For managing environment variables (API ID/Hash).
        *   `aiosqlite`: (Verify usage - was for temp phone_code_hash, may be less relevant now).
        *   `slowapi`: (Verify usage - was for rate limiting auth endpoints, may be less relevant now).
*   **Database:** SQLite
    *   **Rationale:** Pyrogram manages the main user session files (`.session`). `telegram_sessions.db` was used for temporary `phone_code_hash` during the old interactive login flow; its current role with `create_session.py` needs verification.
*   **Styling:** Basic CSS in `src/style.css`. (The `frontend/` directory has Tailwind CSS, but the primary app is in `src/`).

## 4. Project Setup

### Backend Setup (Python/FastAPI)

1.  **Navigate to the `backend` directory.**
2.  **Create and activate a Python virtual environment.**
3.  **Install dependencies:**
    ```bash
    pip install -r backend/requirements.txt
    ```
4.  **Configure API Credentials:**
    Ensure `API_ID` and `API_HASH` in `backend/create_session.py` and `backend/main.py` are set to your values from [my.telegram.org](https://my.telegram.org/apps). You can also place them in a `backend/.env` file:
    ```env
    TELEGRAM_API_ID="YOUR_API_ID"
    TELEGRAM_API_HASH="YOUR_API_HASH"
    # Optional: DEFAULT_SESSION_NAME="user_session_YOUR_PHONE_NUMBER" (used by main.py)
    ```
5.  **Create Telegram Session File:**
    Run the script from the project root:
    ```bash
    python backend/create_session.py
    ```
    Follow prompts for phone number and login code. This creates a `.session` file (e.g., `user_session_YOUR_PHONE_NUMBER.session`) in the `backend/` directory.
    The `backend/main.py` is configured to load a session named `user_session_YOUR_PHONE_NUMBER.session` by default (this can be configured via `DEFAULT_SESSION_NAME` in `.env` or directly in `main.py`).

### Frontend Setup (Vue.js - Root Project `src/`)

1.  **Navigate to the project root directory.**
2.  **Install Node.js dependencies:**
    ```bash
    npm install
    ```

### Running the Application

1.  **Start the Backend Server:**
    *   Ensure your virtual environment is activated and the `.session` file exists in `backend/`.
    *   From the project root:
        ```bash
        python backend/main.py
        ```
        Or for development:
        ```bash
        uvicorn backend.main:app --reload --port 8000
        ```
    *   API at `http://localhost:8000`.

2.  **Start the Frontend Development Server:**
    *   In a new terminal, from the project root:
        ```bash
        npm run dev
        ```
    *   App typically at `http://localhost:5173`.

## 5. Key Architectural Decisions

*   **Session Management:**
    *   Authentication is handled by a pre-generated Pyrogram `.session` file in the `backend/` directory.
    *   The `backend/create_session.py` script is used to generate this session file.
    *   The FastAPI backend (`main.py`) loads this session on startup to initialize an authenticated Pyrogram client. All subsequent API calls use this single, pre-authenticated client.
    *   **Security Note:** Session files are highly sensitive. Ensure the `backend/` directory and its `.session` files are secured and not publicly accessible or committed to version control (ensure `.gitignore` covers `*.session`).
*   **Primary Frontend Location:** The core, active frontend is in the project's root `src/` directory. The `frontend/` subdirectory is a separate, older/alternative setup.
*   **Media Handling:**
    *   Backend's `format_message` extracts `file_id`.
    *   Frontend uses `file_id` to call `/api/media/{file_id}`.
    *   Backend endpoint `get_media_file` uses the authenticated Pyrogram client to download media and stream it.
*   **API Design:** The API is now simpler as it doesn't require `phone_number` for authentication in each request. The backend uses its pre-loaded session.

## 6. File Structure (Key Files)

```
.
├── backend/
│   ├── .env (optional, for API_ID/HASH, DEFAULT_SESSION_NAME)
│   ├── main.py             # FastAPI app, loads session
│   ├── create_session.py   # Generates .session file
│   ├── requirements.txt
│   └── *.session           # Telegram session files (e.g., user_session_YOURPHONE.session) - DO NOT COMMIT
├── src/                    # Primary Vue.js frontend
│   ├── App.vue             # Root component, directly shows DialogList
│   ├── components/
│   │   ├── ChannelMessages.vue
│   │   └── DialogList.vue
│   ├── main.js
│   └── style.css
├── package.json
├── vite.config.js
├── README.md
└── README_AI.md  <-- This file
```
*(Note: `AuthForm.vue` has been removed. The `frontend/` directory is not the primary focus.)*

## 7. API Endpoint Documentation

The backend API (running on `http://localhost:8000` by default) now relies on a pre-authenticated session.

| Method | Path                                      | Description                                                                 | Key Request Parameters/Body | Example Success Response                                                                |
| :----- | :---------------------------------------- | :-------------------------------------------------------------------------- | :-------------------------- | :-------------------------------------------------------------------------------------- |
| GET    | `/api/dialogs`                            | Lists the authenticated user's dialogs. Session is pre-loaded by backend.   | None                        | `[{"id": ..., "title": "...", "type": "..."}, ...]`                                      |
| GET    | `/api/channels/{channel_id}/messages`     | Fetches messages from a specific channel/dialog. Session pre-loaded.        | Path: `channel_id`. Query: `limit`, `offset` | `[{"id": ..., "text": ..., "sender": ..., "date": ..., "media_type": ..., ...}, ...]` |
| GET    | `/api/channels/{channel_id}/info`         | Fetches information about a specific channel/dialog. Session pre-loaded.    | Path: `channel_id`          | `{"id": ..., "title": ..., "type": ..., "username": ..., "description": ...}`           |
| POST   | `/api/send_message`                       | Sends a text message. Session pre-loaded.                                   | `{"chat_id": ..., "text": "Hello"}` | `{"message": "Message sent successfully!"}`                                             |
| POST   | `/api/channels/join`                      | Joins a channel. Session pre-loaded.                                        | `{"channel_id": ...}`       | `{"message": "Successfully joined channel!"}`                                           |
| GET    | `/api/media/{file_id}`                    | Downloads/streams a media file. Session pre-loaded.                         | Path: `file_id`             | `FileResponse` / `StreamingResponse` with media content.                                |

*Authentication endpoints (`/api/auth/request_code`, `/api/auth/submit_code`) are no longer part of the main application flow and may be removed from `backend/main.py` if not used for other purposes.*

## 8. Development Status

*   **Backend:**
    *   Switched to session-file based authentication using `create_session.py`.
    *   API endpoints updated to use the pre-loaded session, removing `phone_number` dependencies.
    *   `aiosqlite` and `slowapi` usage might be reduced or removed if old auth endpoints are deprecated.
*   **Frontend (`src/`):**
    *   `AuthForm.vue` removed.
    *   `App.vue` directly renders `DialogList.vue`.
    *   `DialogList.vue` and `ChannelMessages.vue` updated to call APIs without `phone_number`.
    *   Media display (images, downloads) and poll display remain functional.

## 9. Frontend Components Overview (Root `src/` directory)

*   **`App.vue`**: Main root component. Directly renders `DialogList` or `ChannelMessages` based on `selectedChannelId`.
*   **`DialogList.vue`**: Displays user's Telegram dialogs. Fetches from `/api/dialogs` (backend uses its pre-authenticated session). Emits `select-channel`.
*   **`ChannelMessages.vue`**: Displays messages. Fetches from `/api/channels/{channel_id}/messages`. Handles media and polls. Emits `back-to-dialogs`.

## 10. Current Known Issues / Areas for Attention

*   **Media Display & UX:**
    *   Backend `/api/media/{file_id}` should set correct `Content-Type` for better inline display.
    *   Frontend image loading could have indicators. Video/audio are download links.
*   **Security:**
    *   **Session File Security:** The `.session` file in `backend/` is critical. It must NOT be committed to Git and the directory must be secured.
    *   Rate limiting: If old auth endpoints are removed, `slowapi` might be unnecessary. Consider if other endpoints need protection.
*   **Code Cleanup (Backend):**
    *   Old authentication logic (routes, helper functions, `aiosqlite` usage for `phone_code_hash`) in `backend/main.py` should be removed if fully deprecated.
*   **Styling:** UI is basic. `src/style.css` is minimal.

## 11. Next Steps for AI (Development Roadmap)

**High Priority:**
1.  **Security - Session File Handling:** Ensure `.gitignore` correctly excludes `*.session` and `telegram_sessions.db`. Emphasize secure storage of session files in deployment.
2.  **Backend Code Cleanup:** Remove unused old authentication routes and related logic/dependencies (like `aiosqlite` for temp storage if confirmed unused) from `backend/main.py`.
3.  **Improved Media Handling (Backend & Frontend):**
    *   Backend: `/api/media/{file_id}` to set `Content-Type`.
    *   Frontend: Loading indicators for images.

**Medium Priority:**
4.  **Error Handling & User Feedback (Full Stack):** Refine for clarity.
5.  **Styling/UI Consistency:** Improve `src/style.css` or integrate a framework like Tailwind CSS properly into `src/`.

**Low Priority / Future Considerations:**
6.  **Advanced Features:** Sending media, real-time updates (WebSockets).
7.  **Caching:** For API responses if needed.

## 12. Planned Development Phases (Post-Refactor)

**Phase 1: Stabilization & Cleanup**
*   Task 1.1: Verify and ensure session file security (gitignore, documentation).
*   Task 1.2 (Backend): Remove deprecated authentication code from `main.py`.
*   Task 1.3 (Backend): Update `requirements.txt` if `aiosqlite` or `slowapi` are removed.
*   Task 1.4 (Full Stack): Test all existing functionality thoroughly with the new session-based auth.

**Phase 2: Core Improvements**
*   Task 2.1 (Backend): Implement `Content-Type` setting in `/api/media/{file_id}`.
*   Task 2.2 (Frontend): Add loading indicators for images.
*   Task 2.3 (Full Stack): Enhance error handling and user feedback.

**Phase 3: UI/UX Enhancements**
*   Task 3.1 (Frontend): Improve overall styling and UI consistency.

**Phase 4: Feature Expansion (Future)**
*   Task 4.1: Consider poll voting, sending media, etc.

## 13. Contact & Questions

*   **Project Owner/Lead:** [Insert Name/Contact Method Here]
*   **Previous AI Collaborator:** Cline (via current interaction platform)

---
*This handoff document is intended to be a living document. Please update it as the project evolves.*

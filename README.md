# Telegram Web Client

This project is a web-based Telegram client that allows you to view your dialogs and messages. It uses a Python backend with FastAPI and Telethon, and a Vue.js 3 frontend with Vite.

## Features

- View a list of your Telegram dialogs (chats, channels, groups).
- Select a dialog to view its messages.
- Basic media display (images, download links for other files).
- Session-based authentication for Telegram.
- Modern user interface for an enhanced user experience.
- Dark mode toggle for user preference.

## Technologies Used

- **Backend**:
  - Python 3
  - FastAPI (for the web framework)
  - Telethon (for interacting with the Telegram API)
  - Uvicorn (ASGI server)
- **Frontend**:
  - Vue.js 3 (with `<script setup>` SFCs)
  - Vite (for the frontend build tooling and dev server)
  - Axios (for making HTTP requests to the backend)
- **Database**:
  - SQLite (for storing Telethon session files, e.g., `telegram_sessions.db` and `user_session_PHONE.session`)

## Project Structure

```
.
├── backend/                # Python FastAPI backend
│   ├── main.py             # FastAPI application
│   ├── create_session.py   # Script to create Telegram session
│   ├── requirements.txt    # Python dependencies
│   └── ...                 # Session files will be created here
├── src/                    # Vue.js frontend (main application)
│   ├── App.vue             # Main App component
│   ├── main.js             # Vue app initialization
│   ├── components/         # Vue components (DialogList, ChannelMessages)
│   └── ...
├── frontend/               # Older/alternative Vue.js frontend (potentially unused or for reference)
├── public/
├── package.json
├── vite.config.js
└── README.md
```

## Setup and Installation

### Prerequisites

- Python 3.8+
- Node.js 16+ and npm

### 1. Backend Setup

Navigate to the project root directory (`c:/Users/HP/Desktop/Code/test`).

a. **Create a Python virtual environment (optional but recommended):**
   ```bash
   python -m venv venv
   # Activate the virtual environment
   # On Windows:
   .\venv\Scripts\activate
   # On macOS/Linux:
   # source venv/bin/activate
   ```

b. **Install Python dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

c. **Create your Telegram session:**
   You need to authenticate with Telegram to allow the application to access your account.
   Run the `create_session.py` script:
   ```bash
   python backend/create_session.py
   ```
   You will be prompted for your phone number, and then a login code sent to your Telegram account. Enter these when prompted. This will create a session file (e.g., `user_session_YOUR_PHONE_NUMBER.session`) and a `telegram_sessions.db` file in the `backend` directory.
   **Important**: The `API_ID` and `API_HASH` in `backend/create_session.py` and `backend/main.py` should be replaced with your own values obtained from [my.telegram.org](https://my.telegram.org/apps).

### 2. Frontend Setup

Navigate to the project root directory (`c:/Users/HP/Desktop/Code/test`).

a. **Install Node.js dependencies:**
   ```bash
   npm install
   ```

## Running the Application

### 1. Start the Backend Server

Ensure your Telegram session file is present in the `backend` directory.
From the project root directory:
```bash
python backend/main.py
```
Or, for development with auto-reload:
```bash
uvicorn backend.main:app --reload --port 8000
```
The backend server will typically run on `http://localhost:8000`.

### 2. Start the Frontend Development Server

In a **new terminal**, from the project root directory:
```bash
npm run dev
```
This will usually start the frontend application on `http://localhost:5173` and open it in your default web browser.

You should now be able to see your Telegram dialogs listed in the web interface.

## Notes

- The application currently uses the frontend code located in the `src/` directory. The `frontend/` directory might contain an older or alternative version.
- Ensure that the API endpoints called by the frontend (e.g., in `src/components/DialogList.vue` and `src/components/ChannelMessages.vue`) match the port your backend is running on (default `http://localhost:8000`).

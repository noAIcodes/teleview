# 🚀 Telegram Web Viewer 🚀

Welcome to the Telegram Web Viewer! This project allows you to browse your Telegram chats, channels, and messages directly in your web browser using your personal account. It features a sleek, modern interface with dark mode support.

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![Vue.js](https://img.shields.io/badge/Vue.js-3-42b883.svg)](https://vuejs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100.0-009688.svg)](https://fastapi.tiangolo.com/)
[![Pyrogram](https://img.shields.io/badge/Pyrogram-2-orange.svg)](https://pyrogram.org/)

## ✨ Features

*   **👁️ View Dialogs:** See a list of all your Telegram chats, channels, and groups.
*   **💬 Browse Messages:** Select any dialog to view its message history.
*   **🖼️ Enhanced Media Display:**
    *   **Interactive Image Viewer:** Click on any image in a chat to open it in a full-featured modal viewer. Supports zoom, pan, rotation, and other standard image viewing controls (powered by `v-viewer`).
    *   Download links for videos, documents, and other file types.
*   **🔒 Secure Session Authentication:** Uses Pyrogram's session management for secure access to your Telegram account.
*   **🖥️ Modern User Interface:** Enjoy a clean, responsive, and user-friendly design.
*   **🌙 Dark Mode:** Toggle between light and dark themes for comfortable viewing.
*   **📤 Outgoing Message Indicator:** Easily identify messages sent by you.
*   **ℹ️ Channel Information:** View details about channels and groups.
*   **➕ Join Channels:** Ability to join new channels or groups via invite links.
*   **✉️ Send Messages:** Send text messages to your chats.

## 🛠️ Technologies Used

*   **Backend (Python 🐍):**
    *   **FastAPI:** High-performance web framework for building APIs.
    *   **Pyrogram:** Modern, elegant, and asynchronous MTProto API client library for Telegram.
    *   **Uvicorn:** ASGI server for running the FastAPI application.
    *   **python-dotenv:** Manages environment variables for configuration.
*   **Frontend (Vue.js 🎨):**
    *   **Vue.js 3:** Progressive JavaScript framework (using Composition API and `<script setup>` SFCs).
    *   **Vite:** Next-generation frontend tooling for fast development and optimized builds.
    *   **Axios:** Promise-based HTTP client for making API requests.
*   **Database (Session Storage):**
    *   **SQLite:** Pyrogram uses SQLite (`.session` files) to store session information.

## 📂 Project Structure

```
.
├── backend/                # Python FastAPI backend
│   ├── .env                # Environment variables (API ID, HASH, Phone)
│   ├── main.py             # FastAPI application logic
│   ├── create_session.py   # Script to generate Telegram session file
│   ├── requirements.txt    # Python dependencies
│   └── *.session           # Telegram session files (e.g., user_session_YOURPHONE.session) - DO NOT COMMIT!
├── src/                    # Main Vue.js frontend application
│   ├── App.vue             # Root Vue component
│   ├── main.js             # Vue app initialization
│   ├── components/         # Reusable Vue components (DialogList, ChannelMessages, etc.)
│   ├── assets/             # Static assets like images
│   └── style.css           # Global styles, including dark mode
├── public/                 # Public assets for Vite
├── .gitignore
├── package.json            # Frontend dependencies and scripts
├── vite.config.js          # Vite configuration
├── README.md               # This file!
└── README_AI.md            # AI collaboration and development handoff guide
```

## ⚙️ Setup and Installation

### Prerequisites

*   Python 3.8+
*   Node.js 16+ and npm
*   A Telegram API ID and API Hash (get these from [my.telegram.org](https://my.telegram.org/apps))

### 1. Backend Setup 🔧

Navigate to the project root directory.

**a. Create and Activate a Python Virtual Environment:**
   ```bash
   python -m venv backend/venv
   # On Windows:
   backend\venv\Scripts\activate
   # On macOS/Linux:
   # source backend/venv/bin/activate
   ```

**b. Install Python Dependencies:**
   ```bash
   pip install -r backend/requirements.txt
   ```

**c. Configure Environment Variables:**
   Create a file named `.env` inside the `backend/` directory. Add your Telegram API credentials and phone number:
   ```env
   TELEGRAM_API_ID="YOUR_API_ID"
   TELEGRAM_API_HASH="YOUR_API_HASH"
   PHONE_NUMBER="YOUR_PHONE_NUMBER_WITH_COUNTRY_CODE" # e.g., +11234567890
   ```
   Replace the placeholder values with your actual credentials.

**d. Create Your Telegram Session:**
   Run the `create_session.py` script from the project root:
   ```bash
   python backend/create_session.py
   ```
   You will be prompted for your phone number (it will use the one from `.env` if available, otherwise it will ask) and then a login code sent to your Telegram account.
   This will create a session file (e.g., `user_session_YOURPHONENUMBER.session`) in the `backend/` directory. This file is crucial and contains your active session.

   **🔒 Important Security Note:**
   The `.session` file and your `.env` file contain sensitive information.
   *   **NEVER** commit your `.session` file or `.env` file (with real credentials) to version control (e.g., Git).
   *   The `.gitignore` file should already be configured to ignore `*.session` and `.env`. Double-check this.

### 2. Frontend Setup 🌐

Navigate to the project root directory.

**a. Install Node.js Dependencies:**
   ```bash
   npm install
   ```

## ▶️ Running the Application

### 1. Start the Backend Server サーバー

*   Ensure your Python virtual environment is activated.
*   Ensure your `.env` file is configured and the `.session` file exists in the `backend/` directory.
*   From the project root directory:
    ```bash
    python backend/main.py
    ```
    Or, for development with auto-reload:
    ```bash
    uvicorn backend.main:app --reload --port 8000
    ```
    The backend API will typically be available at `http://localhost:8000`.

### 2. Start the Frontend Development Server 💻

*   In a **new terminal**, from the project root directory:
    ```bash
    npm run dev
    ```
    This will usually start the frontend application (typically at `http://localhost:5173`) and open it in your default web browser.

You should now be able to access the Telegram Web Viewer in your browser!

## 🚀 Deployment Guide (Conceptual for Local Use)

This application is primarily designed for local use due to the nature of personal Telegram account access.

1.  **Backend:**
    *   The FastAPI backend can be run using `uvicorn` as shown in the "Running the Application" section. For a more production-like setup (still local), you could use Gunicorn with Uvicorn workers if you were to expose it beyond your local machine (not recommended for this type of app without significant security considerations).
    *   Ensure the `.env` and `.session` files are present and correctly configured in the `backend` directory where `main.py` is run.

2.  **Frontend:**
    *   To build the frontend for "production" (e.g., to serve static files):
        ```bash
        npm run build
        ```
        This will create a `dist/` directory with the optimized static assets.
    *   You can then serve these static files using any static file server (e.g., Nginx, Caddy, or even a simple Python HTTP server for local testing). The backend (FastAPI) could also be configured to serve these static files if desired, though a dedicated web server is common for production.

**Key Considerations for any "Deployment":**
*   **Security:** Access to the machine running the backend implies access to the Telegram session. This is paramount.
*   **Session Persistence:** The `.session` file must be persisted.
*   **Environment Variables:** `TELEGRAM_API_ID`, `TELEGRAM_API_HASH`, and `PHONE_NUMBER` must be available to the backend environment.

## 🔍 Troubleshooting Guide

*   **"Database is locked" error on backend:**
    *   This was a common issue with older versions due to multiple Pyrogram client instances. The current version uses a single shared client, which should prevent this. If you encounter it, ensure you are on the latest code version.
    *   Ensure no other processes are trying to access the same `.session` file simultaneously.

*   **Session file not found / Authentication errors (`401 Unauthorized`):**
    *   Ensure you have run `python backend/create_session.py` successfully.
    *   Verify that a `user_session_YOURPHONENUMBER.session` file exists in the `backend/` directory.
    *   Check that `PHONE_NUMBER` in `backend/.env` matches the session file name convention.
    *   Your `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` in `backend/.env` must be correct and active.
    *   The session might have expired or been revoked on Telegram's side. Try re-running `backend/create_session.py`.

*   **"Too many requests" / `FloodWait` error:**
    *   Telegram has rate limits. If you make too many requests in a short period, you might get temporarily blocked. The error message usually indicates how long to wait.
    *   The backend startup will fail if a `FloodWait` occurs during initial client connection. Wait for the specified time and try restarting the backend.

*   **Frontend shows errors or doesn't load data:**
    *   Check your browser's developer console (usually F12) for error messages.
    *   Ensure the backend server is running and accessible at `http://localhost:8000` (or the configured port).
    *   Verify that the API URLs in the frontend components (e.g., in `src/components/*.vue`) correctly point to your backend.
    *   CORS errors: The FastAPI backend is configured with CORS middleware for `http://localhost:5173`. If you are running the frontend on a different port, you might need to update `allow_origins` in `backend/main.py`.

*   **`create_session.py` fails:**
    *   Ensure `TELEGRAM_API_ID` and `TELEGRAM_API_HASH` are correctly set in `backend/.env`.
    *   Make sure you are entering the phone number in the correct international format (e.g., `+11234567890`) when prompted or in the `.env` file.
    *   Double-check the login code you receive from Telegram.

*   **Python/Node.js command not found:**
    *   Ensure Python and Node.js are installed correctly and their executable paths are included in your system's PATH environment variable.
    *   If using a Python virtual environment, make sure it's activated.

## 📄 Example `.env` File for GitHub Users

For users cloning the repository, create a `backend/.env` file with the following structure. **Do not commit your actual credentials.**

```env
# backend/.env.example

# Obtain your API ID and API Hash from https://my.telegram.org/apps
TELEGRAM_API_ID="YOUR_ACTUAL_API_ID_HERE"
TELEGRAM_API_HASH="YOUR_ACTUAL_API_HASH_HERE"

# Your phone number in international format (e.g., +11234567890)
# This will be used by create_session.py and main.py
PHONE_NUMBER="YOUR_PHONE_NUMBER_HERE"
```

## 🤝 Contributing

Contributions are welcome! Please feel free to fork the repository, make changes, and submit pull requests. For major changes, please open an issue first to discuss what you would like to change.

## 📜 License

This project is open-source. Please refer to the license file if one is included. (Assuming MIT or similar if not specified).

---

Happy Browsing! 🎉

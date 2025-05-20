import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv
from pyrogram.client import Client
from pyrogram.errors import SessionPasswordNeeded, PhoneCodeInvalid, PhoneNumberInvalid

# Load environment variables from .env file
dotenv_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=dotenv_path)

API_ID = os.getenv("TELEGRAM_API_ID")
API_HASH = os.getenv("TELEGRAM_API_HASH")

if not API_ID or not API_HASH:
    print("Error: TELEGRAM_API_ID and TELEGRAM_API_HASH must be set in .env file")
    exit(1)

# At this point, API_ID and API_HASH are guaranteed to be strings.
# We can cast them to satisfy Pylance if it's still complaining,
# or add assertions. For Client, API_ID needs to be int.
API_ID_INT = int(API_ID)
API_HASH_STR = str(API_HASH) # Explicitly a string

async def main():
    phone_number_input = input("Please enter your phone number (e.g., +1234567890): ").strip()
    session_name = f"user_session_{phone_number_input.replace('+', '')}"
    
    print(f"Attempting to create session: {session_name}.session")
    print(f"Using API_ID: {API_ID}")

    # Ensure workdir is the directory of this script so session file is saved here
    script_dir = Path(__file__).parent
    
    client = Client(
        name=session_name,
        api_id=API_ID_INT,
        api_hash=API_HASH_STR,
        workdir=str(script_dir) # Save session file in the backend directory
    )

    try:
        print("Connecting to Telegram...")
        await client.connect()
        print("Connected.")

        print(f"Sending code to {phone_number_input}...")
        try:
            sent_code_info = await client.send_code(phone_number_input)
            print("Verification code sent.")
        except PhoneNumberInvalid:
            print(f"Error: Invalid phone number format: {phone_number_input}")
            await client.disconnect()
            return
        except Exception as e:
            print(f"Error sending code: {e}")
            await client.disconnect()
            return

        while True:
            code = input("Please enter the verification code you received: ").strip()
            try:
                print("Submitting code...")
                await client.sign_in(
                    phone_number=phone_number_input,
                    phone_code_hash=sent_code_info.phone_code_hash,
                    phone_code=code
                )
                print("Sign in successful (code accepted).")
                break  # Exit loop if sign_in is successful
            except SessionPasswordNeeded:
                print("Two-Factor Authentication is enabled.")
                password = input("Please enter your 2FA password: ").strip()
                try:
                    await client.check_password(password)
                    print("2FA password accepted. Sign in successful.")
                    break # Exit loop if 2FA is successful
                except Exception as e_2fa:
                    print(f"Error with 2FA password: {e_2fa}. Please try again or restart the script.")
                    # Optionally, allow retrying 2FA or break to restart script
                    # For simplicity, we'll let the user restart if 2FA fails multiple times.
            except PhoneCodeInvalid:
                print("Error: Invalid verification code. Please try again.")
                # Loop will continue to ask for the code
            except Exception as e:
                print(f"An error occurred during sign_in: {e}")
                await client.disconnect()
                return
        
        me = await client.get_me()
        print(f"Successfully signed in as: {me.first_name} (ID: {me.id})")
        print(f"Session file '{session_name}.session' should now be created in the '{script_dir}' directory.")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if client.is_connected:
            print("Disconnecting client...")
            await client.disconnect()
            print("Client disconnected.")

if __name__ == "__main__":
    asyncio.run(main())

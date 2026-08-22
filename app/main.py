import httpx
from fastapi import FastAPI, Request
from dotenv import load_dotenv
import os

from agent import run_agent

load_dotenv()  # Load environment variables from .env file

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"


@app.post("/webhook")
async def webhook(request: Request):
    data = await request.json()

    # Check if the update contains a text message
    if "message" in data and "text" in data["message"]:
        chat_id = data["message"]["chat"]["id"]
        user_text = data["message"]["text"]

        if user_text.startswith("/create_issue"):
            # Extract title and body from the command
            command = user_text[len("/create_issue") :].strip()

            response = await run_agent(command)  # You can modify the body as needed
            # Prepare the payload to send back
            payload = {"chat_id": chat_id, "text": f"{response}"}
        else:
            # Prepare the payload to send back
            payload = {"chat_id": chat_id, "text": f"You said: {user_text}"}

        # Send the message back to the user asynchronously
        async with httpx.AsyncClient() as client:
            await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)

    # Telegram expects a 200 OK response, otherwise it will retry sending
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Hello, this is the Telegram bot webhook server, new!"}

import httpx
import logging
import sys
from fastapi import FastAPI, Request, Header, HTTPException, BackgroundTasks
from dotenv import load_dotenv
import os

from app.agent import run_agent

load_dotenv()  # Load environment variables from .env file

logger = logging.getLogger("aiops")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler(sys.stdout)

formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")

handler.setFormatter(formatter)

logger.addHandler(handler)

app = FastAPI()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
WEBHOOK_SECRET_TOKEN = os.getenv("WEBHOOK_SECRET_TOKEN")
TELEGRAM_API = f"https://api.telegram.org/bot{TOKEN}"

raw_allowed = os.getenv("ALLOWED_USERS", "")
ALLOWED_USERS = set(raw_allowed.split(",")) if raw_allowed else set()

PROCESSED_UPDATES = set()  # To keep track of processed update_ids


async def process_telegram_update(data):
    if data:
        logger.info(f"Received Telegram webhook update: {data}")

        chat_id = None
        result = None

        try:
            # Check if the update contains a text message

            if "callback_query" in data:
                logger.info(f"Received callback query: {data['callback_query']}")
                callback = data["callback_query"]
                chat_id = callback["message"]["chat"]["id"]
                decision = callback["data"]

                async with httpx.AsyncClient(timeout=10.0) as client:
                    await client.post(
                        f"{TELEGRAM_API}/answerCallbackQuery",
                        json={"callback_query_id": callback["id"]},
                    )

                    await client.post(
                        f"{TELEGRAM_API}/editMessageReplyMarkup",
                        json={
                            "chat_id": chat_id,
                            "message_id": callback["message"]["message_id"],
                            "reply_markup": {"inline_keyboard": []},
                        },
                    )

                result = await run_agent(chat_id=chat_id, resume_decision=decision)

                payload = {
                    "chat_id": chat_id,
                    "text": f"After approval, {result['text']}.",
                }

                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{TELEGRAM_API}/sendMessage", json=payload
                        )
                        response.raise_for_status()
                except httpx.HTTPError:
                    logger.exception("Failed to send Telegram reply message.")

            elif "message" in data and "text" in data["message"]:
                chat_id = data["message"]["chat"]["id"]
                user_text = data["message"]["text"]

                logger.info(f"Received message from chat_id {chat_id}: {user_text}")

                if user_text.startswith("/issue"):
                    # Extract title and body from the command
                    command = user_text[len("/issue") :].strip()
                    logger.info(f"Processing command: {command}")

                    response = await run_agent(
                        command=command, chat_id=chat_id
                    )  # You can modify the body as needed
                    reply_text = (
                        response.get("text")
                        if isinstance(response, dict)
                        else str(response)
                    )
                    if not reply_text or not str(reply_text).strip():
                        reply_text = "I’m preparing the GitHub action."
                    payload = {"chat_id": chat_id, "text": reply_text}

                elif user_text.startswith("/talk"):
                    # Extract the message to talk about
                    command = user_text[len("/talk") :].strip()
                    logger.info(f"Processing talk command: {command}")

                    result = await run_agent(
                        command=command, chat_id=chat_id
                    )  # You can modify the body as needed
                    reply_text = (
                        result.get("text") if isinstance(result, dict) else str(result)
                    )
                    if not reply_text or not str(reply_text).strip():
                        reply_text = "I’m preparing the GitHub action."
                    logger.info(f"Replying to chat_id {chat_id} with: {reply_text}")
                    payload = {"chat_id": chat_id, "text": reply_text}

                else:
                    # Prepare the payload to send back
                    payload = {"chat_id": chat_id, "text": f"You said: {user_text}"}

                # Send the message back to the user asynchronously
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.post(
                            f"{TELEGRAM_API}/sendMessage", json=payload
                        )
                        response.raise_for_status()
                except httpx.HTTPError:
                    logger.exception("Failed to send Telegram reply message.")

            else:
                logger.warning("Received update without a text message.")

            # logger.info(f"Result from run_agent: {result}")

            if result and chat_id:
                logger.info(
                    f"lsdfjAsking for user approval for chat_id {chat_id} with result: {result}"
                )
                async with httpx.AsyncClient() as client:
                    if result.get("interrupt"):
                        desc = result["interrupt"]["description"]
                        payload = {
                            "chat_id": chat_id,
                            "text": f"Agent wants to execute: {desc}",
                            "parse_mode": "Markdown",
                            "reply_markup": {
                                "inline_keyboard": [
                                    [
                                        {"text": "Approve", "callback_data": "approve"},
                                        {"text": "Reject", "callback_data": "reject"},
                                    ]
                                ]
                            },
                        }

                        await client.post(f"{TELEGRAM_API}/sendMessage", json=payload)

        except Exception:
            logger.exception("Unexpected error while handling Telegram webhook update.")

        # Telegram expects a 200 OK response, otherwise it will retry sending
        return {"status": "ok"}

    else:
        logger.warning("Received empty or invalid Telegram webhook update.")
        return {"status": "ok"}


@app.post("/webhook")
async def webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    x_telegram_bot_api_secret_token: str = Header(None),
):

    if x_telegram_bot_api_secret_token != WEBHOOK_SECRET_TOKEN:
        logger.warning("Unauthorized access attempt to webhook.")
        raise HTTPException(status_code=403, detail="Unauthorized")

    try:
        data = await request.json()
        update_id = data.get("update_id")

        if update_id in PROCESSED_UPDATES:
            return {"status": "ok"}  # Ignore duplicate updates

        PROCESSED_UPDATES.add(update_id)

        if len(PROCESSED_UPDATES) > 1000:
            PROCESSED_UPDATES.pop()  # Remove the oldest update_id to prevent memory bloat

    except Exception:
        logger.exception("Failed to decode Telegram webhook payload.")
        return {"status": "ok"}

    user_info = data.get("message", {}).get("from") or data.get(
        "callback_query", {}
    ).get("from", {})
    user_id = str(user_info.get("id")) if user_info else None

    if ALLOWED_USERS and user_id not in ALLOWED_USERS:
        logger.warning(f"Unauthorized user {user_id} attempted to access the bot.")
        return {"status": "ok"}  # Respond with 200 OK to avoid retries

    background_tasks.add_task(process_telegram_update, data)
    return {"status": "ok"}


@app.get("/")
async def root():
    return {"message": "Hello, this is the Telegram bot webhook server, new!"}

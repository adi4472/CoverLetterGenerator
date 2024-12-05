import os
import sqlite3
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse
from slack_sdk.errors import SlackApiError
import openai
from dotenv import load_dotenv
import logging

logging.basicConfig(level=logging.DEBUG)  # Enable detailed logging

def start_socket_mode():
    app_token = os.getenv("SLACK_APP_TOKEN")  # Slack App Token for Socket Mode
    bot_token = os.getenv("SLACK_BOT_TOKEN")  # Slack Bot Token

    # Initialize SocketModeClient
    socket_mode_client = SocketModeClient(
        app_token=app_token,
        web_client=WebClient(token=bot_token)
    )

    # Event handler for message events
    def handle_message_events(req: SocketModeRequest, resp: SocketModeResponse):
        logging.debug(f"Received event: {req.payload}")  # Log the entire event
        payload = req.payload
        event = payload.get("event", {})

        if event.get("type") == "message" and "subtype" not in event:
            logging.debug(f"Message received: {event['text']}")  # Log the incoming message

            # Respond to the message (e.g., echo back the text)
            WebClient(token=bot_token).chat_postMessage(
                channel=event["channel"],
                text=f"Received message: {event['text']}"
            )
        resp.ack()

    # Register the event handler
    socket_mode_client.socket_mode_request_listeners.append(handle_message_events)

    # Start the Socket Mode connection
    try:
        logging.info("Connecting to Slack via Socket Mode...")
        socket_mode_client.connect()
        logging.info("Bot is now running...")
    except Exception as e:
        logging.error(f"Error connecting to Slack: {str(e)}")

if __name__ == "__main__":
    start_socket_mode()

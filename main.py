import os, sys
import json
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseSettings, BaseModel
from discord_webhook import DiscordWebhook
import logging
from meraki_register_webhook import MerakiWebhook

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


class Settings(BaseSettings):
        # Store local settings
        BOT_BASE_URL = "http://localhost:8000"
        USE_NGROK = False
        try:
                WEBHOOK_ID = os.environ.get("WEBHOOK_ID")
                WEBHOOK_TOKEN = os.environ.get("WEBHOOK_TOKEN")
        except:
                logging.exception("Error: Could not collect Discord webook token/ID info. \
                                   Please set the appropriate environmental variables")
                sys.exit(1)


class MerakiWebhook(BaseModel):
        # Meraki API ver / secret
        version: float
        sharedSecret: str
        sentAt: str
        # Org info
        organizationId: int
        organizationName: str
        organizationUrl: str
        # Network Info
        networkId: str
        networkName: str
        networkTags: Optional[list] = None
        deviceSerial: str
        # Device Info
        deviceMac: str
        deviceName: str
        deviceUrl: str
        deviceTags: Optional[list] = None
        deviceModel: str
        # Alert Info
        alertId: str
        alertType: str
        alertTypeId: str
        alertLevel: str
        occurredAt: str
        alertData: Optional[dict] = None

if settings.USE_NGROK:
        # Import ngrok library
        from pyngrok import ngrok

        # Get uvicon port number
        port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 8000

        # Open a new ngrok tunnel & Update settings
        ngrok_url = ngrok.connect(port).public_url
        settings.BOT_BASE_URL = ngrok_url


@app.post('/post-msg-discord')
async def post_from_meraki(item: MerakiWebhook):
        logging.info("Got POST request")
        if item.sharedSecret == meraki.SHARED_SECRET:
                logging.info("API secret matches")
                print(item)
                sendDiscordMsg(item)
                return {'message': 'Got it!'}
        else:
                logging.error(f"Received bad API secret: {item.sharedSecret}")
                return {'message': 'Bad webhook secret'}


async def sendDiscordMsg(data):
        """
        Send alert via Discord webhooks
        """
        content = formatMessage(data)
        logging.info("Sending Discord message...")
        POST_URL = f"https://discord.com/api/webhooks/{settings.WEBHOOK_ID}/{settings.WEBHOOK_TOKEN}"
        logging.info(f"Using Discord webhook ID: {settings.WEBHOOK_ID}")
        try:
                webhook = DiscordWebhook(url=POST_URL,content=str(content))
                response = webhook.execute()
        except:
                logging.exception("Failed to send message")
                return
        if response.status_code == 200:
                logging.info("Message successfully posted to Discord webhook")
        else:
                logging.error("Failed to send message")
        return 

def formatMessage(data):
        logging.info("Formatting message payload...")
        message = []
        message.append(data['deviceModel'])
        message.append(data['alertTypeId'])
        message = message.join('\r\n')
        return message

if __name__ == '__main__':
        settings = Settings()
        meraki = MerakiWebHook()
        app = FastAPI()

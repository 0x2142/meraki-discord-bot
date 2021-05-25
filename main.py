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
        USE_NGROK = True
        
        WEBHOOK_ID = os.environ.get("DISCORD_WEBHOOK_ID")
        WEBHOOK_TOKEN = os.environ.get("DISCORD_WEBHOOK_TOKEN")
        if WEBHOOK_ID == None or WEBHOOK_TOKEN == None:
                logging.error("Error: Could not collect Discord webook token/ID info. " +
                                   "Please set the appropriate environmental variables.")
                sys.exit(1)


class MerakiAlert(BaseModel):
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

def setup_ngrok():
        from pyngrok import ngrok

        # Get uvicon port number
        port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 8000

        # Open a new ngrok tunnel & Update settings
        ngrok_url = ngrok.connect(port, bind_tls=True).public_url
        settings.BOT_BASE_URL = ngrok_url
        meraki.update_webhook_url(ngrok_url)

settings = Settings()
meraki = MerakiWebhook()
if settings.USE_NGROK: setup_ngrok()
logging.info(f"Accepting requests at: {settings.BOT_BASE_URL}")
app = FastAPI()

@app.post('/post-msg-discord')
async def post_from_meraki(item: MerakiAlert):
        logging.info("Got POST request")
        if item.sharedSecret == meraki.webhook_config['sharedSecret']:
                logging.info("API secret matches")
                logging.info(item)
                sendDiscordMsg(item)
                return {'message': 'Message received'}
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
        message = [":alarm_clock: :alarm_clock: Meraki Alert :alarm_clock: :alarm_clock: "]
        message.append(f"Alert for device: {data.deviceName}")
        message.append(f"Message info: {data.alertTypeId}")
        message.append(f"Occurred at: {data.occurredAt}")
        sendmessage = ""
        for each in message:
                sendmessage += each + "\r\n"
        return sendmessage

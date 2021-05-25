import os, sys
import json
from typing import Optional
from fastapi import FastAPI
from pydantic import BaseSettings, BaseModel
from discord_webhook import DiscordWebhook
import logging
from meraki_register_webhook import MerakiWebhook

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


def setup_ngrok():
    from pyngrok import ngrok

    logging.info("ngrok enabled. Spinning up tunnels...")

    # Get uvicon port number
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 8000

    # Open a new ngrok tunnel & Update settings
    ngrok_url = ngrok.connect(port, bind_tls=True).public_url
    return ngrok_url


class Settings(BaseSettings):
    # Webserver / inbound settings
    USE_NGROK = os.environ.get("USE_NGROK")
    if USE_NGROK == False:
        WEBHOOK_URL = os.environ.get("MERAKI_TARGET_WEBHOOK_URL")
        if not WEBHOOK_URL:
            logging.error(
                "Error: ngrok disabled, but no self URL provided. Missing config item MERAKI_TARGET_WEBHOOK_URL"
            )
            sys.exit(1)
    else:
        WEBHOOK_URL = setup_ngrok()

    # Meraki-specific settings
    NETWORK_NAME = os.environ.get("MERAKI_TARGET_NETWORK_NAME")
    if not NETWORK_NAME:
        logging.error("Error: Missing config item MERAKI_TARGET_NETWORK_NAME")
        sys.exit(1)

    WEBHOOK_NAME = os.environ.get("MERAKI_WEBHOOK_NAME")
    MERAKI_API_KEY = os.environ.get("MERAKI_API_KEY")
    if not MERAKI_API_KEY:
        logging.error("Error: Missing config item MERAKI_API_KEY")
        sys.exit(1)

    # Discord settings
    DISCORD_URL = os.environ.get("DISCORD_URL")
    if not DISCORD_URL:
        logging.error("Error: Missing config item DISCORD_URL")
        sys.exit(1)

    # Defaults, for those settings which are not required
    if not WEBHOOK_NAME:
        WEBHOOK_NAME = "api-generated_Discord"
    if USE_NGROK == None:
        USE_NGROK = True


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


## Main Stuffs:
settings = Settings()
# if settings.USE_NGROK: setup_ngrok()
meraki = MerakiWebhook(
    settings.MERAKI_API_KEY,
    settings.WEBHOOK_NAME,
    settings.WEBHOOK_URL,
    settings.NETWORK_NAME,
)
logging.info(f"Accepting requests at: {settings.WEBHOOK_URL}")
app = FastAPI()


@app.post("/post-msg-discord")
async def post_from_meraki(item: MerakiAlert):
    logging.info("Got POST request")
    if item.sharedSecret == meraki.webhook_config["sharedSecret"]:
        logging.info("API secret matches")
        logging.info(item)
        sendDiscordMsg(item)
        return {"message": "Message received"}
    else:
        logging.error(f"Received bad API secret: {item.sharedSecret}")
        return {"message": "Bad webhook secret"}


def sendDiscordMsg(data):
    """
    Send alert via Discord webhooks
    """
    content = formatMessage(data)
    logging.info("Sending Discord message...")
    try:
        webhook = DiscordWebhook(url=settings.DISCORD_URL, content=str(content))
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

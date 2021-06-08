import asyncio
import json
import logging
import os
import sys
from typing import Optional

from discord_webhook import DiscordWebhook
from fastapi import FastAPI
from pydantic import BaseModel, BaseSettings
from pyngrok import ngrok

from meraki_register_webhook import MerakiWebhook

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


def setup_ngrok():
    """
    Build ngrok tunnel for inbound webhook calls
    """
    logging.info("ngrok enabled. Spinning up tunnels...")

    # Get Auth token:
    NGROK_AUTH_TOKEN = os.environ.get("NGROK_TOKEN")
    if not NGROK_AUTH_TOKEN:
        logging.error("Missing config item: NGROK_TOKEN. Program will still run, but non-authenticated tunnels will break after some time...")
    if NGROK_AUTH_TOKEN:
        logging.info("Adding ngrok authentication token...")
        ngrok.set_auth_token(NGROK_AUTH_TOKEN)

    # Get uvicon port number
    port = sys.argv[sys.argv.index("--port") + 1] if "--port" in sys.argv else 8000

    # Open a new ngrok tunnel & Update settings
    ngrok_url = ngrok.connect(port, bind_tls=True).public_url
    return ngrok_url


async def check_ngrok():
    """
    ngrok may re-establish session occasionally, which means new public URL.
    This will check intermittently, and update Meraki's config if needed
    """
    while True:
        await asyncio.sleep(30)
        logging.info("Checking ngrok session...")
        current_url = ngrok.get_tunnels()[0].public_url
        logging.info(f"Current ngrok URL: {current_url}")
        logging.info(f"Current webhook URL: {settings.WEBHOOK_URL}")
        if current_url != settings.WEBHOOK_URL:
            logging.info(
                "Current ngrok URL does not match Meraki-configured URL. Need to update..."
            )
            meraki.update_webhook_url(current_url)


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


@app.on_event("startup")
async def startup_event():
    if settings.USE_NGROK:
        asyncio.create_task(check_ngrok())


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
    """
    Format incoming message before passing to Discord
    """
    logging.info("Formatting message payload...")
    time = (data.occurredAt).split("T")
    message = [":alarm_clock: __**Meraki Alert**__ :alarm_clock: "]
    message.append(f"**Device:** {data.deviceName}")
    message.append(f"**Message info:** {data.alertType}")
    message.append(f"**Occurred at:** {time[0]} - {time[1][:8]}")
    if len(data.alertData) > 0:
        message.append(f"**Additional data:** ```fix\r\n{data.alertData}\r\n```")
    sendmessage = ""
    for each in message:
        sendmessage += each + "\r\n"
    return sendmessage

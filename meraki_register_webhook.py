import json
import logging
import os
import secrets
import string

import httpx

logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

API_BASE_URL = 'https://api.meraki.com/api/v1'
SHARED_SECRET = ''.join((secrets.choice(string.ascii_letters + string.digits + string.punctuation) for i in range(24)))

NETWORK = os.environ.get("MERAKI_TARGET_NETWORK_NAME")
WEBHOOK_URL = os.environ.get("MERAKI_TARGET_WEBHOOK_URL")
WEBHOOK_NAME = 'api-generated_Discord'
MERAKI_API_KEY = os.environ.get("MERAKI_API_KEY")

class MerakiWebhook():
    def __init__(self):
        self.headers = {"X-Cisco-Meraki-API-Key": MERAKI_API_KEY}
        self.webhook_config = {
            "name": WEBHOOK_NAME,
            "url": WEBHOOK_URL,
            "sharedSecret": SHARED_SECRET
        }
        logging.info("Beginning Meraki API webhook check/create/update")
        self.get_org_id()
        self.get_network_id()
        self.get_curent_webhooks()
        if self.webhook_exists:
            self.update_existing_webhook()
        else:
            self.create_new_webhook()

    def get_org_id(self):
        """
        Query Meraki API for which Organizations we have access to & return Org ID
        """
        url = API_BASE_URL + "/organizations"
        response = httpx.get(url, headers=self.headers)
        orgID = json.loads(response.text)[0]["id"]
        logging.info(f"Using Org ID: {orgID}")
        self.orgID = orgID

    def get_network_id(self):
        """
        Use Organization ID to pull list of networks we have access to
        """
        url = API_BASE_URL + f"/organizations/{self.orgID}/networks"
        response = httpx.get(url, headers=self.headers)
        data = json.loads(response.text)
        logging.info(f"Got Network list, searching for network: {NETWORK}")
        for network in data:
            if network['name'] == NETWORK:
                self.networkID = network['id']
                logging.info(f"Found Network: {NETWORK}, ID: {self.networkID}")
                return

    def get_curent_webhooks(self):
        """
        Query list of all current configured webhooks
        """
        url = API_BASE_URL + f'/networks/{self.networkID}/webhooks/httpServers'

        response = httpx.get(url, headers=self.headers)
        if response.status_code == 200:
            self.current_webhooks = json.loads(response.text)
            logging.info(f"Found {len(self.current_webhooks)} existing webhooks")
        self.webhook_exists = False
        if len(self.current_webhooks) >= 1:
            logging.info("Checking if we own any of the existing webhooks....")
            for config_item in self.current_webhooks:
                if config_item['name'] == WEBHOOK_NAME:
                    self.webhookID = config_item['id']
                    logging.info(f"Found existing webhook ID: {self.webhookID}")
                    self.webhook_exists = True

    def create_new_webhook(self):
        """
        Create new webhook config, if it doesn't already exist
        """
        url = API_BASE_URL + f"/networks/{self.networkID}/webhooks/httpServers"
        logging.info("Attempting to create new webhook config")
        response = httpx.post(url, json=self.webhook_config, headers=self.headers)
        if response.status_code == 200:
            webhook = json.loads(response.text)
            logging.info(f"New webhook created, ID: {webhook['id']}")
            print(response.text)
        else:
            logging.error("Failed to create new webhook. Error:")
            logging.error(response.text)

    def update_existing_webhook(self):
        """
        Locate existing webhook ID created by this automation,
        then update with any new parameters
        """
        url = API_BASE_URL + f"/networks/{self.networkID}/webhooks/httpServers/{self.webhookID}"
        logging.info(f"Updating existing webhook with ID: {self.webhookID}")
        response = httpx.put(url, json=self.webhook_config, headers=self.headers)
        if response.status_code == 200:
            logging.info("Successfully updated webhook with new config")
        else:
            logging.error("Failed to update webhook. Error:")
            logging.error(response.text)


if __name__ == '__main__':
    MerakiWebhook()

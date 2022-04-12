# Note: This project is no longer maintained
Meraki now supports native templating within Dashboard, so this bot is no longer needed. I submitted a discord template to the Meraki webhook template repo [here](https://github.com/meraki/webhook-payload-templates)

***

# meraki-discord-bot

Readme in progress, some info below - but not yet completed! Project is a work in progress, so please check back later for more updates.

Docker image: https://hub.docker.com/r/0x2142/meraki-discord-bot

### Description:

A quick bot to take in Meraki alerting webhooks via POST requests, then forward them to a desired Discord room.

### Features:
 - Receives webhook alerts sent from Meraki Dashboard
 - Formats alert messaging & forwards to Discord server
 - Auto-generates/rotates webhook shared secret
 - Uses dynamic ngrok tunnels & dynamically updates Meraki webhook destinations

### Why did you build this? 

Meraki allows you to specify a URL to send webhooks to - but unfortunately the data sent doesn't match up with what Discord requires for an incoming webhook.

So I needed to write an intermediary that would take in the alert webhooks from Meraki, then format them to include the required parameters expected by Discord. 

Since receiving a webhook requires a public-facing URL, I opted to use ngrok to generate ephemeral URLs & not have to permanantly host anything. This script will auto-update the Meraki Dashboard config with the current ngrok URL every time it starts.

I may add support for additional destinations later on, like Slack or WebEx. 

Also - I've been looking for a reason to play with fastapi, so here it is!  


### Initial instructions:
 1. Install `pip install -r requirements.txt`
 2. Set environment variables (see below)
 3. Run `uvicorn meraki-discord-bot:app`

 Or use the container version, link above!

 ### Environment Variables / Config

 Please note the values below may change

 | Variable Name 	| Required 	| Description 	| Example 	|
|-	|-	|-	|-	|
| MERAKI_TARGET_NETWORK_NAME 	| Yes 	| Name of the Meraki network to attach an alert webhook. 	| Home Office 	|
| MERAKI_API_KEY 	| Yes 	| API key to Meraki Dashboard, used to create/modify alerting webhook configuration 	| 1dc01da6a2e1asdfio434aaasdfasdf 	|
| DISCORD_URL	| Yes 	| Discord webhook URL 	| https://discord.com/api/webhooks/bot_id/token 	|
| NGROK_TOKEN | No | Authentication token for ngrok. If USE_NGROK is True, this will be used to build an authenticated ngrok tunnel. If no authentication token is provided, this script will use the free/unauthenticated ngrok tunnels - which will timout after some time & stop functioning | asdfDAsdfnjiwnri435oA | 
| MERAKI_WEBHOOK_NAME 	| No 	| Name to use when creating the webhook in Meraki. This is used to track which webhook is owned by this bot. By default, will use "api-generated_Discord" 	| api-generated_Discord 	|
| USE_NGROK | No | By default, this will spin up an ngrok tunnel to receive webhook POSTs. If you would rather provide a dedicated external URL, set this to False & provide a webhook URL| True |
| MERAKI_TARGET_WEBHOOK_URL 	| No 	| URL for Meraki to send POST requests to. This is the externally facing URL of this bot.  Note: if USE_NGROK is False, this **must** be set. *MUST be https* 	| https://merakibot.local 	|

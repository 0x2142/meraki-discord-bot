# meraki-discord-bot

Readme in progress, some info below - but not yet completed! 

### Initial instructions:
 1. Install `pip install -r requirements.txt`
 2. Set environment variables (see below)
 3. Run `uvicorn meraki-discord-bot:app --reload`

 ### Environment Variables / Config

 Please note the values below may change

 | Variable Name 	| Required 	| Description 	| Example 	|
|-	|-	|-	|-	|
| MERAKI_TARGET_NETWORK_NAME 	| Yes 	| Name of the Meraki network to attach an alert webhook. 	| Home Office 	|
| MERAKI_TARGET_WEBHOOK_URL 	| No 	| URL for Meraki to send POST requests to. This is the externally facing URL of this bot.  Note: Right now this is overwritten by the ngrok auto-config - will be usable later. *MUST be https* 	| https://merakibot.local 	|
| MERAKI_API_KEY 	| Yes 	| API key to Meraki Dashboard, used to create/modify alerting webhook configuration 	| 1dc01da6a2e1asdfih4852e5d190asfnai4i533o434aaasdfasdf 	|
| MERAKI_WEBHOOK_NAME 	| No 	| Name to use when creating the webhook in Meraki. This is used to track which webhook is owned by this bot. By default, will use "api-generated_Discord" 	| api-generated_Discord 	|
| DISCORD_WEBHOOK_ID 	| Yes 	| Webhook ID generated by Discord to post messages 	| 0174891758902347510345 	|
| DISCORD_WEBHOOK_TOKEN 	| Yes 	| Webhook token generated by Discord to post messages 	| SADFJASDFN#$I#$M$#TOefosdfaJ(#KAFJSDFSADF 	|

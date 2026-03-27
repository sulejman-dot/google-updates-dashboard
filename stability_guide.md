# Slack Bot Stability Guide

To prevent "dispatch_failed" errors, the Flask server and ngrok tunnel must be running continuously.

## Option 1: Quick Background Run (nohup)
If you just want to run them in the background on your current machine:

```bash
# Start Flask
nohup python3 slack_bot_server.py > flask.log 2>&1 &

# Start ngrok
nohup ngrok http 3000 --log=stdout > ngrok.log 2>&1 &
```

## Option 2: Process Manager (PM2) - Recommended
For a production-like setup that auto-restarts if it crashes:

1. **Install PM2:**
   ```bash
   npm install -g pm2
   ```

2. **Start the bot:**
   ```bash
   pm2 start slack_bot_server.py --interpreter python3 --name "slack-bot"
   ```

3. **Monitor:**
   ```bash
   pm2 status
   pm2 logs slack-bot
   ```

## Option 3: Static ngrok Domain
The "dispatch_failed" errors often happen because the ngrok URL changes on every restart. To avoid updating Slack settings every time, you can use a static domain (requires a free ngrok account):

1. Claim your free domain at [dashboard.ngrok.com](https://dashboard.ngrok.com/cloud-edge/domains).
2. Start ngrok with the domain:
   ```bash
   ngrok http --url=prevertebral-preadequately-lezlie.ngrok-free.dev 3000
   ```

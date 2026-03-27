# ClickUp Comment Monitor Setup

## ✅ What's Been Done

1. **LaunchAgent Created**: `com.clickup.comment.monitor.plist`
   - Configured to run every 10 minutes
   - Logs to: `clickup_monitor.log` and `clickup_monitor_error.log`
   - Currently loaded and active

2. **Workflow Documentation**: `.agent/workflows/clickup-comments.md`
   - Documents the monitoring process
   - Can be referenced via `/clickup-comments` command

3. **Test Alert Successful**: `test_alert.py`
   - Successfully sent a Slack alert for Vlad's comment
   - Proves Slack webhook integration works

## ❌ Current Issue

The `CLICKUP_API_KEY` in the `.env` file is invalid (returns "Token invalid" error).

This prevents the automated monitoring script from authenticating with the ClickUp API.

## ✅ What Works

- **MCP ClickUp Integration**: Can successfully fetch tasks and comments
- **Slack Webhooks**: Can send alerts successfully  
- **LaunchAgent**: Configured and loaded properly

## 🔧 Solutions

### Option 1: Get Valid ClickUp API Key (Recommended)

1. Go to ClickUp Settings → Apps → API Token
2. Generate a new Personal API Token
3. Update `.env` file with new API key:
   ```
   CLICKUP_API_KEY=pk_NEW_TOKEN_HERE
   ```
4. Test with: `python3 clickup_monitor_complete.py`

### Option 2: Manual Monitoring (Temporary)

Run the monitoring script manually when needed:
```bash
cd "/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
python3 test_alert.py  # Test that alerts work
```

## 📝 Files Created

1. `clickup_monitor_complete.py` - Full monitoring script (needs valid API key)
2. `run_clickup_monitor_wrapper.py` - Wrapper called by LaunchAgent
3. `test_alert.py` - Test script that sent successful alert
4. `.agent/workflows/clickup-comments.md` - Workflow documentation
5. `/Users/user/Library/LaunchAgents/com.clickup.comment.monitor.plist` - LaunchAgent config

## 🎯 Next Steps

1. **Get a valid ClickUp API key** from your ClickUp settings
2. **Update the `.env` file** with the new key
3. **Test the monitor**: `python3 clickup_monitor_complete.py`
4. The LaunchAgent will automatically use the updated key on next run (every 10 minutes)

## 📊 Monitoring Features

Once the API key is fixed, the monitor will:
- ✅ Check all your assigned tasks every 10 minutes
- ✅ Find comments posted in the last 24 hours
- ✅ Send Slack alerts for new comments (once per comment)
- ✅ Track seen comments in `clickup_comment_state.json`
- ✅ Log all activity to `clickup_monitor.log`

#!/bin/bash
# Install and configure LaunchAgents for Slack Bot and ngrok auto-start

WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"

echo "🚀 Installing Slack Bot and ngrok LaunchAgents..."
echo "=================================================="

# Create LaunchAgents directory if it doesn't exist
mkdir -p "$LAUNCH_AGENTS_DIR"

# Copy plist files to LaunchAgents directory
echo "📋 Copying plist files..."
cp "$WORKSPACE_DIR/com.slackbot.server.plist" "$LAUNCH_AGENTS_DIR/"
cp "$WORKSPACE_DIR/com.ngrok.tunnel.plist" "$LAUNCH_AGENTS_DIR/"

# Set proper permissions
chmod 644 "$LAUNCH_AGENTS_DIR/com.slackbot.server.plist"
chmod 644 "$LAUNCH_AGENTS_DIR/com.ngrok.tunnel.plist"

# Unload if already loaded (ignore errors)
echo "🔄 Unloading existing agents (if any)..."
launchctl unload "$LAUNCH_AGENTS_DIR/com.slackbot.server.plist" 2>/dev/null || true
launchctl unload "$LAUNCH_AGENTS_DIR/com.ngrok.tunnel.plist" 2>/dev/null || true

# Load the LaunchAgents
echo "✅ Loading LaunchAgents..."
launchctl load "$LAUNCH_AGENTS_DIR/com.slackbot.server.plist"
launchctl load "$LAUNCH_AGENTS_DIR/com.ngrok.tunnel.plist"

echo ""
echo "=================================================="
echo "✅ Installation complete!"
echo ""
echo "Services will now:"
echo "  • Start automatically on boot"
echo "  • Restart automatically if they crash"
echo ""
echo "To check status:"
echo "  launchctl list | grep -E '(slackbot|ngrok)'"
echo ""
echo "To manually stop:"
echo "  launchctl unload ~/Library/LaunchAgents/com.slackbot.server.plist"
echo "  launchctl unload ~/Library/LaunchAgents/com.ngrok.tunnel.plist"
echo ""
echo "To manually start:"
echo "  launchctl load ~/Library/LaunchAgents/com.slackbot.server.plist"
echo "  launchctl load ~/Library/LaunchAgents/com.ngrok.tunnel.plist"
echo "=================================================="

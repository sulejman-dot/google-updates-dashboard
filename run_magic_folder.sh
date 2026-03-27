#!/bin/bash
# Start Magic Folder Watcher in the background

WORKSPACE_DIR="/Users/user/Library/CloudStorage/GoogleDrive-sulejman@seomonitor.com/My Drive/cosmin folder/Sulejman Workspace"

echo "✨ Starting Magic Folder Watcher in the background..."

# Check if watcher is already running
if pgrep -f "invoice_watcher.py" > /dev/null; then
    echo "⚠️  Magic Folder Watcher is already running!"
    exit 0
fi

# Run using nohup so it survives terminal closing
cd "$WORKSPACE_DIR"
nohup python3 invoice_watcher.py > /tmp/invoice_watcher_nohup.log 2>&1 &

echo "✅ Magic Folder is now Active!"
echo "You can drop Chargebee ZIP files into ~/Desktop/Chargebee_Invoices anytime."

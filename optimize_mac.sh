#!/bin/bash

# Mac Optimization Script - 2026-01-19
# Run this to reduce memory pressure and UI stutters.

echo "--- Starting Mac Optimization ---"

# 1. Disable AWDL (Stops WLAN discovery timeouts/stutters)
echo "1. Disabling AWDL (AirPlay/Airdrop/Handoff)..."
# We run it multiple times as some services might try to bring it back up immediately
sudo ifconfig awdl0 down
sleep 1
sudo ifconfig awdl0 down
if [ $? -eq 0 ]; then
    echo "   [✓] AWDL disabled."
    echo "   NOTE: If lags persist, disable 'Handoff' in System Settings -> General -> AirDrop & Handoff."
else
    echo "   [✗] Failed to disable AWDL."
fi

# 2. Purge Inactive Memory
echo "2. Purging inactive memory..."
sudo purge
echo "   [✓] Inactive memory purged."

# 3. Clear Caches
echo "3. Clearing system and user caches (safe)..."
rm -rf ~/Library/Caches/*
sudo rm -rf /Library/Caches/*
echo "   [✓] Caches cleared."

# 4. Recommendation: WindowServer
echo "--- Optimization Complete ---"
echo "TIP: If you still experience freezing, consider restarting the 'WindowServer' process."
echo "     Warning: This will log you out immediately."
echo "     Command: sudo killall -HUP WindowServer"
echo ""
echo "Recommended: Restart your Mac when convenient to fully clear the 8GB RAM swap."

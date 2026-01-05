#!/bin/bash
cd "$(dirname "$0")"

echo "========================================"
echo "  Cafe Menu Scraper - Setup"
echo "========================================"
echo ""
echo "Installing required packages..."
echo ""

pip3 install -r requirements.txt

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "You can now run START-MAC.command to start the tool."
echo ""
read -p "Press Enter to close..."

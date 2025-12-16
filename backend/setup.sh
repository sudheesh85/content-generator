#!/bin/bash
# Setup script to install all dependencies

echo "Installing Python dependencies..."
pip install -r requirements.txt

echo "Creating media directories..."
mkdir -p media/images
mkdir -p media/videos
mkdir -p media/assets

echo "Setup complete!"
echo ""
echo "Make sure to set the following environment variables in .env:"
echo "  - OPENAI_API_KEY"
echo "  - INSTAGRAM_ACCESS_TOKEN (optional)"
echo "  - FACEBOOK_ACCESS_TOKEN (optional)"


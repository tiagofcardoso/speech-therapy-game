#!/bin/bash

echo "Setting up dependencies for 3D Avatar with Lipsync..."

# Create necessary directories
mkdir -p ~/Projects/TutorAI_MCP/speech-therapy-game/frontend/public/models
mkdir -p ~/Projects/TutorAI_MCP/speech-therapy-game/frontend/public/audio/phonemes

# Install system dependencies
sudo dnf install -y cmake gcc-c++ boost-devel sox espeak-ng ffmpeg

# Install Rhubarb Lip Sync
echo "Installing Rhubarb Lip Sync..."
cd /tmp
rm -rf rhubarb-lip-sync
git clone https://github.com/DanielSWolf/rhubarb-lip-sync.git
cd rhubarb-lip-sync
mkdir build && cd build
cmake ..
make -j4
sudo cp rhubarb /usr/local/bin/
echo "Rhubarb Lip Sync installed to /usr/local/bin/rhubarb"

# Install frontend dependencies
echo "Installing frontend dependencies..."
cd ~/Projects/TutorAI_MCP/speech-therapy-game/frontend
npm install three @react-three/fiber @react-three/drei

# Download sample 3D model
echo "Downloading sample 3D model..."
cd ~/Projects/TutorAI_MCP/speech-therapy-game/frontend/public/models
curl -L -o default_avatar.glb https://models.readyplayer.me/64493df7e1abd0ad48965cbf.glb

echo "Setup complete! You may need to restart your development server."
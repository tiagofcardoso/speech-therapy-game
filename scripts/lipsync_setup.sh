#!/bin/bash

# Ensure script is run as root
if [ "$EUID" -ne 0 ]; then
  echo "Please run as root or with sudo"
  exit 1
fi

echo "Setting up dependencies for 3D Avatar with Lipsync..."

# Install system dependencies
dnf install -y cmake gcc-c++ boost-devel sox espeak-ng

# Install Rhubarb Lip Sync
echo "Installing Rhubarb Lip Sync..."
cd /tmp
rm -rf rhubarb-lip-sync
git clone https://github.com/DanielSWolf/rhubarb-lip-sync.git
cd rhubarb-lip-sync
mkdir build && cd build
cmake ..
make
cp rhubarb /usr/local/bin/
echo "Rhubarb Lip Sync installed to /usr/local/bin/rhubarb"

# Python dependencies
echo "Installing Python dependencies..."
pip install pyttsx3 librosa soundfile

# Frontend dependencies
echo "Installing frontend dependencies..."
cd /home/tiagocardoso/Projects/TutorAI_MCP/speech-therapy-game/frontend
npm install three @react-three/fiber @react-three/drei

echo "Setup complete! You may need to restart your development server."
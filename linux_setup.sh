#!/bin/bash
sudo apt update
sudo apt install python3-venv python3-pip tmux python3-opencv libatlas-base-dev libopenjp2-7 libavcodec-dev -y
sudo apt upgrade
chmod +x on_startup.sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
echo "[!!!] VERY IMPORTANT: If runnning on a raspberry pi, you need to enable legacy camera mode in `sudo raspi-config`."

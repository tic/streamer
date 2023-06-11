#!/bin/bash
sudo apt install python3-venv python3-pip tmux -y
chmod +x on_startup.sh
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

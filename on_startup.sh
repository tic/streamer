#!/bin/bash

# If desired, this script can be set to run on startup for a machine
# to launch the streamer automatically when the machine turns on.

# Autonomous activation requires a valid tmux installation and will
# attach the instance to a tmux session called "streamer".

# This script assumes the project is located in the "~/streamer" folder!

# Make sure the start script is executable
chmod +x run.sh

# A simple startup instruction
# tmux new-session -d -s streamer 'cd ~/streamer && ./run.sh'

# A more robust aproach that supports virtual environments
tmux new-session -s cam -d
tmux send-keys -t "cam:0" "/bin/bash" Enter
tmux send-keys -t "cam:0" "cd /home/pi/streamer" Enter
tmux send-keys -t "cam:0" "source venv/bin/activate" Enter
tmux send-keys -t "cam:0" "sudo ./run.sh" Enter

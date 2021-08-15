#!/bin/bash

# If desired, this script can be set to run on startup for a machine
# to launch the streamer automatically when the machine turns on.

# Autonomous activation requires a valid tmux installation and will
# attach the instance to a tmux session called "streamer".

# This script assumes the project is located in the "~/streamer" folder!

tmux new-session -d -s streamer 'cd ~/streamer && ./run.sh'

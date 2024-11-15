#!/bin/bash
set -e

# Update and install dependencies
sudo apt-get update
sudo apt-get install -y cmake wget build-essential libgl1-mesa-dev libxmu-dev

# Clone PARSEC 3.0 from GitHub
if [ ! -d "/home/gem5/parsec-benchmark" ]; then
    git clone https://github.com/bamos/parsec-benchmark  /home/gem5/parsec-benchmark
fi

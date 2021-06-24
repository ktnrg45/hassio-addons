#!/usr/bin/with-contenv bashio

echo "AWS Route 53 Dynamic DNS"
CONFIG_PATH=/data/options.json

echo "Starting..."
python3 run.py $CONFIG_PATH
echo "Stopping..."
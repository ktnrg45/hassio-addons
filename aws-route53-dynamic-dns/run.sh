#!/usr/bin/with-contenv bashio

echo "AWS Route 53 Dynamic DNS"
CONFIG_PATH=/data/options.json
AWS_ACCESS_KEY_ID=$(jq --raw-output ".aws_access_key_id" $CONFIG_PATH)
AWS_SECRET_ACCESS_KEY=$(jq --raw-output ".aws_secret_access_key" $CONFIG_PATH)
ZONE_ID=$(jq --raw-output ".zone_id" $CONFIG_PATH)
DOMAIN_URLS=$(jq --raw-output '.domain_urls | join(",")' $CONFIG_PATH)
INTERVAL=$(jq --raw-output ".interval" $CONFIG_PATH)
LOG_LEVEL=$(jq --raw-output ".log_level" $CONFIG_PATH)

echo "Starting..."
python3 run.py $AWS_ACCESS_KEY_ID $AWS_SECRET_ACCESS_KEY $ZONE_ID $DOMAIN_URLS \
	--interval $INTERVAL --log-level $LOG_LEVEL
echo "Stopping..."
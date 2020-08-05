import socket
import logging
from datetime import datetime
import time
import sys
import argparse

import requests
import boto3 as aws
from botocore import errorfactory

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S',
)
_LOGGER = logging.getLogger(__name__)

CHECK_IP_URL = "https://checkip.amazonaws.com"


def change_record(data, new_ip_address, current_ip_address):
    """Update A record with new IP Address."""
    _LOGGER.info("Updating DNS Record")

    try:
        client = aws.client(
            'route53',
            aws_access_key_id=data['id'],
            aws_secret_access_key=data['key'],
        )

        response = client.list_resource_record_sets(HostedZoneId=data['zone_id'])
        _LOGGER.debug(response)
        list_status_code = response['ResponseMetadata']['HTTPStatusCode']
        if list_status_code != 200:
            _LOGGER.error("HTTP request failed: %s", list_status_code)
            return False

    except errorfactory.NoSuchHostedZone:
        _LOGGER.error("Hosted Zone not found: %s", data['zone_id'])
        return False

    _LOGGER.info("Client connected to AWS")
    record_sets = response["ResourceRecordSets"]
    for record_set in record_sets:
        if record_set['Name'] == data['domain_url'] and record_set['Type'] == "A":
            a_record = record_set
            break
    if a_record is None:
        _LOGGER.error("Matching record not found in records set")
        _LOGGER.info(record_set)
        return False
    resource_records = a_record['ResourceRecords']
    resource_values = [resource['Value'] for resource in resource_records]

    if current_ip_address not in resource_values:
        _LOGGER.error("Record Value Mismatch")
        return False

    _LOGGER.info("Current A Record Values: %s", str(resource_values))

    new_record_set = {
        'Name': data['domain_url'],
        'Type': 'A',
        'TTL': record_set['TTL'],
        'ResourceRecords': [
            {
                'Value': new_ip_address,
            },
        ],
    }
    change_batch = {
        'Changes': [
            {
                'Action': 'UPSERT',
                'ResourceRecordSet': new_record_set,
            },
        ]
    }

    change_response = client.change_resource_record_sets(
        HostedZoneId=data['zone_id'],
        ChangeBatch=change_batch
    )
    change_data = change_response['ResponseMetadata']
    status_code = change_data['HTTPStatusCode']
    _LOGGER.debug("Response %s: %s", status_code, change_data)
    if status_code != 200:
        _LOGGER.error("HTTP Error")
    _LOGGER.info(
        "Changed %s record: Name=%s, Values=%s",
        a_record['Type'],
        new_record_set['Name'],
        str(new_record_set["ResourceRecords"]))

    _LOGGER.info("Waiting on Status Update...")
    waiter = client.get_waiter('resource_record_sets_changed')
    failed = waiter.wait(Id=change_response['ChangeInfo']['Id'])
    if failed is not None:
        _LOGGER.error("Error: %s", failed)
        return False
    return True


def check_external_ip(current_ip_address):
    """Checks if external IP has changed."""
    ip_address = requests.get(CHECK_IP_URL).text.strip()
    _LOGGER.debug("IP Address=%s; A Record=%s", ip_address, current_ip_address)
    if ip_address != current_ip_address:
        _LOGGER.info("External IP Address has changed to: %s", ip_address)
        return ip_address
    return None


def start(data: dict):
    """Start process."""
    _LOGGER.info("Checking DNS Record in %s second intervals", data['interval'])

    while True:
        _LOGGER.debug("Validating DNS Record")
        current_ip_address = socket.gethostbyname(data['domain_url'])
        new_ip_address = check_external_ip(current_ip_address)
        if new_ip_address is not None:
            success = change_record(data, new_ip_address, current_ip_address)
            if success:
                _LOGGER.info("Record Update Successful")
            else:
                _LOGGER.error("Record Update Failed. Exiting...")
                sys.exit()
        else:
            _LOGGER.debug("DNS Record is up-to-date")
        time.sleep(data['interval'])


parser = argparse.ArgumentParser(description='Dynamically update Route 53 DNS Record')
parser.add_argument('id', type=str, help='AWS ID')
parser.add_argument('key', type=str, help='AWS Key')
parser.add_argument('zone_id', type=str, help='AWS Route 53 Zone ID')
parser.add_argument('domain_url', type=str, help='Domain URL')
parser.add_argument('--interval', type=int, default=180, help='Interval in seconds to run checks')
parser.add_argument('--log-level', type=str, default='info', help='Log level to use')

args = parser.parse_args()

data = {
    'id': args.id,
    'key': args.key,
    'zone_id': args.zone_id,
    'domain_url': args.domain_url,
    'interval': args.interval,
}

log_level = args.log_level.lower()
if log_level in LOG_LEVELS:
    _LOGGER.setLevel(LOG_LEVELS[log_level])

start(data)

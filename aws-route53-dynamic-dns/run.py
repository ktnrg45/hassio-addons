import argparse
import json
import logging
import socket
import sys
import time
from datetime import datetime

import boto3 as aws
import requests
from botocore import errorfactory

LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL,
}

CHECK_IP_URL = "https://checkip.amazonaws.com"


def check_zone(client, zone_id: str, domain_url: str) -> list:
    """Return A-Record if domain is in zone."""
    try:
        response = client.list_resource_record_sets(HostedZoneId=zone_id)
        _LOGGER.debug(response)
        list_status_code = response['ResponseMetadata']['HTTPStatusCode']
        if list_status_code != 200:
            _LOGGER.error("HTTP request failed: %s", list_status_code)
            return None
    except errorfactory.NoSuchHostedZone:
        _LOGGER.error("Hosted Zone not found: %s", zone_id)
        return None

    record_sets = response["ResourceRecordSets"]
    a_record = None
    domain_url = [domain_url, "{}.".format(domain_url)]
    for record_set in record_sets:
        if record_set['Name'] in domain_url and record_set['Type'] == "A":
            a_record = record_set
            break
    if a_record is None:
        _LOGGER.info("Matching record not found in records set for zone")
        _LOGGER.debug(record_set)
        return None

    return a_record



def change_record(data: dict, new_ip_address: str, current_ip_address: str):
    """Update A-Record with new IP Address."""
    _LOGGER.info("Updating DNS Record for: %s", data["domain_url"])
    client = aws.client(
        'route53',
        aws_access_key_id=data['aws_access_key_id'],
        aws_secret_access_key=data['aws_secret_access_key'],
    )
    _LOGGER.info("Client connected to AWS")

    for zone in data["zone_ids"]:
        a_record = check_zone(client, zone, data["domain_url"])
        if a_record:
            break

    if not a_record:
        _LOGGER.error("Could not find Domain: %s in any Zone", data["domain_url"])
        return (False,)

    resource_records = a_record['ResourceRecords']
    resource_values = [resource['Value'] for resource in resource_records]
    _LOGGER.info("Current A-Record Values: %s", str(resource_values))

    if current_ip_address not in resource_values:
        _LOGGER.error("Record Value Mismatch")
        return (False,)

    new_record_set = {
        'Name': data['domain_url'],
        'Type': 'A',
        'TTL': a_record['TTL'],
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
        HostedZoneId=zone,
        ChangeBatch=change_batch
    )
    change_data = change_response['ResponseMetadata']
    status_code = change_data['HTTPStatusCode']
    _LOGGER.debug("Response %s: %s", status_code, change_data)
    if status_code != 200:
        _LOGGER.error("HTTP Error")
        return (False,)

    _LOGGER.info(
        "Changed %s record: Name=%s, Values=%s",
        a_record['Type'],
        new_record_set['Name'],
        str(new_record_set["ResourceRecords"]))

    waiter = client.get_waiter('resource_record_sets_changed')
    change_response_id = change_response['ChangeInfo']['Id']
    return (True, data['domain_url'], waiter, change_response_id)


def check_external_ip(current_ip_address: str):
    """Checks if external IP has changed."""
    ip_address = requests.get(CHECK_IP_URL).text.strip()
    _LOGGER.debug("IP Address=%s; A-Record=%s", ip_address, current_ip_address)
    if ip_address != current_ip_address:
        _LOGGER.info("External IP Address has changed to: %s", ip_address)
        return ip_address
    return None


def validate_record(data: dict):
    """Validate and Update DNS record."""
    _LOGGER.debug("Validating DNS Record for %s", data['domain_url'])
    new_ip_address = None
    try:
        current_ip_address = socket.gethostbyname(data['domain_url'])
    except socket.gaierror as e:
        _LOGGER.error("Error resolving hostname: %s", e)
    else:
        new_ip_address = check_external_ip(current_ip_address)
    if new_ip_address is not None:
        return change_record(data, new_ip_address, current_ip_address)
    _LOGGER.debug("DNS Record is up-to-date")
    return (True,)


def wait_for_results(results: list):
    """Wait for results."""
    for result in results:
        domain = result[1]
        waiter = result[2]
        change_response_id = result[3]
        _LOGGER.info("Waiting on Status Update for: %s ...", domain)
        failed = waiter.wait(Id=change_response_id)
        if failed is not None:
            _LOGGER.error("Error: %s", failed)
            _LOGGER.error("Record Update Failed for: %s", domain)
        else:
            _LOGGER.info("Record Update Successful for: %s", domain)


def start(data: dict):
    """Start process."""
    _LOGGER.info("Checking DNS Records in %s second intervals", data['interval'])
    accounts = data["accounts"]
    results = []
    while True:
        for account in accounts:
            for domain_url in account['domain_urls']:
                account['domain_url'] = domain_url
                result = validate_record(account)
                if result[0] and len(result) == 4:
                    results.append(result)
        wait_for_results(results)
        time.sleep(data['interval'])


parser = argparse.ArgumentParser(description='Dynamically update Route 53 DNS Record')
parser.add_argument('options_path', type=str, help='Path to options.json')
args = parser.parse_args()
options_path = args.options_path
with open(options_path, "r") as f:
    data = json.load(f)

log_level = data['log_level'].lower()
if log_level not in LOG_LEVELS:
    log_level = 'info'
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=LOG_LEVELS[log_level],
    datefmt='%Y-%m-%d %H:%M:%S',
)
_LOGGER = logging.getLogger(__name__)
_LOGGER.info("Using log level: %s", log_level)
start(data)

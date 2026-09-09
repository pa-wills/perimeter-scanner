import boto3
import datetime
import json
import nmap
import os
import re

# This is the nmap worker function. It 1. pops a message from the queue it's paired with, 2. attempts to nmap the host referred to within,
# 3. parses the results, 4. Writes the results out to the required tables

# A queue message is a single hostname or IPv4 address. Validate it before handing
# it to nmap: python-nmap appends the value to the nmap argv split on whitespace,
# so an unconstrained string could inject extra nmap options.
_HOST_RE = re.compile(r"^(?!-)[A-Za-z0-9.-]{1,253}(?<![-.])$")


def _isValidHost(value):
    return bool(_HOST_RE.fullmatch(value)) and ".." not in value


def handler(event, context):

    outputDerivedHostsTableName = os.environ.get("HOSTS_OF_INTEREST_TABLE")
    outputHostPortsTableName = os.environ.get("HOST_PORTS_TABLE")
    workQueueName = os.environ.get("WORK_QUEUE")

    dynamodb = boto3.resource('dynamodb')
    hostsOfInterestTable = dynamodb.Table(outputDerivedHostsTableName)
    hostPortsTable = dynamodb.Table(outputHostPortsTableName)
    sqs = boto3.client('sqs')

    # If queue depth == 0, disable the trigger - no point running until it refills.
    if (sqs.get_queue_attributes(
        QueueUrl = workQueueName,
        AttributeNames = ["ApproximateNumberOfMessages"])["Attributes"]["ApproximateNumberOfMessages"] == "0"
    ):

        # TODO: I really want to refer to an EnvVar. Parsing the message in this way is kludgey.
        matches = re.search(r'/(.*)$', str(event["resources"][0]))
        events = boto3.client("events")
        response = events.disable_rule(Name = str(matches.group(1)))

        return {
            'statusCode': 200,
            'body': json.dumps('Work queue was zero-depth. Exiting')
        }

    # Pop from queue, obtain hostname.
    response = sqs.receive_message(QueueUrl = workQueueName, MaxNumberOfMessages = 1)
    if not response.get("Messages"):
        return {
            'statusCode': 200,
            'body': json.dumps('No message received (queue drained since the depth check). Exiting')
        }
    message = response['Messages'][0]
    receiptHandle = message['ReceiptHandle']
    host = message["Body"].strip()

    if not _isValidHost(host):
        # Drop it so it doesn't churn into the DLQ; leave the derived table alone.
        sqs.delete_message(QueueUrl = workQueueName, ReceiptHandle = receiptHandle)
        return {
            'statusCode': 200,
            'body': json.dumps('Rejected invalid host: ' + repr(host))
        }

    nm = nmap.PortScanner()
    nmapResults = nm.scan(host, '22-443')
    nmapResultsCsv = nm.csv()

    # Write required results out to the HostPorts table.
    for csvItem in nmapResultsCsv.splitlines():
        words = csvItem.split(";")
        if (words[0] == "host"): continue
        if len(words) < 13: continue
        datetimeString = datetime.datetime.now(datetime.timezone.utc).isoformat()
        response = hostPortsTable.put_item(
            Item = {
                'composite_HostIpUdpTcp': (words[1] + words[0] + words[3] + words[4]),
                'datetime': datetimeString,
                'host': words[0],
                'hostname': words[1],
                'hostname_type': words[2],
                'protocol': words[3],
                'port': words[4],
                'name': words[5],
                'state': words[6],
                'product': words[7],
                'extrainfo': words[8],
                'reason': words[9],
                'version': words[10],
                'conf': words[11],
                'cpe': words[12]
            }
        )

    # Write the current datetime back to the HostsOfInterest table.
    datetimeString = datetime.datetime.now(datetime.timezone.utc).isoformat()
    hostsOfInterestTable.update_item(
        Key = {
          "host": host
        },
        UpdateExpression = "set DatetimeLastNmaped = :r",
        ExpressionAttributeValues = {
          ":r": datetimeString
        }
      )

    response = sqs.delete_message(QueueUrl = workQueueName, ReceiptHandle = receiptHandle)

    return {
        'statusCode': 200,
        'message': message,
        'nmapOutputs': nmapResults
    }

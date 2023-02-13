import boto3
import datetime
import json
import nmap
import os

# This is the nmap worker function. It 1. pops a message from the queue it's paired with, 2. attempts to nmap the host referred to within,
# 3. parses the results, 4. Writes the results out to the required tables

def handler(event, context):

    outputDerivedHostsTableName = os.environ.get("HOSTS_OF_INTEREST_TABLE")
    outputHostPortsTableName = os.environ.get("HOST_PORTS_TABLE")
    workQueueName = os.environ.get("WORK_QUEUE")

    dynamodb = boto3.resource('dynamodb', region_name="ap-southeast-2")
    hostsOfInterestTable = dynamodb.Table(outputDerivedHostsTableName)
    hostPortsTable = dynamodb.Table(outputHostPortsTableName)
    sqs = boto3.client('sqs')

    # If queue depth == 0, continue.
    if (sqs.get_queue_attributes(
        QueueUrl = workQueueName,
        AttributeNames = ["ApproximateNumberOfMessages"])["Attributes"]["ApproximateNumberOfMessages"] == "0"
    ):
        # TODO: Maybe it should also disable the trigger for this function.
        return {
            'statusCode': 200,
            'body': json.dumps('Work queue was zero-depth. Exiting')
        }

    # TODO: Pop from queue, obtain hostname.
    response = sqs.receive_message(QueueUrl = workQueueName, MaxNumberOfMessages = 1)
    message = response['Messages'][0]
    receiptHandle = message['ReceiptHandle']
 
#    print("nmap - starting")
    nm = nmap.PortScanner()
    nmapResults = nm.scan(message["Body"], '22-443')
    nmapResultsCsv = nm.csv()
#    print("nmap - completed")
#    print("message results: " + str(message))
#    print("nmap results: " + str(nmapResults))
#    print("nmap results csv: " + str(nmapResultsCsv))

    # TODO: Write required results out to the HostPorts table.
    for csvItem in nmapResultsCsv.splitlines():
        words = csvItem.split(";")
        if (words[0] == "host"): continue
        datetimeString = str(datetime.datetime.now().isoformat())
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

    # TODO: Write the current datetime back to the HostsOfInterest table.
    datetimeString = str(datetime.datetime.now().isoformat())
    hostsOfInterestTable.update_item(
        Key = {
          "host": str(message["Body"])
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

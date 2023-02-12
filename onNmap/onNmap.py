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
    hostPortsTable = dynamodb.Table(outputDerivedHostsTableName)
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
 
    print("nmap - starting")
    nm = nmap.PortScanner()
    nmapResultsJson = nm.scan(message["Body"], '22-443')
    print("nmap - completed")
    print("message results: " + str(message))
    print("nmap results json: " + str(nmapResultsJson))

    # TODO: Write required results out to the HostPorts table.
    nmapResults = json.JSONDecoder().decode(nmapResultsJson)
    print("nmap results: " + str(nmapResults))


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
        'nmapOutputs': nmapResults,
        'body': json.dumps('Hello from nmap, mofos!')
    }

import boto3
import json
import nmap

def handler(event, context):

    # TODO: establish contexts to the worked queue and output table.
    outputTableName = os.environ.get("RESULTS_TABLE")
    dynamodb = boto3.resource('dynamodb', region_name="ap-southeast-2")
    table = dynamodb.Table(tableName)
    workQueueName = os.environ.get("WORK_QUEUE")
    sqs = boto3.client('sqs')

    # TODO: If queue depth == 0, exit()
    if (client.get_queue_attributes(
        QueueUrl = workQueueName, 
        AttributeNames = ["ApproximateNumberOfMessages"])["Attributes"]["ApproximateNumberOfMessages"] == 0
    ):
        # TODO: Maybe it should also disable the trigger for this function.
        return {
            'statusCode': 200,
            'body': json.dumps('Work queue was zero-depth. Exiting')
        }

    # TODO: Pop from queue, obtain hostname.
    response = client.receive_message(QueueUrl = workQueueName, MaxNumberOfMessages = 1)
    message = response['Messages'][0]
    receiptHandle = message['ReceiptHandle']

 
#    nm = nmap.PortScanner()
#    stuff = nm.scan('peterwills.com', '22-443')

    # TODO: Nmap said host.
    # TODO: Write required messages to table.

    # TODO: Delete message from queue.
    response = client.delete_message(QueueUrl = workQueueName, ReceiptHandle = receiptHandle)

    return {
        'statusCode': 200,
        'stuff': stuff,
        'body': json.dumps('Hello from nmap, mofos!')
    }

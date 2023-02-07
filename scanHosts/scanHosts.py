import json
import nmap

def handler(event, context):
    nm = nmap.PortScanner()
    stuff = nm.scan('peterwills.com', '22-443')

    # TODO implement
    return {
        'statusCode': 200,
        'stuff': stuff,
        'body': json.dumps('Hello from Peter Wills, mofos!')
    }

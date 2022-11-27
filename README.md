# perimeter-scanner
A schedulable OSINT scanner using [recon-ng](https://github.com/lanmaster53/recon-ng) which allows for the analysis of an attack surface over time.

## Background
This project comes from a desire to learn how to build applications on AWS, and a practical need to under the attack surface of an organisation as a function of time. This initial, very basic release does domain enumeration periodically with effectively indefinite persistence of results. This will hopefully serves as a helpful baseline for dcata analysis.

## Overall Architecture and CICD
AWS helpfully [explains](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.pdf?did=wp_card&trk=wp_card) how we should segment large Organisations into multiple Accounts, and I have used a similar architecture for this project. Specifically:

* I have production and non-production workloads in their own accounts.
* The CICD pipeline and associated components are also has its own acccount.
* The DNS infrastructure, given its shared nature, also has its own account.

The pipeline itself comprises a source stage in Github, a build step followed by a deployment to a non-production (I refer to it herein as *devtest*) environment, and finally: deployment to production. 

## The App
* Fundamentally: recon-ng with a custom workflow run from the shell of a EC2 Instance created for the task. I could not figure out how to make recon-ng serverless, and so I've done what I hope is the next best thing:

* An EC2 Instance which is configured to launch, install recon-ng, clone this rpo, set up cron, set up some environment variables, then stop.
* A scheduled eventbridge task that invokes a Lambda, which itself boots the previously launched EC2 Instance. This act causes the enumeration script to run, resulting in a CSV file which is copied to S3 and then deleted locally. That EC2 Instance is then stopped (because I am cheap).
* S3 event notifications then cause another Lambda to invoke, which parses the file, loads contents into a Dynamo DB table, then deletes the CSV file.

## Instructions
1. Deploy the *[crossAccountRoles](crossAccountRoles.yaml)* stack to the Accounts you intend to use for production and devtest.
2. Deploy the *[pipeline](pipeline.yaml)* stack to the Account you intend to use for CICD.
3. The CodePipeline object will run automatically once the *pipeline* stack reaches CREATE_COMPLETE. This will result in a built application.


## Assumptions / Parameters
OK, so despite my best efforts the application is not perfectly self-contained. I.e. there are some items that need to be set up prior to deploying the pipeline stack.

* The Pipeline's source stage connects to Github through a Codestar Connection. This needs to instantiated, and its ARN given as a parameter.
* Since this repo is currently *private*, it cannot be accessed without authentication. Loathe as I am to store secrets in repos of any kind - I have placed the require [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) into the Systems Manager Paramater Store.



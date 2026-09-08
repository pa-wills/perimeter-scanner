# perimeter-scanner
A schedulable OSINT scanner using [recon-ng](https://github.com/lanmaster53/recon-ng) which allows for the analysis of an attack surface over time.

## Background
This project comes from a desire to learn how to build applications on AWS, and a practical need to understand the attack surface of an organisation as a function of time. This initial, very basic release does domain enumeration periodically with effectively indefinite persistence of results. This will hopefully serves as a helpful baseline for dcata analysis.

## Overall Architecture and CICD
AWS helpfully [explains](https://docs.aws.amazon.com/whitepapers/latest/organizing-your-aws-environment/organizing-your-aws-environment.pdf?did=wp_card&trk=wp_card) how we should segment large Organisations into multiple Accounts, and I have used a similar architecture for this project. Specifically:

* I have production and non-production workloads in their own accounts; and
* The CICD pipeline and associated components are also has its own acccount.

The pipeline itself comprises a source stage in Github, a build step followed by a deployment to a non-production (I refer to it herein as *devtest*) environment, and finally: deployment to production. 

## The App
Fundamentally: recon-ng with a custom workflow run from the shell of a EC2 Instance created for the task. I could not figure out how to make recon-ng serverless, and so I've done what I hope is the next best thing:

* An EC2 Instance which is configured to launch, install recon-ng, clone this rpo, set up cron, set up some environment variables, then stop.
* A scheduled eventbridge task that invokes a Lambda, which itself starts the previously launched EC2 Instance. This act causes the enumeration script to run, resulting in a CSV file which is copied to S3 and then deleted locally. That EC2 Instance is then stopped (because I am cheap / frugal).
* S3 event notifications then cause another Lambda to invoke, which parses the file, loads contents into a DynamoDB table, then deletes the CSV file.
* A secondary DynamoDB table that summarises when hosts were first detected and most recently detected.

## Instructions

### 1. Cross-account deployment roles

*[crossAccountRoles.yaml](crossAccountRoles.yaml)* defines the roles the CICD account's
pipeline assumes to deploy into the devtest and prod accounts:

* `perimeter-scanner-cross-account-role-<env>` — assumed by the CICD pipeline to run the
  CloudFormation deploy action (least-privilege managed policy `perimeter-scanner-cicd-deploy-policy`).
* `perimeter-scanner-cf-execution-role-<env>` — the CloudFormation service role that
  actually creates the app's resources.

It is deployed **once**, as a *service-managed* CloudFormation StackSet, from the CICD
account acting as a StackSets **delegated administrator**, auto-deploying to the
Organizational Units that contain the devtest and prod accounts. (This is not deployed by
the pipeline — it is a prerequisite of it.)

```bash
CICD_ACCOUNT_ID=623056247312
DEVTEST_OU_ID=ou-8me6-lphnkp1y   # OU containing the devtest workload account
PROD_OU_ID=ou-8me6-u6ss8udg      # OU containing the prod workload account
REGION=ap-southeast-2

aws cloudformation create-stack-set \
  --stack-set-name perimeter-scanner-cross-account-roles \
  --template-body file://crossAccountRoles.yaml \
  --permission-model SERVICE_MANAGED \
  --auto-deployment Enabled=true,RetainStacksOnAccountRemoval=false \
  --capabilities CAPABILITY_NAMED_IAM \
  --parameters ParameterKey=CiCdAccountId,ParameterValue=$CICD_ACCOUNT_ID \
  --call-as DELEGATED_ADMIN --region $REGION

# devtest instance (Environment defaults to devtest)
aws cloudformation create-stack-instances \
  --stack-set-name perimeter-scanner-cross-account-roles \
  --deployment-targets OrganizationalUnitIds=$DEVTEST_OU_ID \
  --regions $REGION --call-as DELEGATED_ADMIN

# prod instance (override Environment=prod)
aws cloudformation create-stack-instances \
  --stack-set-name perimeter-scanner-cross-account-roles \
  --deployment-targets OrganizationalUnitIds=$PROD_OU_ID \
  --parameter-overrides ParameterKey=Environment,ParameterValue=prod \
  --regions $REGION --call-as DELEGATED_ADMIN
```

Subsequent changes: `aws cloudformation update-stack-set --stack-set-name
perimeter-scanner-cross-account-roles --template-body file://crossAccountRoles.yaml
--capabilities CAPABILITY_NAMED_IAM --call-as DELEGATED_ADMIN --region $REGION`
(the prod instance keeps its `Environment=prod` override).

### 2. Pipeline

Deploy the *[pipeline.yaml](pipeline.yaml)* stack to the CICD account. Its
`DevTest*`/`Production*` role-ARN parameters default to the roles created in step 1.

### 3. Build

The CodePipeline runs automatically on a push to its source branch, producing a built and
deployed application.


## Assumptions / Parameters
OK, so despite my best efforts the application is not perfectly self-contained. I.e. there are some items that need to be set up prior to deploying the pipeline stack.

* The Pipeline's source stage connects to Github through a Codestar Connection. This needs to instantiated, and its ARN given as a parameter.
* Since this repo is currently *private*, it cannot be accessed without authentication. Loathe as I am to store secrets in repos of any kind - I have placed the require [Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) into the Systems Manager Paramater Store.



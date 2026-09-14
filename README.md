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
recon-ng with a custom workflow, packaged as a container image ([reconng/](reconng/)) and
run as a one-shot **ECS Fargate task**:

* An EventBridge Scheduler schedule (`ReconngSchedule`, periodicity per environment) runs
  the Fargate task. The container runs `enumerateSubdomains.bash` — the recon-ng workflow —
  and copies the resulting CSV to S3; the task then exits.
* An S3 event notification invokes `onArrivalOfResults`, which parses the CSV into the
  `ResultsTableHosts` DynamoDB table and deletes the object.
* DynamoDB Streams on `ResultsTableHosts` / `ResultsTableHostPorts` drive functions that
  maintain the derived "of interest" tables (first-seen / last-seen per host and per
  host:port).
* A separate nmap worker (`onNmap`, a container-image Lambda) port-scans discovered hosts
  from an SQS work queue.

(Earlier releases ran the recon-ng workflow from a `@reboot` cron on a scheduled-boot EC2
instance; that was replaced by the Fargate task.)

## Instructions

### 1. Cross-account deployment roles

*[crossAccountRoles.yaml](crossAccountRoles.yaml)* defines the roles the CICD account's
pipeline assumes to deploy into the devtest and prod accounts:

* `perimeter-scanner-cross-account-role-<env>` — assumed by the CICD pipeline to run the
  CloudFormation deploy action (least-privilege managed policy `perimeter-scanner-cicd-deploy-policy`).
* `perimeter-scanner-cf-execution-role-<env>` — the CloudFormation service role that
  actually creates the app's resources.

`crossAccountRoles.yaml` is an **enclosing stack** (`PerimeterScanner-StackSetCrossAccountRoles`):
it defines its own CloudFormation service role (`perimeter-scanner-stackset-cf-execution-role`)
and an `AWS::CloudFormation::StackSet` resource (`perimeter-scanner-cross-account-roles`,
`SERVICE_MANAGED`, `CallAs: DELEGATED_ADMIN`) whose inlined child template + `StackInstancesGroup`
create the roles above in the devtest and prod OUs. Deployed **once**, from the CICD account
acting as a StackSets delegated administrator. Not deployed by the pipeline — it is a
prerequisite of it.

```bash
# First deploy only (the service role does not exist yet): omit --role-arn.
aws cloudformation deploy --stack-name PerimeterScanner-StackSetCrossAccountRoles \
  --template-file crossAccountRoles.yaml --capabilities CAPABILITY_NAMED_IAM \
  --region ap-southeast-2

# Every deploy after that:
aws cloudformation deploy --stack-name PerimeterScanner-StackSetCrossAccountRoles \
  --template-file crossAccountRoles.yaml --capabilities CAPABILITY_NAMED_IAM \
  --role-arn arn:aws:iam::623056247312:role/perimeter-scanner-stackset-cf-execution-role \
  --region ap-southeast-2
```

The OU IDs and pipeline artifact bucket / KMS key ARNs are template parameters with
defaults; override with `--parameter-overrides` if they change. Updating the role
definitions is a single `deploy` of this file — CloudFormation propagates the change to
every target account via the StackSet.

### 2. Pipeline

Deploy the *[pipeline.yaml](pipeline.yaml)* stack (`PerimeterScanner-App`) to the CICD
account. Its `DevTest*`/`Production*` role-ARN parameters default to the roles created in
step 1.

The template defines its own CloudFormation service role, `PipelineCfExecutionRole`
(`perimeter-scanner-pipeline-cf-execution-role`), so the stack runs with a scoped role
rather than the deploying principal (Security Hub CloudFormation.4). The very first deploy
that creates this role must run without `--role-arn` (the role does not exist yet); **every
deploy after that must pass it**:

```bash
aws cloudformation deploy --stack-name PerimeterScanner-App --template-file pipeline.yaml \
  --capabilities CAPABILITY_NAMED_IAM \
  --role-arn arn:aws:iam::<cicd-account>:role/perimeter-scanner-pipeline-cf-execution-role \
  --parameter-overrides ...
```

### 3. Build

The CodePipeline runs automatically on a push to its source branch: it builds the `onNmap`
and `reconng` container images (tagged `<name>-<git sha>` and `<name>-latest`), packages
`template.yaml`, and deploys to devtest then (on manual transition) production.

## Assumptions / Parameters
Some items must be set up before deploying the pipeline stack:

* The pipeline's source stage connects to GitHub through an AWS CodeConnections
  (CodeStar) connection; its ARN is a parameter. This is the only GitHub credential the
  system needs — the recon-ng workflow is baked into the `reconng` image at build time, so
  there is no runtime `git clone` and no Personal Access Token.
* The recon-ng workspace name and the comma-separated list of domains to enumerate are
  parameters, passed through from the pipeline.



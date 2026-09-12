# nmap worker - a container-image Lambda (PackageType: Image).
#
# Inspector (ECR image scanning) reports ~8 findings (5 HIGH) as of 2026-09-12,
# all in this base image's own bundled OS packages (libssh2, openssl-fips-provider)
# and the Go tooling AWS bundles into the Lambda runtime itself (golang.org/x/sys,
# github.com/go-chi/chi) - none in onNmap.py or requirements.txt. Accepted risk:
# nothing in this file installs or controls those components; the only lever is a
# future AWS-published patch to this base image tag, which `--pull` in buildspec.yaml
# ensures the next build will pick up automatically. See #52.
FROM public.ecr.aws/lambda/python:3.13

# Amazon Linux 2023 base: dnf, and a current nmap (the old AL2 base shipped
# nmap 6.40 from 2013). onNmap.py runs a TCP-connect scan, which needs no
# raw-socket capability, so it works unprivileged in Lambda.
RUN dnf install -y nmap && dnf clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY onNmap.py ${LAMBDA_TASK_ROOT}/

CMD [ "onNmap.handler" ]

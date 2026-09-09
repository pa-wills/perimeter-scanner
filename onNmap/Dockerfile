# nmap worker - a container-image Lambda (PackageType: Image).
FROM public.ecr.aws/lambda/python:3.13

# Amazon Linux 2023 base: dnf, and a current nmap (the old AL2 base shipped
# nmap 6.40 from 2013). onNmap.py runs a TCP-connect scan, which needs no
# raw-socket capability, so it works unprivileged in Lambda.
RUN dnf install -y nmap && dnf clean all

COPY requirements.txt ${LAMBDA_TASK_ROOT}/
RUN pip install --no-cache-dir -r ${LAMBDA_TASK_ROOT}/requirements.txt

COPY onNmap.py ${LAMBDA_TASK_ROOT}/

CMD [ "onNmap.handler" ]

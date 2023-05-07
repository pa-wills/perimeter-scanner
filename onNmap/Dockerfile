FROM public.ecr.aws/lambda/python:3.10.2023.05.06.17-x86_64

RUN yum install git -y
RUN pip install python-nmap
RUN yum install nmap -y

# Copy function code
COPY onNmap.py ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler (could also be done as a parameter override outside of the Dockerfile)
CMD [ "onNmap.handler" ] 

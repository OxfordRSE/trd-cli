FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy your local trd_cli script into the container
COPY ./trd_cli /app/trd_cli
COPY ./requirements.txt /app/requirements.txt

# Install Python dependencies
RUN pip install -r /app/requirements.txt

# ENTRYPOINT will pull secrets from AWS Secrets Manager and run the main script
ENTRYPOINT ["python", "/app/trd_cli/main.py"]

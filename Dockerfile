# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Update and upgrade the base image
RUN apt-get update && apt-get upgrade -y && apt-get install -y --no-install-recommends \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory inside the container
WORKDIR /usr/local/domain_manager

# Copy the entire project into the container at /usr/local/domain_manager
COPY . .

# Set the PYTHONPATH environment variable to include /usr/local/domain_manager/src
ENV PYTHONPATH="/usr/local/domain_manager/src"

# Install the required Python packages using setup.py
RUN pip install --upgrade pip
RUN pip install .

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Run the main entry point defined in setup.py
CMD ["domain-manager"]

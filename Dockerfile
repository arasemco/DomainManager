# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the entire project into the container at /usr/src/app
COPY . .

# Set the PYTHONPATH environment variable to include /usr/src/app/src
ENV PYTHONPATH="/usr/src/app/src"

# Install the required Python packages using setup.py
RUN pip install .

# Set environment variables
ENV PYTHONUNBUFFERED 1

# Run the main entry point defined in setup.py
CMD ["domain-manager"]

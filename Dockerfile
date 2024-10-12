# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Install the Docker SDK for Python and OVH library
RUN pip install ovh docker pandas

# Set the working directory inside the container
WORKDIR /usr/src/app

# Copy the current directory contents into the container at /usr/src/app
COPY app/main.py .

# Make sure the Python script is executable
RUN chmod +x main.py

# Run the Python script
CMD ["python", "/usr/src/app/main.py"]

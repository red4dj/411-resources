# Use the official Ubuntu 22.04 LTS as the base image
FROM ubuntu:22.04

# Set the working directory inside the container
WORKDIR /app

# Update and install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip

# Copy the current directory contents into the container at /app
COPY . /app

# Normally we would install any needed packages specified in requirements.txt
# RUN pip install --no-cache-dir -r requirements.txt
RUN pip install flask

# ENV Variables
ENV PORT=5002

# Port 5000 is the default value for flask apps
# Make port 5000 available to the world outside this container
# Note that this is for the purposes of documentation
# The port is actually exposed when you run the container from the command line
EXPOSE $PORT

# Run app.py when the container launches
CMD ["python3", "app.py"]

# Health check (checks every 30 seconds to see if the endpoint
# returns a successful response)
HEALTHCHECK --interval=30s --timeout=3s \
CMD curl -f http://localhost:${PORT}/healthcheck || exit 1
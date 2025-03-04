# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Upgrade pip to the latest version
RUN pip install --upgrade pip

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Install deno using the official installation script
RUN apt-get update && apt-get install -y curl ca-certificates unzip \
    && curl -fsSL https://deno.land/install.sh | sh \
    && echo "Deno installation completed" \
    && ls -l /root/.deno/bin

# Add deno to the PATH
ENV DENO_INSTALL=/root/.deno
ENV PATH=$DENO_INSTALL/bin:$PATH

# Make port 80 available to the world outside this container
EXPOSE 80

# Define the default command to run behave.py
CMD ["python", "behave.py"]
# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y \
    tesseract-ocr \
    tesseract-ocr-eng \
    tesseract-ocr-guj \
    tesseract-ocr-hin \
    unzip \
    wget \
    nginx \
    && apt-get clean

# Install Ghostscript
COPY ghostscript-9.54.0-linux-x86_64/gs-9540-linux-x86_64 /usr/local/bin/gs

# Set the work directory
WORKDIR /app

# Copy the requirements.txt file (create this file with your Python dependencies)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application files
COPY . /app

# Copy the Nginx configuration file
COPY nginx.conf /etc/nginx/nginx.conf

# Expose port 80 for Nginx and 5000 for Flask
EXPOSE 80 5000

# Start Nginx and Gunicorn
CMD ["sh", "-c", "service nginx start && gunicorn -w 4 -b 0.0.0.0:5000 app:app"]

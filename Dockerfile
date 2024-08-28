# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-hin \
    tesseract-ocr-san \
    && apt-get clean

# Install Ghostscript 9.54
RUN wget https://github.com/ArtifexSoftware/ghostpdl-downloads/releases/download/gs9540/ghostscript-9.54.0-linux-x86_64.tgz \
    && tar -xvzf ghostscript-9.54.0-linux-x86_64.tgz \
    && cp ghostscript-9.54.0-linux-x86_64/gs-954-linux-x86_64 /usr/local/bin/gs \
    && rm -rf ghostscript-9.54.0-linux-x86_64* 

# Copy the current directory contents into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 80 for the app to run on
EXPOSE 80

# Run the Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

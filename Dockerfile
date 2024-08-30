# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies (excluding Ghostscript)
RUN apt-get update && apt-get install -y \
    wget \
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-hin \
    tesseract-ocr-san \
    pngquant \
    libjpeg-dev \
    libpng-dev \
    && apt-get clean

# Copy the local Ghostscript binary into the container
COPY gs-9540-linux-x86_64 /usr/local/bin/gs

# Make the Ghostscript binary executable
RUN chmod +x /usr/local/bin/gs

# Copy the current directory contents into the container
COPY . .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 80 for the Flask app to run on
EXPOSE 80

# Run the Flask app with Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:80", "app:app"]

# Use an official Python runtime as a parent image
FROM python:3.9-slim

# Set the working directory
WORKDIR /app

# Copy the current directory contents into the container
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Ghostscript
COPY gs-9540-linux-x86_64 /usr/local/bin/gs

# Install Tesseract with additional languages
RUN apt-get update && \
    apt-get install -y tesseract-ocr tesseract-ocr-guj tesseract-ocr-hin

# Expose port 80 for the app to run on
EXPOSE 80

# Run the Flask app
CMD ["python", "app.py"]

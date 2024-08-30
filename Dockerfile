# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set the working directory
WORKDIR /app

# Install system dependencies including JBIG2 encoder dependencies
RUN apt-get update && apt-get install -y \
    wget \
    tesseract-ocr \
    tesseract-ocr-guj \
    tesseract-ocr-hin \
    tesseract-ocr-san \
    pngquant \
    libjpeg-dev \
    libpng-dev \
    autotools-dev \
    automake \
    libtool \
    libleptonica-dev \
    git \
    build-essential \  
    && apt-get clean

# Clone, build, and install JBIG2 encoder
RUN git clone https://github.com/agl/jbig2enc && \
    cd jbig2enc && \
    ./autogen.sh && \
    ./configure && \
    make && \
    make install

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

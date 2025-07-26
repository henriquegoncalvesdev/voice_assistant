# Dockerfile for Voice Assistant
FROM python:3.9-slim

# Install dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsm6 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install git+https://github.com/openai/whisper.git

# Copy application code
COPY . .

# Expose port and run the application
EXPOSE 5000
CMD ["python", "app.py"]

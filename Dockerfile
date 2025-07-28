FROM python:3.12-slim

WORKDIR /app

# Install system dependencies: build tools, vim, and coreutils for ll
RUN apt-get update && apt-get install -y \
    build-essential \
    vim \
    curl \
    coreutils \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# Optional: Add ll alias
RUN echo "alias ll='ls -alF'" >> /root/.bashrc

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code and .env
COPY . .
COPY .env .

# Expose FastAPI port
EXPOSE 8000

# Start FastAPI server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

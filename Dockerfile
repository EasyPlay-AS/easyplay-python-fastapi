# Use Python 3.11 slim image
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install AMPL Community Edition
RUN wget https://ampl.com/dl/free/ampl-community-linux64.tgz && \
    tar -xzf ampl-community-linux64.tgz && \
    mv ampl-community-linux64 /opt/ampl && \
    ln -s /opt/ampl/ampl /usr/local/bin/ampl && \
    rm ampl-community-linux64.tgz

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:8000"]

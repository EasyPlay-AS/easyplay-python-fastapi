FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies if needed
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

# Install AMPL solver
RUN python -m amplpy.modules install scip

# Copy application code
COPY . .

# Activate AMPL license (this will use the environment variable)
RUN python -m amplpy.modules activate $AMPL_LICENSE_UUID || echo "AMPL license activation skipped"

# Expose port
EXPOSE 8000

# Start command
CMD ["hypercorn", "main:app", "--bind", "[::]:$PORT"]
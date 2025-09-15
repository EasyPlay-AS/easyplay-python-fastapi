FROM python:3.9-slim-bullseye

# Install necessary system dependencies for AMPL and solver compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variable for AMPL modules directory
ENV AMPL_MODULES_DIRECTORY=/app/ampl_modules

# Create the directory for AMPL modules
RUN mkdir -p ${AMPL_MODULES_DIRECTORY}

# Create and change to the application directory.
WORKDIR /app

# Copy local code and requirements file
COPY . .

# Upgrade pip and install project dependencies
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install amplpy and the SCIP solver separately
RUN python -m pip install amplpy --no-cache-dir && \
    python -m amplpy.modules install scip --install-dir ${AMPL_MODULES_DIRECTORY} --no-cache-dir

# Expose port 8000
EXPOSE 8000

# Run the web service on container startup.
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000}"]
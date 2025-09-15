# Start from a slim Python image
FROM python:3.9-slim-bullseye

# Install system dependencies required for building the SCIP solver
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

# Set the environment variable for AMPL module directory
ENV AMPL_MODULES_DIRECTORY=/app/ampl_modules

# Create the working directory for the application
WORKDIR /app

# Copy the application code into the container
COPY . .

# Install Python dependencies and the AMPL SCIP solver module
# This single RUN command ensures the solver is installed and ready
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    python -m amplpy.modules install scip --install-dir ${AMPL_MODULES_DIRECTORY} --no-cache-dir

# Expose the application port
EXPOSE 8000

# Start the application
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:${PORT:-8000}"]
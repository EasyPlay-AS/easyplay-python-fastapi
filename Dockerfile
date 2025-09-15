FROM python:3.9.6-slim-bullseye

# Install build dependencies required for amplpy and other packages.
# The `rm` command cleans up to keep the final image size small.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gfortran \
    libgmp-dev \
    && rm -rf /var/lib/apt/lists/*

# Set environment variable for AMPL modules directory
ENV AMPL_MODULES_DIRECTORY=/app/ampl_modules

# Create and change to the app directory.
WORKDIR /app

# Copy local code to the container image.
COPY . .

# Upgrade pip and install project dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Install amplpy and all necessary amplpy.modules into the specified directory
RUN python -m pip install amplpy --no-cache-dir
RUN python -m amplpy.modules install scip --install-dir ${AMPL_MODULES_DIRECTORY} --no-cache-dir

# Expose port 8000
EXPOSE 8000

# Run the web service on container startup.
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:${PORT:-8000}"]
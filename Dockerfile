FROM python:3.9-slim-bullseye

# Install necessary system dependencies for AMPL and solver compilation
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     gfortran \
#     libgmp-dev \
#     && rm -rf /var/lib/apt/lists/*

# Create and change to the application directory.
WORKDIR /app

# Copy local code and requirements file
COPY . .

# Upgrade pip and install project dependencies
RUN python -m pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Install amplpy, then install AMPL runtime and SCIP into the modules store
RUN python -m pip install --no-cache-dir amplpy && \
    python -m amplpy.modules install ampl && \
    python -m amplpy.modules install scip

# Expose port 8000
EXPOSE 8000

# Run the web service on container startup.
CMD ["sh", "-c", "hypercorn main:app --bind 0.0.0.0:${PORT:-8000}"]
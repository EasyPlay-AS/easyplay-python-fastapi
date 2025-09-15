# Start from a clean, suitable base image
FROM python:3.9.6-slim-bullseye

# Create and change to the app directory.
WORKDIR /app

# Copy local code to the container image.
COPY . .

# Set the environment variable for AMPL module directory.
ENV AMPL_MODULES_DIRECTORY=/app/ampl_modules

# Copy the pre-downloaded SCIP solver from your local project into the Docker image.
COPY ampl/modules/scip ${AMPL_MODULES_DIRECTORY}/scip

# Make the copied solver executable
RUN chmod +x ${AMPL_MODULES_DIRECTORY}/scip

# Upgrade pip and install project dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

# Expose port 8000
EXPOSE 8000

# Run the web service on container startup.
CMD ["hypercorn", "main:app", "--bind", "0.0.0.0:${PORT:-8000}"]
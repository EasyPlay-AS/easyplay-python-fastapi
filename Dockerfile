FROM python:3.9.6-slim-bullseye

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
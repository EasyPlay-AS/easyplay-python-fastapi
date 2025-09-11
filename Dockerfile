# Use the Python 3 alpine official image
# https://hub.docker.com/_/python
FROM python:3-alpine

# Install build dependencies for amplpy
RUN apk add --no-cache \
    g++ \
    gcc \
    musl-dev \
    libffi-dev

# Create and change to the app directory.
WORKDIR /app

# Copy local code to the container image.
COPY . .

# Install project dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install SCIP solver for AMPL
RUN python -m amplpy.modules install scip

# Create a startup script for AMPL license activation
RUN echo '#!/bin/sh\n\
# Activate AMPL license if provided\n\
if [ -n "$AMPL_LICENSE_UUID" ]; then\n\
    echo "Activating AMPL license..."\n\
    python -m amplpy.modules activate "$AMPL_LICENSE_UUID"\n\
    echo "AMPL license activated successfully"\n\
else\n\
    echo "Warning: AMPL_LICENSE_UUID not set. AMPL will run in demo mode."\n\
fi\n\
\n\
# Start the application\n\
exec hypercorn main:app --bind 0.0.0.0:${PORT:-8000}\n\
' > /app/start.sh && chmod +x /app/start.sh

# Expose port 8000
EXPOSE 8000

# Run the startup script
CMD ["/app/start.sh"]
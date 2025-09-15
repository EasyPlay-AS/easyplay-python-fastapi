FROM python:3.9.6-slim-bullseye

WORKDIR /code

COPY ./requirements.txt /code/requirements.txt

# Upgrade pip and install project dependencies
RUN python -m pip install --upgrade pip
RUN pip install --no-cache-dir --upgrade -r /code/requirements.txt

# Install amplpy and all necessary amplpy.modules
RUN python -m pip install amplpy --no-cache-dir
RUN python -m amplpy.modules install scip --no-cache-dir

# Copy the application code
COPY ./app /code/app

# Expose port 8000
EXPOSE 8000

# Run the web service on container startup.
CMD ["hypercorn", "app.main:app", "--bind", "0.0.0.0:${PORT:-8000}"]
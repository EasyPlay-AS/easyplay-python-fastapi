# EasyPlay Python FastAPI

A lightweight FastAPI REST API for EasyPlay optimization services.

## Prerequisites

- Python 3.8+
- pip

## Setup

1. **Clone the repository**

   ```bash
   git clone <repository-url>
   cd easyplay-python-fastapi
   ```

2. **Create and activate virtual environment**

   ```bash
   python -m venv .venv # or python3
   source .venv/bin/activate  # On Windows: source .venv\Scripts\activate
   ```

3. Upgrade `pip`

   ```bash
   python -m pip install --upgrade pip
   ```

4. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

5. **Run the development server**

   ```bash
   fastapi dev main.py
   ```

The API will be available at `http://127.0.0.1:8000/`

## API Endpoints

- `GET /` - API information
- `POST /optimization` - Optimization endpoint

## Interactive Documentation

FastAPI automatically generates interactive API documentation:

- **Swagger UI**: `http://127.0.0.1:8000/docs`
- **ReDoc**: `http://127.0.0.1:8000/redoc`

## Features

- ⚡ **Fast**: One of the fastest Python frameworks
- 🔧 **Type hints**: Full Python type support
- 📚 **Auto docs**: Automatic OpenAPI/Swagger documentation
- ✅ **Validation**: Automatic request/response validation
- 🔒 **Security**: Built-in security features

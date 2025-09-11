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

5. **Install and setup AMPL**

- [AMPL initiup setup](https://amplpy.ampl.com/en/latest/getting-started.html)

  ```bash
  # Install Python API for AMPL
  python -m pip install amplpy --upgrade

  # Install SCIP (AMPL is installed automatically with any solver)
  python -m amplpy.modules install scip

  # Activate your license (e.g., free https://ampl.com/ce license)
  python -m amplpy.modules activate <license-uuid>

  # Confirm that the license is active
  python -m amplpy.modules run ampl -vvq
  ```

6. **Run the development server**

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

## Railway Deployment

To deploy this application on Railway:

1. **Set up AMPL License**

   - Get a free AMPL Community Edition license from [https://ampl.com/ce](https://ampl.com/ce)
   - Copy your license UUID

2. **Configure Railway Environment**

   - In your Railway project, go to Variables tab
   - Add environment variable: `AMPL_LICENSE_UUID` with your license UUID

3. **Deploy**

   - Connect your GitHub repository to Railway
   - Railway will use the Dockerfile for deployment (configured in `railway.json`)
   - The deployment will automatically:
     - Install all dependencies including `amplpy`
     - Install SCIP solver
     - Activate your AMPL license using the environment variable
     - Start the FastAPI application

4. **Verify Deployment**
   - Check the logs to ensure AMPL license is activated successfully
   - Test the `/solve-example` endpoint at `https://your-app.railway.app/solve-example`

## Features

- ⚡ **Fast**: One of the fastest Python frameworks
- 🔧 **Type hints**: Full Python type support
- 📚 **Auto docs**: Automatic OpenAPI/Swagger documentation
- ✅ **Validation**: Automatic request/response validation
- 🔒 **Security**: Built-in security features
- 🚀 **Railway Ready**: Pre-configured for Railway deployment with AMPL

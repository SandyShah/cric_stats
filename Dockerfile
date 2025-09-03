# Use a lightweight Python base
FROM python:3.9-slim

# Create and set working directory
WORKDIR /code

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Make sure data directory exists with proper permissions
RUN mkdir -p data && chmod -R 777 data

# Expose Streamlit port
EXPOSE 8501

# Run the app
CMD ["streamlit", "run", \
     "streamlit_app.py", \
     "--server.port=8501", \
     "--server.address=0.0.0.0", \
     "--server.baseUrlPath=/", \
     "--server.enableCORS=false", \
     "--server.enableXsrfProtection=false", \
     "--browser.serverAddress=0.0.0.0", \
     "--server.headless=true"]

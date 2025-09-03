# Use a lightweight Python base
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files
COPY . .

# Make sure data directory exists
RUN mkdir -p data

# Expose Streamlit port
EXPOSE 8501

# Run the app
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]

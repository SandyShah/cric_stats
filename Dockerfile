# Use a lightweight Python base
FROM python:3.10-slim

# Set working directory
WORKDIR /workspace

# System dependencies (optional but useful for scientific libs)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (so Docker can cache installs)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files into the container
COPY . .

# Expose Streamlit default port
EXPOSE 8501

# Healthcheck for HuggingFace Spaces
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run the Streamlit app (now directly from root)
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]

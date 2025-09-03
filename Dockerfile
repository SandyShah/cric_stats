# Base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Expose port (Hugging Face sets $PORT dynamically, so just expose it)
EXPOSE $PORT

# Run Streamlit app
CMD streamlit run streamlit_app.py --server.port $PORT --server.address 0.0.0.0

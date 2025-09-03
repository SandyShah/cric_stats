FROM python:3.9-slim

WORKDIR /app

# Copy requirements first for better cache utilization
COPY requirements.txt .

# Install dependencies
RUN pip install -r requirements.txt

# Copy the rest of the application
COPY . .

# Command to run the application
EXPOSE 8501
ENTRYPOINT ["streamlit", "run", "streamlit_app.py", "--server.address=0.0.0.0"]

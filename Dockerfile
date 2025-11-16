# Use the official Python 3.12 image as base
FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install common Python packages
RUN pip install --upgrade pip setuptools wheel

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Copy and run script to patch Streamlit HTML for SEO
COPY patch_streamlit_html.py /tmp/patch_streamlit_html.py
RUN python3 /tmp/patch_streamlit_html.py && rm /tmp/patch_streamlit_html.py

# Copy application code
COPY . .

# Expose Streamlit port
EXPOSE 8501

# Set the default command to run Streamlit
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
# Use Python 3.11 slim image as base
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements file if it exists
COPY requirements.txt* ./

# Install dependencies if requirements.txt exists
RUN if [ -f requirements.txt ]; then pip install --no-cache-dir -r requirements.txt; fi

# Copy application code
COPY . .

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Expose port (adjust as needed)
EXPOSE 8080

# Command to run the application (adjust based on your entry point)
CMD ["python", "main.py"]

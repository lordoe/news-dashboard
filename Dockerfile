# Use Python 3.11 slim image (compatible with Raspberry Pi ARM)
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port 5000
EXPOSE 5000

# Run the application
# Using python app.py directly. For production, consider gunicorn.
CMD ["python", "app.py"]

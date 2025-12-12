# Use Python 3.11 slim image (compatible with Raspberry Pi ARM)
FROM python:3.11-slim

# Create a non-root user with a specific UID (1000 is common for the first user on Linux)
RUN useradd -m -u 1000 appuser

# Set working directory
WORKDIR /app

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Change ownership of the application directory to the non-root user
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port 5000
EXPOSE 5000

# Run the application
# Using python app.py directly. For production, consider gunicorn.
CMD ["python", "app.py"]

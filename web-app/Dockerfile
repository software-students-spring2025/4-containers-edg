FROM python:3.10-slim

WORKDIR /app

# Copy requirements files
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pip install pipenv && \
    pipenv install --system --deploy

# Copy application code
COPY . .

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV PYTHONUNBUFFERED=1

# Expose port
EXPOSE 3000

# Command to run the application
CMD ["python", "app.py"]

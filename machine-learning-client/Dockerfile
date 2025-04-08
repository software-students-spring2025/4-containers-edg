FROM python:3.10-slim

WORKDIR /app

# Copy requirements files
COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pip install pipenv && \
    pipenv install --system --deploy

# Copy application code
COPY . .

# Command to run the application
CMD ["python", "app.py"]

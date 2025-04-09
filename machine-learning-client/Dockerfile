FROM python:3.10-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY Pipfile Pipfile.lock ./

# Install dependencies
RUN pip install pipenv && \
    pipenv install --system --deploy

# Copy application code
COPY . .

# Expose the port that the app runs on
EXPOSE 5005

# Command to run the application
CMD ["python", "app.py"]

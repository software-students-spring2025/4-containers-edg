FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install pipenv && pipenv install --system --deploy

CMD ["python", "app.py"]

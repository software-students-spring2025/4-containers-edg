#!/bin/bash

if [ -f ".env.example" ]; then
  echo "Copying root .env.example to .env"
  cp .env.example .env
fi

if [ -f "web-app/.env.example" ]; then
  echo "Copying web-app/.env.example to web-app/.env"
  cp web-app/.env.example web-app/.env
fi

if [ -f "machine-learning-client/.env.example" ]; then
  echo "Copying machine-learning-client/.env.example to machine-learning-client/.env"
  cp machine-learning-client/.env.example machine-learning-client/.env
fi

echo "Environment setup complete"

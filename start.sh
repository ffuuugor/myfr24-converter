#!/bin/bash
set -e

echo "Current directory: $(pwd)"
echo "Contents of /app:"
ls -la /app

echo "Python version:"
python --version

echo "Pip list:"
pip list

echo "Starting Nginx..."
nginx

echo "Starting Gunicorn..."
GUNICORN_PATH=$(which gunicorn)
echo "Gunicorn path: $GUNICORN_PATH"
$GUNICORN_PATH --bind unix:/tmp/gunicorn.sock app:app

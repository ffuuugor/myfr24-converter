#!/bin/bash
set -e

echo "Downloading assets..."
mkdir -p /app/data
curl -o /app/data/planes.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/planes.dat
curl -o /app/data/airlines.dat https://raw.githubusercontent.com/jpatokal/openflights/master/data/airlines.dat

echo "Verifying downloaded assets:"
ls -la /app/data

echo "Starting Nginx..."
nginx

echo "Starting Gunicorn..."
GUNICORN_PATH=$(which gunicorn)
$GUNICORN_PATH --bind unix:/tmp/gunicorn.sock app:app

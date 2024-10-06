# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

COPY . .

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && apt-get install -y nginx && rm -rf /var/lib/apt/lists/*

# Explicitly install Gunicorn
RUN pip install --no-warn-script-location gunicorn

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

# Verify installations and paths
RUN echo $PATH && \
    which nginx && \
    which gunicorn && \
    which flask && \
    which f2py && \
    ls /app/app.py && \
    ls /etc/nginx/nginx.conf

# Use a shell script to start services
COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

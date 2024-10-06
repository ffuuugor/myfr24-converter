# Build stage
FROM python:3.12-slim as builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --user --no-cache-dir --no-warn-script-location -r requirements.txt

COPY . .

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

COPY --from=builder /root/.local /root/.local
COPY --from=builder /app /app

# Ensure local bin is in PATH
ENV PATH=/root/.local/bin:$PATH

RUN apt-get update && \
    apt-get install -y nginx curl && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --no-warn-script-location gunicorn

COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80

RUN mkdir -p /app/data && chmod 777 /app/data

COPY start.sh /start.sh
RUN chmod +x /start.sh

CMD ["/start.sh"]

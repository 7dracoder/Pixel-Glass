FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Ensure the centerline data is present (download before building)
# The data/ folder should contain centerline.geojson (~120MB)
RUN test -f data/centerline.geojson || \
    echo "WARNING: data/centerline.geojson not found. Run download_centerline.py first."

# ADK api_server exposes the agent as an A2A-compatible HTTP server
# Cloud Run injects $PORT (default 8080)
CMD ["sh", "-c", "adk api_server --port ${PORT:-8080} ."]

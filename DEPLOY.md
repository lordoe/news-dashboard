# Deployment Instructions

## Setup Environment Variable

You need to set the `GEMINI_API_KEY` before running. You can create a `.env` file in the same directory:

```bash
echo "GEMINI_API_KEY=xxx" > .env
```

## Running with Docker Compose

```bash
docker-compose up -d --build
```

## Running with Podman

```bash
podman-compose up -d --build
```

Or manually with Podman:

```bash
podman build -t news-dashboard .
podman run -d --name news-dashboard \
  -p 5000:5000 \
  -e GEMINI_API_KEY="YOUR_KEY_HERE" \
  -v ./config.json:/app/config.json \
  -v ./archive.json:/app/archive.json \
  -v ./cache.json:/app/cache.json \
  news-dashboard
```

Access the dashboard at `http://localhost:5000` (or your Pi's IP).

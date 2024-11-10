# Screenshot API Service

A containerized web service that takes screenshots of websites using headless Chrome.

## Features
- Takes screenshots of any public webpage
- RESTful API interface
- Docker containerized
- Configurable screenshot dimensions
- Returns PNG images

## Prerequisites
- Docker
- Docker Compose

## Installation

1. Clone the repository:
```bash
git clone [your-repository-url]
cd screenshot-service
```

2. Build and start the service:
```bash
docker-compose up --build
```

3. The service will be available at `http://localhost:5000`

## API Usage

### Check Status
```bash
curl http://localhost:5000/status
```

### Take Screenshot
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"url":"https://example.com"}' \
     http://localhost:5000/screenshot \
     --output screenshot.png
```

## API Endpoints

- `GET /status` - Check service status
- `GET /ping` - Health check
- `POST /screenshot` - Take screenshot (requires JSON body with 'url' parameter)

## Directory Structure
```
screenshot-service/
├── api/
│   ├── requirements.txt
│   ├── screenshot_api.py
│   └── monitor.sh
├── screenshots/
├── docker-compose.yml
└── Dockerfile
```

## Configuration
The service can be configured through environment variables in the docker-compose.yml file.

## Development
To run in development mode:
```bash
docker-compose up --build
```

## Monitoring
To check service status:
```bash
docker exec screenshot-service-screenshot-service-1 /vm/api/monitor.sh
```

## License
[Your chosen license]
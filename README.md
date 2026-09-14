# URL Shortener

A full-stack URL shortener built with **FastAPI, PostgreSQL, Redis, HTML/CSS/JavaScript, and Docker**.

The application allows users to convert long URLs into short, shareable links. It also supports custom short codes, URL expiration, click tracking, Redis caching, rate limiting, and a responsive web interface.

---

## Features

* 🔗 Create short URLs from long URLs
* 🔢 Automatic short-code generation using Base62 encoding
* ✏️ Custom short codes
* ⏳ URL expiration
* 📊 Click statistics
* ⚡ Redis caching for faster redirects
* 🛡️ Redis-based rate limiting
* 🗄️ PostgreSQL persistent storage
* 📋 Copy short URL functionality
* 🌐 Responsive HTML/CSS/JavaScript frontend
* 🐳 Docker and Docker Compose support
* ❤️ Health-check endpoint

---

## Tech Stack

| Category              | Technology            |
| --------------------- | --------------------- |
| Language              | Python                |
| Backend               | FastAPI               |
| Validation            | Pydantic              |
| Database              | PostgreSQL            |
| ORM                   | SQLAlchemy            |
| PostgreSQL Driver     | asyncpg               |
| Cache & Rate Limiting | Redis                 |
| Frontend              | HTML, CSS, JavaScript |
| Server                | Uvicorn               |
| Containerization      | Docker                |
| Orchestration         | Docker Compose        |

---

## How It Works

### Creating a Short URL

The URL creation flow works like this:

```text
User
  │
  │ Long URL
  ▼
Frontend
  │
  │ POST /shorten
  ▼
FastAPI
  │
  ├── Validate request
  │
  ├── Generate PostgreSQL ID
  │
  ├── Convert ID → Base62
  │
  └── Store URL + short code
          │
          ▼
      PostgreSQL
          │
          ▼
      Short URL
```

For example:

```text
https://www.example.com/very/long/url
                    ↓
                  "b7"
                    ↓
http://localhost:8000/b7
```

### Redirecting a Short URL

When a user opens a short URL:

```text
User
  │
  │ GET /b7
  ▼
FastAPI
  │
  ▼
Redis
  │
  ├── Cache HIT ──────► Original URL
  │
  └── Cache MISS
          │
          ▼
      PostgreSQL
          │
          ▼
      Original URL
          │
          ▼
       Redirect
```

Redis is checked first so frequently accessed URLs can be served without querying PostgreSQL every time.

---

## Project Structure

```text
url_shortner/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── database.py
│   ├── model.py
│   ├── redis.py
│   └── utils.py
│
├── frontend/
│   ├── index.html
│   ├── style.css
│   └── script.js
│
├── Dockerfile
├── docker-compose.yml
├── .dockerignore
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

### Backend

| File          | Purpose                                                                          |
| ------------- | -------------------------------------------------------------------------------- |
| `main.py`     | FastAPI application, endpoints, redirects, rate limiting and application startup |
| `database.py` | PostgreSQL connection and SQLAlchemy configuration                               |
| `model.py`    | SQLAlchemy URL database model                                                    |
| `redis.py`    | Redis connection                                                                 |
| `utils.py`    | Base62 encoding                                                                  |

### Frontend

| File         | Purpose                                                  |
| ------------ | -------------------------------------------------------- |
| `index.html` | URL shortener interface                                  |
| `style.css`  | Application styling and responsive layout                |
| `script.js`  | Frontend API requests, copy functionality and statistics |

---

## Getting Started

### Prerequisites

Make sure you have the following installed:

* [Docker](https://www.docker.com/)
* Docker Compose

### Clone the Repository

```bash
git clone <your-repository-url>
cd url_shortner
```

### Start the Application

Build and start all services using Docker Compose:

```bash
docker compose up -d --build
```

This starts:

* FastAPI API
* PostgreSQL database
* Redis server

### Verify the Containers

```bash
docker ps
```

You should see the following services running:

```text
url-shortener-api
url-shortener-postgres
url-shortener-redis
```

### Open the Application

Visit:

```text
http://localhost:8000
```

The FastAPI server serves the frontend directly.

### Health Check

The application provides a simple health-check endpoint:

```text
GET /health
```

Open:

```text
http://localhost:8000/health
```

Expected response:

```json
{
  "status": "ok"
}
```

### Stop the Application

```bash
docker compose down
```

The PostgreSQL database uses a Docker volume, so the database data is preserved when the containers are stopped.

---

## API Reference

### `GET /`

Serves the frontend application.

```text
http://localhost:8000/
```

---

### `GET /health`

Checks whether the API is running.

**Response:**

```json
{
  "status": "ok"
}
```

---

### `POST /shorten`

Creates a new shortened URL.

**Request:**

```json
{
  "long_url": "https://www.example.com",
  "custom_code": null,
  "expires_at": null
}
```

**Response:**

```json
{
  "long_url": "https://www.example.com/",
  "short_code": "b",
  "short_url": "http://localhost:8000/b"
}
```

The `custom_code` and `expires_at` fields are optional.

---

### `GET /{short_code}`

Redirects the user to the original URL.

Example:

```text
http://localhost:8000/b
```

Possible responses:

| Status | Meaning                   |
| ------ | ------------------------- |
| `302`  | Redirect to original URL  |
| `404`  | Short code does not exist |
| `410`  | Short URL has expired     |

---

### `GET /stats/{short_code}`

Returns statistics for a shortened URL.

Example:

```text
http://localhost:8000/stats/b
```

**Response:**

```json
{
  "short_code": "b",
  "long_url": "https://www.example.com/",
  "click_count": 5,
  "created_at": "2026-09-14T10:30:00",
  "expires_at": null
}
```

---

## Short Code Generation

The application uses **Base62 encoding** to generate compact short codes.

The Base62 character set contains:

```text
0-9
a-z
A-Z
```

A PostgreSQL sequence generates a unique numeric ID, which is then converted into a Base62 string.

For example:

```text
Database ID
    ↓
100
    ↓
Base62 encoding
    ↓
"1C"
```

This provides short, URL-friendly identifiers without storing the generated code separately.

---

## Redis

Redis is used for two main purposes.

### Caching

When a short URL is requested, Redis is checked before PostgreSQL.

```text
Request
   ↓
Redis
   │
   ├── HIT  → Use cached URL
   │
   └── MISS → PostgreSQL → Store in Redis
```

This reduces repeated database lookups for frequently accessed URLs.

### Rate Limiting

The `/shorten` endpoint is rate limited using Redis.

The current limit is:

```text
5 requests per minute per client IP
```

If the limit is exceeded, the API returns:

```text
429 Too Many Requests
```

---

## URL Expiration

Users can optionally specify an expiration date and time when creating a short URL.

Once the URL expires:

```text
GET /{short_code}
        ↓
Check expiration
        ↓
Expired
        ↓
410 Gone
```

URLs without an expiration date remain available until they are otherwise removed.

---

## Click Tracking

Every successful redirect increments the URL's click count.

For example:

```text
First click  → 1
Second click → 2
Third click  → 3
```

The current click count can be viewed through:

```text
GET /stats/{short_code}
```

It can also be viewed directly from the frontend using the **View Stats** button.

---

## Docker Architecture

The application runs as three main services:

```text
                    ┌──────────────┐
                    │   Frontend   │
                    │ HTML/CSS/JS  │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │   FastAPI    │
                    │     API      │
                    └──────┬───────┘
                           │
                  ┌────────┴────────┐
                  ▼                 ▼
          ┌──────────────┐   ┌──────────────┐
          │  PostgreSQL  │   │    Redis     │
          │   Database   │   │Cache/Rate    │
          │              │   │   Limiting   │
          └──────────────┘   └──────────────┘
```

Docker Compose manages all three services together.

---

## Useful Docker Commands

### Start

```bash
docker compose up -d
```

### Build and Start

```bash
docker compose up -d --build
```

### View Running Containers

```bash
docker ps
```

### View All Containers

```bash
docker ps -a
```

### View API Logs

```bash
docker logs url-shortener-api
```

### Stop Containers

```bash
docker compose down
```

### Rebuild After Code Changes

```bash
docker compose up -d --build
```

---

## Future Improvements

Possible future improvements include:

* Production deployment
* Database migrations with Alembic
* Automated test suite
* Authentication and user accounts
* Detailed analytics
* QR code generation
* Custom domains
* Better cache expiration management
* Production monitoring and logging

---

## License

This project is intended for learning and portfolio purposes.

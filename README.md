# Smart Study API

Smart Study API is a robust, performant RESTful service built with FastAPI that generates structured study notes based on user-provided topics and difficulty levels. It leverages Large Language Models (LLMs) via OpenRouter, with built-in caching and rate limiting.

## Features

- **FastAPI Framework**: High performance and automatic interactive API documentation (Swagger UI/ReDoc).
- **LLM Integration**: Uses OpenRouter (defaulting to `openai/gpt-4o-mini`) to dynamically generate study notes securely.
- **Structured Output**: Enforces strict JSON schemas for LLM responses using Pydantic, ensuring notes contain titles, summaries, key concepts, examples, and practice questions.
- **Caching**: Utilizes Redis to cache previously generated notes for 1 hour `(TTL: 3600s)`, drastically reducing API calls and improving response times.
- **Rate Limiting**: Protects generating endpoints by limiting requests to `5/minute` per IP address using SlowAPI.
- **Fallback Mechanism**: Provides offline, deterministic test-safe notes if the LLM service or caching layer encounters an error.

## Project Structure

```text
smart-study-api/
├── .env                # Environment variables (API keys, URLs)
├── .gitignore          # Git ignore rules
├── requirements.txt    # Python dependencies
└── app/
    ├── __init__.py
    ├── main.py         # App entry point, middleware, routes
    ├── llm.py          # LLM prompt construction, calling, and fallback logic
    ├── schemas.py      # Pydantic models for request & response
    ├── cache.py        # Redis caching setup and helper functions
    ├── config.py       # Configuration and env var loading
    └── rate_limit.py   # SlowAPI limiter instance
```

## Setup & Installation

### Prerequisites

- Python 3.9+
- Redis (running locally on port `6379`)

### 1. Clone the Repository

```bash
git clone <repository_url>
cd smart-study-api
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: .\\venv\\Scripts\\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Variables

Create a `.env` file in the root directory and add the following:

```env
OPENROUTER_API_KEY=your_openrouter_api_key_here
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
OPENROUTER_MODEL=openai/gpt-4o-mini
```

### 5. Start Redis

Make sure your Redis server is running.
```bash
# If installed locally on Linux/Mac
redis-server

# Or using Docker
docker run -p 6379:6379 -d redis
```

### 6. Run the Application

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. FastAPIs interactive docs can be found at `http://127.0.0.1:8000/docs`.

## API Endpoints

### 1. Health Check
- **Endpoint:** `GET /`
- **Description:** Verifies the API is running.
- **Response:**
  ```json
  {
    "message": "Smart Study API running!"
  }
  ```

### 2. Generate Study Notes
- **Endpoint:** `POST /generate`
- **Rate Limit:** 5 requests per minute
- **Request Body (`app/schemas.py`):**
  ```json
  {
    "topic": "Quantum Computing",
    "difficulty": "hard"
  }
  ```
  *(Topic must be between 3 and 100 characters. Difficulty defaults to "medium".)*

- **Response:**
  ```json
  {
    "title": "Study notes for Quantum Computing",
    "summary": "...",
    "key_concepts": ["...", "..."],
    "examples": ["..."],
    "practice_questions": ["...", "..."]
  }
  ```

## Development

- **Logging**: The application leverages Python's built-in `logging` module to track cache hits/misses, and LLM query generation events.
- **Error Handling**: API gracefully falls back to deterministic mock data if LLM validation fails or rate limits are exceeded, managed via FastAPI Exception handlers.

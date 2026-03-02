from fastapi import FastAPI, HTTPException, Request
from app.schemas import StudyRequest, StudyResponse
from app.llm import generate_notes
from app.rate_limit import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

app = FastAPI()

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.get("/")
def root():
    return {"message": "Smart Study API running!"}


@app.post("/generate", response_model=StudyResponse)
@limiter.limit("5/minute") 
def generate_study_notes(request: Request, body: StudyRequest):
    try:
        return generate_notes(body.topic)
    except Exception as e:
        print("ERROR: ",e)
        raise HTTPException(status_code=500, detail=str(e))
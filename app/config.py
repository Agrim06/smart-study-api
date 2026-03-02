import os
from dotenv import load_dotenv

load_dotenv()

# OpenRouter configuration. These may be None during local testing;
# downstream code should handle missing values gracefully.
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-4o-mini")
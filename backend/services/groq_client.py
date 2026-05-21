import logging

from fastapi import HTTPException
from groq import Groq, APIError, RateLimitError

import state.store as store
from config.settings import GROQ_API_KEY, GROQ_MODEL

log = logging.getLogger("cloud-ops.groq")

_client = Groq(api_key=GROQ_API_KEY)


def call_groq(
    system: str,
    messages: list,
    max_tokens: int   = 300,
    temperature: float = 0.3,
) -> str:
    """
    Call the Groq chat API.
    Increments the global call counter and raises mapped HTTP exceptions on failure.
    """
    try:
        response = _client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "system", "content": system}] + messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        store.groq_call_count += 1
        log.info("Groq call #%d completed", store.groq_call_count)
        return response.choices[0].message.content

    except RateLimitError:
        log.warning("Groq rate limit hit")
        raise HTTPException(status_code=429, detail="AI rate limit reached — try again shortly.")

    except APIError as e:
        log.error("Groq API error: %s", e)
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")

    except Exception as e:
        log.error("Unexpected Groq error: %s", e)
        raise HTTPException(status_code=500, detail="Internal AI error.")
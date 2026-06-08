import time
import anthropic
from config import ANTHROPIC_API_KEY, CHANNEL_VOICE

_client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY, timeout=60.0)


def generate(prompt: str, max_tokens: int = 600, retries: int = 3) -> str:
    last_err = None
    for attempt in range(retries):
        try:
            msg = _client.messages.create(
                model="claude-sonnet-4-6",
                max_tokens=max_tokens,
                system=CHANNEL_VOICE,
                messages=[{"role": "user", "content": prompt}],
            )
            return msg.content[0].text.strip()
        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            last_err = e
            wait = 5 * (attempt + 1)
            print(f"  [claude retry {attempt+1}] {e} — waiting {wait}s")
            time.sleep(wait)
    raise last_err

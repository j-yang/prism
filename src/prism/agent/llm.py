import os
import logging
import requests
from typing import Optional

logger = logging.getLogger(__name__)

DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
DEFAULT_MODEL = "deepseek-chat"


def get_api_key() -> Optional[str]:
    return os.environ.get("DEEPSEEK_API_KEY")


def call_deepseek(
    prompt: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.1,
    timeout: int = 60,
) -> Optional[str]:
    api_key = get_api_key()
    if not api_key:
        logger.warning("No DEEPSEEK_API_KEY found in environment")
        return None

    try:
        response = requests.post(
            DEEPSEEK_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
            },
            timeout=timeout,
        )
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"DeepSeek API call failed: {e}")
        return None


def extract_code_block(content: str, language: str = "python") -> str:
    content = content.strip()
    marker = f"```{language}"

    if marker in content:
        content = content.split(marker)[1]
        if "```" in content:
            content = content.split("```")[0]
    elif "```" in content:
        content = content.split("```")[1]
        if "```" in content:
            content = content.split("```")[0]

    return content.strip()

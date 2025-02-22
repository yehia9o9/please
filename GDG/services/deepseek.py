import requests
import logging
from config import Config

def get_deepseek_solution(question):
    """Fetch solution from DeepSeek."""
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {Config.OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": Config.DEEPSEEK_MODEL_ID,
            "messages": [{"role": "user", "content": f"Solve this math problem step by step: {question}"}],
            "temperature": 0.7
        }
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
        response_data = response.json()
        if "choices" in response_data and response_data["choices"]:
            choice = response_data["choices"][0]
            if "message" in choice and "content" in choice["message"]:
                return choice["message"]["content"].strip()
    except requests.exceptions.RequestException as e:
        logging.error(f"DeepSeek API request failed: {e}")
    return None
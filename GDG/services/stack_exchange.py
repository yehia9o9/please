import requests
import logging
from bs4 import BeautifulSoup

STACK_EXCHANGE_API_KEY = "rl_AkMa815x96XM6UqeAPZXWt3T3"

def clean_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text()

def get_stack_exchange_answers(question_id):
    try:
        url = f"https://api.stackexchange.com/2.3/questions/{question_id}/answers"
        params = {
            "site": "math.stackexchange",
            "key": STACK_EXCHANGE_API_KEY,
            "sort": "votes",
            "order": "desc",
            "filter": "withbody"
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "items" not in data:
            logging.error("No 'items' key in Stack Exchange API response.")
            return None
        if data["items"]:
            highest_voted_answer = data["items"][0]["body"]
            return clean_html(highest_voted_answer).strip()
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Stack Exchange API request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Stack Exchange query: {e}")
    return None

def get_stack_exchange_solution(question):
    try:
        url = "https://api.stackexchange.com/2.3/search/advanced"
        params = {
            "site": "math.stackexchange",
            "q": question,
            "key": STACK_EXCHANGE_API_KEY,
            "sort": "relevance",
            "order": "desc",
            "pagesize": 3,
            "answers": 1
        }
        response = requests.get(url, params=params)
        response.raise_for_status()
        data = response.json()
        if "items" not in data or not data["items"]:
            logging.error("No relevant questions found on Stack Exchange.")
            return None
        for item in data["items"]:
            question_id = item["question_id"]
            answer = get_stack_exchange_answers(question_id)
            if answer:
                return answer
        logging.error("No valid answers found on Stack Exchange. Falling back to Google AI.")
        return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Stack Exchange API request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Stack Exchange query: {e}")
    return None

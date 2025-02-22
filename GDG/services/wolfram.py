import requests
import urllib.parse
import xml.etree.ElementTree as ET
import logging
from config import Config

def get_wolfram_solution(question):
    """Fetch solution from Wolfram Alpha."""
    try:
        encoded_question = urllib.parse.quote(question)
        url = f"http://api.wolframalpha.com/v2/query?appid={Config.WOLFRAM_APP_ID}&input={encoded_question}&format=plaintext"
        logging.info(f"Wolfram API URL: {url}")

        response = requests.get(url)
        response.raise_for_status()

        root = ET.fromstring(response.content)
        if root.get("success") == "true":
            for pod in root.findall("pod"):
                pod_title = pod.get("title")
                if pod_title in ["Solutions", "Roots", "Real solutions", "Result"]:
                    solutions = []
                    for subpod in pod.findall("subpod"):
                        plaintext = subpod.find("plaintext").text
                        if plaintext:
                            solutions.append(plaintext.strip())
                    if solutions:
                        return ", ".join(solutions)
            logging.error("No plaintext result found in the relevant pods.")
            return None
        else:
            logging.error("Wolfram Alpha query was not successful.")
            return None
    except requests.exceptions.RequestException as e:
        logging.error(f"Wolfram Alpha API request failed: {e}")
    except ET.ParseError as e:
        logging.error(f"Error parsing Wolfram Alpha XML response: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Wolfram Alpha query: {e}")
    return None
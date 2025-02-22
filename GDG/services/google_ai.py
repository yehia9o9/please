import google.generativeai as genai
import logging
from config import Config

def get_google_ai_solution(question):
    """Fetch solution from Google AI."""
    try:
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-pro")
        prompt = (
            f"Solve the following math problem step by step, clearly explaining each step. "
            f"Format the response as follows:\n\n"
            f"*Steps:*\n"
            f"1. Step 1: [Explanation of the first step]\n"
            f"2. Step 2: [Explanation of the second step]\n"
            f"...\n"
            f"*Final Answer:* [The final answer]\n\n"
            f"Problem: {question}"
        )
        response = model.generate_content(prompt)
        if response.text:
            return response.text.strip()
    except Exception as e:
        logging.error(f"Google AI Error: {e}")
    return None

def evaluate_answers_with_gemini(question, answers):
    """Send answers to Gemini for evaluation and select the best one."""
    try:
        genai.configure(api_key=Config.GOOGLE_API_KEY)
        model = genai.GenerativeModel("gemini-pro")

        # Prepare the prompt for Gemini
        prompt = (
            f"Evaluate the following answers to the math problem and select the best one (excluding your own answer). "
            f"Explain why you chose it.\n\n"
            f"Problem: {question}\n\n"
            f"Answers:\n"
        )
        for i, answer in enumerate(answers):
            prompt += f"{i + 1}. {answer}\n\n"

        # Log the prompt being sent to Gemini
        logging.debug(f"Sending prompt to Gemini: {prompt}")

        # Send the prompt to Gemini
        response = model.generate_content(prompt)
        if response.text:
            logging.debug(f"Gemini response: {response.text.strip()}")
            return response.text.strip()
    except Exception as e:
        logging.error(f"Gemini evaluation error: {e}")
    return None
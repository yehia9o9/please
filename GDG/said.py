from flask import Flask, request, render_template
from flask_caching import Cache
from concurrent.futures import ThreadPoolExecutor
import logging
import os
import google.generativeai as genai
import requests
import sympy as sp
import re
import urllib.parse
import xml.etree.ElementTree as ET
from requests.exceptions import RequestException
from sympy import SympifyError
from bs4 import BeautifulSoup

os.environ["GRPC_POLL_STRATEGY"] = "poll"

logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")

GOOGLE_API_KEY = "AIzaSyCo_o56CNTksGuC9pyyk3EogIQG5X1jgvE"
WOLFRAM_APP_ID = "E7P9HP-R9P7HKJ6PJ"
OPENROUTER_API_KEY = "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"
DEEPSEEK_MODEL_ID = "deepseek/deepseek-chat:free"
STACK_EXCHANGE_API_KEY = "rl_AkMa815x96XM6UqeAPZXWt3T3"

app = Flask(_name_)

cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

@app.template_filter('extract_final_answer')
def extract_final_answer(solution):
    if "*Final Answer:*" in solution:
        return solution.split("*Final Answer:*")[1].strip()
    return solution

@app.template_filter('extract_steps')
def extract_steps(solution):
    if "*Final Answer:*" in solution:
        steps = solution.split("*Final Answer:*")[0].strip()
        return steps
    return solution

@app.template_filter('split_steps')
def split_steps(solution):
    if "*Final Answer:*" in solution:
        steps = solution.split("*Final Answer:*")[0].strip()
        return [step.strip() for step in steps.split("\n") if step.strip()]
    return ["No steps available."]

def preprocess_input_for_sympy(expression):
    try:
        expression = re.sub(r"(\d+)([a-zA-Z])", r"\1*\2", expression)
        expression = re.sub(r"([a-zA-Z])(\d+)", r"\1*\2", expression)
        expression = re.sub(r"([a-zA-Z])([a-zA-Z])", r"\1*\2", expression)
        expression = expression.replace("^", "")
        if "=" not in expression and "differentiate" not in expression.lower():
            expression = f"{expression} = 0"
        return expression
    except Exception as e:
        logging.error(f"Error preprocessing input: {e}")
        return None

@cache.memoize(timeout=300)
def get_google_ai_solution(question):
    try:
        genai.configure(api_key=GOOGLE_API_KEY)
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

@cache.memoize(timeout=300)
def get_deepseek_solution(question):
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEEPSEEK_MODEL_ID,
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
    except RequestException as e:
        logging.error(f"DeepSeek API request failed: {e}")
    return None

@cache.memoize(timeout=300)
def get_sympy_solution(question):
    try:
        processed_question = preprocess_input_for_sympy(question)
        if not processed_question:
            return None
        x = sp.Symbol('x')
        if "differentiate" in question.lower() or "derivative" in question.lower():
            expr = processed_question.replace("=", "")
            sym_expr = sp.sympify(expr.strip())
            derivative = sp.diff(sym_expr, x)
            return f"Step 1: Differentiate the expression.\nDerivative: {derivative}"
        if "=" not in processed_question:
            processed_question = f"{processed_question} = 0"
        parts = processed_question.split("=", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid equation format: {processed_question}")
        left_side, right_side = parts
        left_expr = sp.sympify(left_side.strip())
        right_expr = sp.sympify(right_side.strip())
        equation = sp.Eq(left_expr, right_expr)
        solutions = sp.solve(equation, x)
        if not solutions:
            return None
        return (
            f"Step 1: Rewrite the equation.\n"
            f"Equation: {equation}\n"
            f"Step 2: Solve for x.\n"
            f"Solution: {solutions}"
        )
    except SympifyError as e:
        logging.error(f"SymPy parsing error: {e}")
    except Exception as e:
        logging.error(f"SymPy Error: {e}")
    return None

@cache.memoize(timeout=300)
def get_wolfram_solution(question):
    try:
        encoded_question = urllib.parse.quote(question)
        url = f"http://api.wolframalpha.com/v2/query?appid={WOLFRAM_APP_ID}&input={encoded_question}&format=plaintext"
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
    except RequestException as e:
        logging.error(f"Wolfram Alpha API request failed: {e}")
    except ET.ParseError as e:
        logging.error(f"Error parsing Wolfram Alpha XML response: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Wolfram Alpha query: {e}")
    return None

def clean_html(html_text):
    soup = BeautifulSoup(html_text, "html.parser")
    return soup.get_text()

@cache.memoize(timeout=300)
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
    except RequestException as e:
        logging.error(f"Stack Exchange API request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Stack Exchange query: {e}")
    return None

@cache.memoize(timeout=300)
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
        return get_google_ai_solution(question)
    except RequestException as e:
        logging.error(f"Stack Exchange API request failed: {e}")
    except Exception as e:
        logging.error(f"Unexpected error in Stack Exchange query: {e}")
    return None

def fetch_solutions_async(question):
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(get_google_ai_solution, question),
            executor.submit(get_deepseek_solution, question),
            executor.submit(get_sympy_solution, question),
            executor.submit(get_wolfram_solution, question),
            executor.submit(get_stack_exchange_solution, question)
        ]
        solutions = [future.result() for future in futures]
    return solutions

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')
    if not query:
        return render_template('index.html', error="Please enter a math problem.")
    solutions = fetch_solutions_async(query)
    formatted_solutions = [
        (solutions[0] or "No solution from Google AI.", "Google AI"),
        (solutions[1] or "No solution from DeepSeek.", "DeepSeek"),
        (solutions[2] or "No solution from SymPy.", "SymPy"),
        (solutions[3] or "No solution from Wolfram Alpha.", "Wolfram Alpha"),
        (solutions[4] or "No solution from Stack Exchange.", "Stack Exchange")
    ]
    return render_template('index.html', query=query, solutions=formatted_solutions)

if _name_ == '_main_':
    app.run(debug=True)
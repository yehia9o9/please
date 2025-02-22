from flask import Flask, request, render_template, session, jsonify
from flask_caching import Cache
from concurrent.futures import ThreadPoolExecutor
import logging
from services.google_ai import get_google_ai_solution, evaluate_answers_with_gemini
from services.deepseek import get_deepseek_solution
from services.sympy import get_sympy_solution
from services.wolfram import get_wolfram_solution
from services.stack_exchange import get_stack_exchange_solution
from utils.filters import extract_final_answer, extract_steps, split_steps
from config import Config
from sympy import symbols, lambdify, sympify
import numpy as np

import io
import base64

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

app = Flask(__name__)
app.secret_key = "your_secret_key_here" 
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

app.jinja_env.filters['extract_final_answer'] = extract_final_answer
app.jinja_env.filters['extract_steps'] = extract_steps
app.jinja_env.filters['split_steps'] = split_steps

def fetch_solutions_async(question):
    """Fetch solutions from all services concurrently."""
    with ThreadPoolExecutor() as executor:
        futures = [
            executor.submit(get_google_ai_solution, question),
            executor.submit(get_deepseek_solution, question),
            executor.submit(get_sympy_solution, question),
            executor.submit(get_wolfram_solution, question),
            executor.submit(get_stack_exchange_solution, question)
        ]
        solutions = [future.result() for future in futures]
    
    logging.debug(f"Fetched solutions: {solutions}")
    return solutions

@app.route('/')
def home():
    """Render the home page."""
    return render_template('index.html')

@app.route('/search', methods=['GET'])
def search():
    """Handle search requests and display solutions."""
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

    best_answer = evaluate_answers_with_gemini(query, [sol[0] for sol in formatted_solutions])

    return render_template(
        'index.html',
        query=query,
        best_answer=best_answer,
        all_answers=formatted_solutions  
    )

@app.route('/show_all_answers', methods=['GET'])
def show_all_answers():
    """Display all answers when the user clicks the button."""
    all_answers = session.get('all_answers', [])
    return render_template('index.html', all_answers=all_answers)



if __name__ == '__main__':
    app.run(debug=True)

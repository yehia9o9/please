from flask import Flask, request, render_template, session
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

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")

app = Flask(__name__)
app.secret_key = "your_secret_key_here"  # Required for session support
cache = Cache(app, config={'CACHE_TYPE': 'SimpleCache'})

# Register custom filters
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
    
    # Log the fetched solutions
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

    # Fetch all answers
    solutions = fetch_solutions_async(query)
    formatted_solutions = [
        (solutions[0] or "No solution from Google AI.", "Google AI"),
        (solutions[1] or "No solution from DeepSeek.", "DeepSeek"),
        (solutions[2] or "No solution from SymPy.", "SymPy"),
        (solutions[3] or "No solution from Wolfram Alpha.", "Wolfram Alpha"),
        (solutions[4] or "No solution from Stack Exchange.", "Stack Exchange")
    ]

    # Log the formatted solutions
    logging.debug(f"Formatted solutions: {formatted_solutions}")

    # Exclude Gemini's own answer for evaluation
    other_answers = [sol[0] for sol in formatted_solutions if sol[1] != "Google AI"]

    # Log the other answers being sent to Gemini
    logging.debug(f"Other answers for Gemini evaluation: {other_answers}")

    # Send answers to Gemini for evaluation
    best_answer = evaluate_answers_with_gemini(query, other_answers)

    # Log the best answer selected by Gemini
    logging.debug(f"Best answer selected by Gemini: {best_answer}")

    # Store all answers in the session for later display
    session['all_answers'] = formatted_solutions
    session['best_answer'] = best_answer

    # Display the best answer initially
    return render_template('index.html', query=query, best_answer=best_answer)

@app.route('/show_all_answers', methods=['GET'])
def show_all_answers():
    """Display all answers when the user clicks the button."""
    all_answers = session.get('all_answers', [])
    return render_template('index.html', all_answers=all_answers)

if __name__ == '__main__':
    app.run(debug=True)
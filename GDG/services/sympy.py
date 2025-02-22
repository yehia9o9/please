import sympy as sp
import logging
from utils.helpers import preprocess_input_for_sympy

def get_sympy_solution(question):
    """Solve the problem using SymPy."""
    try:
        processed_question = preprocess_input_for_sympy(question)
        if not processed_question:
            logging.error("Failed to preprocess input for SymPy.")
            return None

        logging.info(f"Input for SymPy: {question}")
        logging.info(f"Processed input for SymPy: {processed_question}")


        x = sp.Symbol('x')
        if "differentiate" in processed_question.lower() or "derivative" in processed_question.lower():

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
            logging.warning("No solutions found for the equation.")
            return None

        return (
            f"Step 1: Rewrite the equation.\n"
            f"Equation: {equation}\n"
            f"Step 2: Solve for x.\n"
            f"Solution: {solutions}"
        )
    except sp.SympifyError as e:
        logging.error(f"SymPy parsing error: {e}")
    except Exception as e:
        logging.error(f"SymPy Error: {e}")
    return None

import re
import logging
def preprocess_input_for_sympy(expression):
    """Preprocess input for SymPy."""
    try:
        expression = re.sub(r"(\d+)([a-zA-Z])", r"\1*\2", expression)
        expression = re.sub(r"([a-zA-Z])(\d+)", r"\1*\2", expression)
        expression = re.sub(r"([a-zA-Z])([a-zA-Z])", r"\1*\2", expression)
        # Retain the caret (^) symbol for exponentiation
        if "=" not in expression and "differentiate" not in expression.lower():
            expression = f"{expression} = 0"
        return expression

    except Exception as e:
        logging.error(f"Error preprocessing input: {e}")
        return None

def extract_final_answer(solution):
    """Extract the final answer from the solution."""
    if "*Final Answer:*" in solution:
        return solution.split("*Final Answer:*")[1].strip()
    return solution

def extract_steps(solution):
    """Extract the steps from the solution."""
    if "*Final Answer:*" in solution:
        steps = solution.split("*Final Answer:*")[0].strip()
        return steps
    return solution

def split_steps(solution):
    """Split the steps into a list."""
    if "*Final Answer:*" in solution:
        steps = solution.split("*Final Answer:*")[0].strip()
        return [step.strip() for step in steps.split("\n") if step.strip()]
    return ["No steps available."]

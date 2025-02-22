from flask import Flask, request, jsonify
from sympy import symbols, lambdify
import numpy as np

app = Flask(__name__)

@app.route('/generate_graph')
@app.route('/plot_graph')
def plot_graph():
    import matplotlib.pyplot as plt
    import io
    import base64

    x = np.linspace(-10, 10, 100)
    y = np.sin(x)

    plt.figure()
    plt.plot(x, y)
    plt.title('Sine Wave')
    plt.xlabel('x')
    plt.ylabel('sin(x)')

    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plot_url = base64.b64encode(buf.read()).decode('utf-8')
    plt.close()

    return f'<img src="data:image/png;base64,{plot_url}"/>'

def generate_graph():
    expression = request.args.get('expression')
    x = symbols('x')
    f = lambdify(x, expression, 'numpy')

    x_values = np.linspace(-10, 10, 400)
    y_values = f(x_values)

    return jsonify({'xValues': x_values.tolist(), 'yValues': y_values.tolist()})

from flask import Flask, render_template, request, jsonify
import numpy as np
import matplotlib
matplotlib.use('Agg') 
import matplotlib.pyplot as plt
import warnings
import io
import base64


app = Flask(__name__)

warnings.filterwarnings("ignore", category=RuntimeWarning)

def create_plot(x, y, d1, d2, func_type, func_str):
 
    num_plots = 3 if func_type in ["Triangular", "Sine-like"] else 2
    fig, axes = plt.subplots(num_plots, 1, figsize=(8, 6), sharex=True)
    
    if num_plots == 1:
        axes = [axes]
        
    fig.suptitle(f"Analysis of function: '{func_str}'", fontsize=16)

    # Plot 1: Original Function
    axes[0].plot(x, y, label="Original Function", color='blue')
    axes[0].set_title("Original Function")
    axes[0].grid(True)
    axes[0].legend()

    # Plot 2: First Derivative
    axes[1].plot(x[:-1], d1, label="First Derivative", color='green')
    axes[1].set_title(r"First Derivative ($dy/dx$)")
    axes[1].grid(True)
    axes[1].legend()

    # Plot 3: Second Derivative (if applicable)
    if num_plots == 3:
        axes[2].plot(x[:-2], d2, label="Second Derivative", color='red')
        axes[2].set_title(r"Second Derivative ($d^2y/dx^2$)")
        axes[2].grid(True)
        axes[2].legend()

    plt.xlabel("x")
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    

    buf = io.BytesIO()
    fig.savefig(buf, format='png')
    buf.seek(0)
    
    image_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
    plt.close(fig) 
    return image_base64


@app.route('/')
def index():
    """
    Əsas səhifəni göstərir.
    """
    return render_template('index.html')

@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Frontend-dən gələn funksiyanı analiz edir və nəticəni JSON olaraq qaytarır.
    """
    func_str = request.json.get('function_string', '')
    if not func_str:
        return jsonify({'error': 'Function string is empty.'}), 400

    try:
        scope = {
            "sin": np.sin, "cos": np.cos, "tan": np.tan, "sign": np.sign,
            "abs": np.abs, "sqrt": np.sqrt, "log": np.log, "exp": np.exp,
            "pi": np.pi, "e": np.e, "np": np , "arcsin" : np.arcsin, "arccos" : np.arccos,
            "x": np.linspace(-2, 2, 20000)
        }
        y = eval(func_str, {"__builtins__": {}}, scope)

        if np.all(np.isnan(y)) or np.all(y == y[0]):
             return jsonify({'result_text': f"The function '{func_str}' is CONSTANT or INVALID."})

    except Exception as e:
        return jsonify({'error': f"Error evaluating function: {e}"}), 400

    x_vals = scope['x']
    first_derivative = np.diff(y) / np.diff(x_vals)
    second_derivative = np.diff(first_derivative) / np.diff(x_vals)[:-1]

    first_derivative = np.nan_to_num(first_derivative, nan=0.0, posinf=0.0, neginf=0.0)
    second_derivative = np.nan_to_num(second_derivative, nan=0.0, posinf=0.0, neginf=0.0)

    THRESHOLD = 1000 
    TOLERANCE = 1e-6 
    func_type = ""

    if np.any(np.abs(first_derivative) > THRESHOLD):
        func_type = "Rectangular"
    elif np.any(np.abs(second_derivative) > THRESHOLD):
        func_type = "Triangular"
    
    elif np.std(second_derivative) < TOLERANCE:
       
        if np.mean(np.abs(second_derivative)) < TOLERANCE:
            func_type = "Linear"
        else:
            func_type = "Quadratic" 
    else:
        func_type = "Smooth / Curved"
        

    category_map = {
        "Rectangular": "RECTANGULAR WAVE",
        "Triangular": "TRIANGULAR WAVE",
        "Linear": "LINEAR FUNCTION",
        "Quadratic": "QUADRATIC FUNCTION", 
        "Smooth / Curved": "SINE-LIKE (SMOOTH / CURVED FUNCTION)" 
    }
    result_text = f"The function is classified as: <strong>{category_map.get(func_type, 'Unknown')}</strong>"
    
    
    plot_image = create_plot(x_vals, y, first_derivative, second_derivative, func_type, func_str)
    
    return jsonify({
        'result_text': result_text,
        'plot_image': plot_image
    })

if __name__ == '__main__':
    app.run(debug=True)

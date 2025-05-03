from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from sympy import sympify, SympifyError, sin, cos, tan, pi, diff, integrate, lambdify
import numpy as np
import plotly.graph_objs as go

app = Flask(__name__)
CORS(app)

@app.route('/')
def serve_frontend():
    return send_from_directory('../frontend', 'index.html')

# 處理一般計算功能
@app.route('/calculate', methods=['POST'])
def calculate():
    try:
        data = request.get_json()
        expr = data.get('expression', '')
        angle_mode = data.get('angle_mode', 'deg')

        parsed_expr = sympify(expr, evaluate=False)

        if angle_mode == 'deg':
            parsed_expr = parsed_expr.replace(
                lambda e: e.func in (sin, cos, tan) and e.args,
                lambda e: e.func(e.args[0] * pi / 180)
            )

        result = parsed_expr.evalf()
        return jsonify({'result': str(result)})
    except (SympifyError, ZeroDivisionError):
        return jsonify({'error': '無效的數學表達式'}), 400

# 專用於找出零點與極值
def find_zeros_extrema(expr, x_vals):
    f = lambdify('x', expr, modules=['numpy'])
    try:
        y = f(x_vals)
        y = np.array(y, dtype=np.float64)
    except:
        return []

    points = []
    for i in range(1, len(y) - 1):
        # 零點
        if y[i - 1] * y[i] < 0:
            points.append(('zero', x_vals[i]))
        # 極值
        if (y[i - 1] < y[i] > y[i + 1]) or (y[i - 1] > y[i] < y[i + 1]):
            points.append(('extremum', x_vals[i]))
    return points

# 繪圖處理
@app.route('/plot', methods=['POST'])
def plot():
    try:
        data = request.get_json()
        funcs = data.get('functions', '')
        x_start = float(data.get('x_start', -10))
        x_end = float(data.get('x_end', 10))
        int_start = float(data.get('int_start', 0))
        int_end = float(data.get('int_end', 0))
        angle_mode = data.get('angle_mode', 'deg')
        show_derivative = data.get('show_derivative', False)
        show_points = data.get('show_points', False)

        x_vals = np.linspace(x_start, x_end, 500)
        traces = []
        integrals = []

        for raw_expr in funcs.split(','):
            expr = raw_expr.strip()
            if not expr:
                continue

            parsed = sympify(expr, evaluate=False)

            if angle_mode == 'deg':
                parsed = parsed.replace(
                    lambda e: e.func in (sin, cos, tan) and e.args,
                    lambda e: e.func(e.args[0] * pi / 180)
                )

            # 原始函數圖
            y_vals = [parsed.evalf(subs={'x': x}) if parsed.free_symbols else parsed.evalf()
                      for x in x_vals]
            y_vals = [float(y) if y.is_real else None for y in y_vals]
            traces.append(go.Scatter(x=x_vals.tolist(), y=y_vals, mode='lines', name=expr))

            # 導數圖
            if show_derivative:
                d_expr = diff(parsed, 'x')
                dy_vals = [d_expr.evalf(subs={'x': x}) for x in x_vals]
                dy_vals = [float(y) if y.is_real else None for y in dy_vals]
                traces.append(go.Scatter(
                    x=x_vals.tolist(), y=dy_vals, mode='lines',
                    name=f"d/dx {expr}", line=dict(dash='dot')
                ))

            # 積分區間填色
            if int_start < int_end:
                area_x = np.linspace(int_start, int_end, 200)
                area_y = [parsed.evalf(subs={'x': x}) for x in area_x]
                area_y = [float(y) if y.is_real else None for y in area_y]

                traces.append(go.Scatter(
                    x=area_x.tolist() + [area_x[-1], area_x[0]],
                    y=area_y + [0, 0],
                    fill='toself',
                    fillcolor='rgba(0, 100, 80, 0.2)',
                    line=dict(color='rgba(0,0,0,0)'),
                    name=f"∫ {expr}"
                ))

                int_result = integrate(parsed, ('x', int_start, int_end)).evalf()
                integrals.append({'expr': expr, 'value': str(int_result)})

            # 顯示零點與極值
            if show_points:
                pts = find_zeros_extrema(parsed, x_vals)
                for kind, x0 in pts:
                    y0 = parsed.evalf(subs={'x': x0})
                    if y0.is_real:
                        traces.append(go.Scatter(
                            x=[x0], y=[float(y0)],
                            mode='markers+text',
                            text=[kind],
                            name=f"{kind} of {expr}",
                            marker=dict(symbol='x', size=10)
                        ))

        return jsonify({
            'traces': [t.to_plotly_json() for t in traces],
            'integrals': integrals
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'繪圖發生錯誤：{str(e)}'}), 400

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
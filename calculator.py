import ast
import math
import operator
from typing import TypeAlias

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field


Number: TypeAlias = int | float | complex
MAX_RESULT = 1e100
MAX_POWER = 1000

app = FastAPI(title="Calculator")


class CalculationRequest(BaseModel):
    expression: str = Field(min_length=1, max_length=200)


HTML_PAGE = """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="theme-color" content="#f4f5fb">
  <title>Calculator</title>
  <style>
    :root {
      color-scheme: light;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      font-synthesis: none;
      text-rendering: optimizeLegibility;
      -webkit-font-smoothing: antialiased;
      --ink: #25253a;
      --muted: #9293a6;
      --purple: #7165e8;
      --purple-dark: #5b4fd1;
      --surface: #ffffff;
      --key: #f5f5fa;
    }
    * { box-sizing: border-box; }
    body {
      min-height: 100vh;
      margin: 0;
      display: grid;
      place-items: center;
      padding: 28px 18px;
      color: var(--ink);
      background:
        radial-gradient(ellipse at 15% 15%, #e9e7ff 0, transparent 34%),
        radial-gradient(ellipse at 90% 88%, #e6f3ff 0, transparent 34%),
        #f4f5fb;
    }
    .layout { width: min(100%, 408px); }
    .brand {
      display: flex;
      align-items: center;
      gap: 11px;
      margin: 0 0 18px 5px;
    }
    .brand-mark {
      display: grid;
      width: 38px;
      height: 38px;
      place-items: center;
      border-radius: 12px;
      color: #fff;
      background: var(--purple);
      box-shadow: 0 6px 15px #7165e833;
      font-size: 22px;
      font-weight: 600;
    }
    .brand h1 { margin: 0; font-size: 17px; letter-spacing: -.3px; }
    .brand p { margin: 2px 0 0; color: var(--muted); font-size: 12px; }
    .calculator {
      padding: 22px;
      border: 1px solid #ffffffc9;
      border-radius: 25px;
      background: #ffffffd9;
      box-shadow: 0 24px 65px #31325b17, 0 3px 9px #31325b0a;
      backdrop-filter: blur(14px);
    }
    .screen {
      display: flex;
      min-height: 128px;
      flex-direction: column;
      justify-content: flex-end;
      align-items: flex-end;
      overflow: hidden;
      padding: 10px 4px 23px;
      text-align: right;
    }
    .expression {
      width: 100%;
      min-height: 22px;
      overflow: hidden;
      color: var(--muted);
      font-size: 15px;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .result {
      max-width: 100%;
      overflow: hidden;
      font-size: clamp(38px, 12vw, 54px);
      font-weight: 550;
      letter-spacing: -2.6px;
      line-height: 1.18;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .result.error { color: #d4495b; font-size: 25px; letter-spacing: -.7px; }
    .keypad { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
    button {
      min-width: 0;
      height: 60px;
      border: 0;
      border-radius: 16px;
      color: var(--ink);
      background: var(--key);
      font: inherit;
      font-size: 20px;
      font-weight: 500;
      cursor: pointer;
      transition: transform 100ms ease, background 120ms ease, box-shadow 120ms ease;
      -webkit-tap-highlight-color: transparent;
    }
    button:hover { background: #ececf5; }
    button:active { transform: scale(.96); }
    button:focus-visible { outline: 3px solid #7165e866; outline-offset: 2px; }
    button.utility { color: var(--purple-dark); background: #efedff; font-size: 17px; }
    button.utility:hover { background: #e6e3ff; }
    button.operator {
      color: var(--purple-dark);
      background: #f0efff;
      font-size: 22px;
    }
    button.operator:hover { background: #e5e2ff; }
    button.equals {
      color: white;
      background: var(--purple);
      box-shadow: 0 7px 15px #7165e833;
      font-size: 24px;
    }
    button.equals:hover { background: var(--purple-dark); }
    .status {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 7px;
      margin: 17px 0 0;
      color: var(--muted);
      font-size: 11px;
      letter-spacing: .8px;
    }
    .status-dot { width: 6px; height: 6px; border-radius: 50%; background: #52be83; }
    .hint { margin: 14px 0 0; color: var(--muted); font-size: 12px; text-align: center; }
    @media (max-width: 380px) {
      .calculator { padding: 16px; border-radius: 21px; }
      .keypad { gap: 8px; }
      button { height: 56px; border-radius: 14px; }
      .screen { min-height: 116px; }
    }
  </style>
</head>
<body>
  <main class="layout">
    <header class="brand">
      <div class="brand-mark" aria-hidden="true">±</div>
      <div>
        <h1>Calculator</h1>
        <p>A little clarity in every calculation</p>
      </div>
    </header>
    <section class="calculator" aria-label="Calculator">
      <div class="screen" aria-live="polite" aria-atomic="true">
        <div class="expression" id="expression" aria-label="Expression"></div>
        <div class="result" id="result" aria-label="Result">0</div>
      </div>
      <div class="keypad">
        <button class="utility" data-action="clear" aria-label="Clear all">AC</button>
        <button class="utility" data-value="(" aria-label="Open parenthesis">(</button>
        <button class="utility" data-value=")" aria-label="Close parenthesis">)</button>
        <button class="utility" data-action="backspace" aria-label="Delete last character">⌫</button>

        <button data-value="7">7</button>
        <button data-value="8">8</button>
        <button data-value="9">9</button>
        <button class="operator" data-value="/" aria-label="Divide">÷</button>

        <button data-value="4">4</button>
        <button data-value="5">5</button>
        <button data-value="6">6</button>
        <button class="operator" data-value="*" aria-label="Multiply">×</button>

        <button data-value="1">1</button>
        <button data-value="2">2</button>
        <button data-value="3">3</button>
        <button class="operator" data-value="-" aria-label="Subtract">−</button>

        <button class="utility" data-value="^" aria-label="Exponent">xʸ</button>
        <button data-value="0">0</button>
        <button data-value=".">.</button>
        <button class="operator" data-value="+" aria-label="Add">+</button>

        <button class="equals" data-action="equals" style="grid-column: 1 / -1" aria-label="Calculate">=</button>
      </div>
      <p class="status"><span class="status-dot" aria-hidden="true"></span>FASTAPI CALCULATOR</p>
    </section>
    <p class="hint">Use your keyboard or tap the buttons · Esc clears</p>
  </main>
  <script>
    const expressionOutput = document.getElementById("expression");
    const resultOutput = document.getElementById("result");
    let expression = "";
    let resultShown = false;

    function pretty(value) {
      return value
        .replaceAll("*", "×")
        .replaceAll("/", "÷")
        .replaceAll("-", "−")
        .replaceAll("^", "^")
        .replaceAll("**", "^");
    }

    function render() {
      expressionOutput.textContent = pretty(expression);
      resultOutput.textContent = expression ? pretty(expression) : "0";
      resultOutput.classList.remove("error");
    }

    function append(value) {
      if (resultShown) {
        if (/^[0-9.(]$/.test(value)) {
          expression = "";
        } else if (/^[-+*/%]$/.test(value)) {
          expression = resultOutput.dataset.value || expression;
        }
        resultShown = false;
      }
      expression += value;
      render();
    }

    function clear() {
      expression = "";
      resultShown = false;
      delete resultOutput.dataset.value;
      render();
    }

    function backspace() {
      if (resultShown) {
        expression = "";
        resultShown = false;
        delete resultOutput.dataset.value;
      } else {
        expression = expression.slice(0, -1);
      }
      render();
    }

    async function calculate() {
      if (!expression.trim()) return;
      try {
        const response = await fetch("/api/calculate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ expression })
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Could not calculate this expression.");

        expressionOutput.textContent = pretty(expression) + " =";
        resultOutput.textContent = data.formatted;
        resultOutput.dataset.value = data.formatted;
        resultOutput.classList.remove("error");
        expression = data.formatted;
        resultShown = true;
      } catch (error) {
        resultOutput.textContent = error.message;
        resultOutput.classList.add("error");
        resultShown = false;
      }
    }

    document.querySelector(".keypad").addEventListener("click", (event) => {
      const button = event.target.closest("button");
      if (!button) return;
      if (button.dataset.action === "clear") clear();
      else if (button.dataset.action === "backspace") backspace();
      else if (button.dataset.action === "equals") calculate();
      else append(button.dataset.value);
    });

    document.addEventListener("keydown", (event) => {
      if (/^[0-9.+*/%^()-]$/.test(event.key)) {
        event.preventDefault();
        append(event.key);
      } else if (event.key === "Enter" || event.key === "=") {
        event.preventDefault();
        calculate();
      } else if (event.key === "Backspace") {
        event.preventDefault();
        backspace();
      } else if (event.key === "Escape") {
        clear();
      }
    });
  </script>
</body>
</html>
"""


def _checked_number(value: Number) -> float:
    if isinstance(value, complex):
        raise ValueError("Complex results are not supported.")
    result = float(value)
    if not math.isfinite(result) or abs(result) > MAX_RESULT:
        raise ValueError("Result is outside the supported range.")
    return result


def _evaluate_node(node: ast.expr) -> float:
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        if isinstance(node.value, bool):
            raise ValueError("Unsupported value.")
        return _checked_number(node.value)

    if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
        operand = _evaluate_node(node.operand)
        return _checked_number(operand if isinstance(node.op, ast.UAdd) else -operand)

    if isinstance(node, ast.BinOp):
        left = _evaluate_node(node.left)
        right = _evaluate_node(node.right)
        operations = {
            ast.Add: operator.add,
            ast.Sub: operator.sub,
            ast.Mult: operator.mul,
            ast.Div: operator.truediv,
            ast.FloorDiv: operator.floordiv,
            ast.Mod: operator.mod,
            ast.Pow: operator.pow,
        }
        operation = operations.get(type(node.op))
        if operation is None:
            raise ValueError("That operator is not supported.")
        if isinstance(node.op, ast.Pow) and abs(right) > MAX_POWER:
            raise ValueError("Exponent is outside the supported range.")
        return _checked_number(operation(left, right))

    raise ValueError("Only basic arithmetic expressions are supported.")


def _normalize_expression(expression: str) -> str:
    normalized = expression.strip()
    if not normalized:
        return normalized
    return normalized.replace("^", "**")


def evaluate_expression(expression: str) -> float:
    try:
        parsed = ast.parse(_normalize_expression(expression), mode="eval")
    except SyntaxError as error:
        raise ValueError("Enter a valid arithmetic expression.") from error
    return _evaluate_node(parsed.body)


@app.get("/", response_class=HTMLResponse)
async def home() -> HTMLResponse:
    return HTMLResponse(content=HTML_PAGE)


@app.post("/api/calculate")
async def calculate(request: CalculationRequest) -> dict[str, float | str]:
    try:
        result = evaluate_expression(request.expression)
    except (ValueError, ZeroDivisionError, OverflowError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error

    if result == 0:
        result = 0.0
    return {"result": result, "formatted": format(result, ".12g")}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("calculator:app", host="127.0.0.1", port=8000, reload=True)

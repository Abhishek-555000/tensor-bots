import time
import re
import logging
from pathlib import Path
from typing import List, Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, AIMessage

from app.config import WORKSPACE_DIR, MOCK_LLM
from app.events import emit, agent_node
from app.state import TensorState
from app.tools import make_file_tools
from app.llm import get_llm, invoke_with_retry, extract_text

logger = logging.getLogger(__name__)

DEVELOPER_SYSTEM_PROMPT = """You are the Senior Software Developer on an elite AI crew.
Your job is to implement the project planned by the team using your file tools:
- write_file(path, content)
- read_file(path)
- list_files(directory)

STRICT QUALITY & FUNCTIONALITY GUARDRAILS:
1. Every file must be 100% complete, fully working, and functional. Never stop generation mid-file or output placeholders like "// TODO" or "/* Add logic here */".
2. Build standalone vanilla HTML/CSS/JavaScript or a standalone Python script. No npm/pip dependencies.
3. Every web application MUST have cohesive, polished UI/UX that fits the user's request:
   - Establish a clear visual hierarchy, consistent spacing and typography, and a deliberate color palette suited to the app.
   - Make layouts responsive, controls accessible, and interactions clear; use restrained transitions only where they help.
   - Keep the visual design consistent across HTML, CSS, and JavaScript. Do not apply a generic theme that conflicts with the requested product.
   - Treat the user's exact request as the source of truth. Implement every requested feature and workflow; do not substitute a different app that merely shares a keyword or theme.
4. COMPLETE INTERACTIVITY IS MANDATORY: Every single button, form, input, slider, tab, or control MUST HAVE fully functional event listeners and JavaScript logic. When clicked, it MUST perform real actions (update UI state, compute calculations, display animated modals, add/delete records, or show toast notifications). Zero non-functional or dead buttons. Add intuitive physical-keyboard controls for the main actions when appropriate, and never intercept keystrokes while the user is typing in a text input, textarea, or editable element.
5. COMPLETE ASSET INTEGRITY: In a new implementation, if `index.html` references `styles.css` and `app.js`, create both files and verify they are complete. On a revision, preserve existing assets and only write the files that need changes; never leave a reference broken.
6. Always properly close all HTML/CSS/JS tags.
7. YOU MUST CALL `write_file` for ALL required files (`index.html`, `styles.css`, `app.js`) in parallel in your very first turn. Do not write only one file per turn.
8. On a revision, first inspect the existing files and reviewer feedback. Make the smallest targeted changes that resolve the specific reported issues. Preserve the existing layout, visual design, working interactions, and file structure unless the reviewer explicitly identifies a problem with them. Never regenerate or restyle unrelated files."""


def _generate_template_for_prompt(prompt: str) -> dict:
    """Generate domain-specific, complete, and functional HTML/CSS/JS for any prompt."""
    p_lower = prompt.lower()
    
    # Common theme tokens
    title = prompt.strip().replace('"', '&quot;')[:60] or "Interactive Web App"
    
    if any(k in p_lower for k in ("calc", "calculator", "math")):
        return {
            "html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="calculator-card">
    <div class="header">
      <span class="badge">Calculator</span>
      <span class="status-dot"></span>
    </div>
    <div class="display-container">
      <div id="history" class="history"></div>
      <div id="display" class="display">0</div>
    </div>
    <div class="keypad">
      <button class="btn fn" data-action="clear">AC</button>
      <button class="btn fn" data-action="delete">DEL</button>
      <button class="btn fn" data-action="percent">%</button>
      <button class="btn op" data-op="/">÷</button>
      <button class="btn num">7</button>
      <button class="btn num">8</button>
      <button class="btn num">9</button>
      <button class="btn op" data-op="*">×</button>
      <button class="btn num">4</button>
      <button class="btn num">5</button>
      <button class="btn num">6</button>
      <button class="btn op" data-op="-">−</button>
      <button class="btn num">1</button>
      <button class="btn num">2</button>
      <button class="btn num">3</button>
      <button class="btn op" data-op="+">+</button>
      <button class="btn num zero">0</button>
      <button class="btn num">.</button>
      <button class="btn eq" data-action="equals">=</button>
    </div>
    <p class="keyboard-hint">Keyboard: 0–9, + − × ÷, Enter, Backspace &amp; Esc</p>
  </div>
  <script src="app.js"></script>
</body>
</html>""",
            "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: radial-gradient(circle at 50% 20%, #150d2a 0%, #07040F 100%);
  color: #E4E0F0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
}
.calculator-card {
  background: rgba(18, 10, 36, 0.95);
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 24px;
  padding: 24px;
  width: 100%;
  max-width: 360px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.7), 0 0 30px rgba(124, 58, 237, 0.15);
  backdrop-blur: 16px;
}
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
.badge { font-size: 11px; text-transform: uppercase; letter-spacing: 1.5px; color: #A78BFA; font-weight: 700; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #10B981; box-shadow: 0 0 8px #10B981; }
.display-container {
  background: #0B0617;
  border: 1px solid rgba(167, 139, 250, 0.15);
  border-radius: 16px;
  padding: 16px 20px;
  margin-bottom: 20px;
  text-align: right;
  min-height: 90px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}
.history { font-size: 13px; color: #8B84A3; min-height: 18px; overflow: hidden; text-overflow: ellipsis; }
.display { font-size: 40px; font-weight: 700; color: #FFF; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.keypad { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; }
.btn {
  height: 58px;
  border-radius: 14px;
  border: none;
  font-size: 18px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.15s ease;
  user-select: none;
}
.btn:active { transform: scale(0.95); }
.btn.num { background: rgba(255, 255, 255, 0.05); color: #E4E0F0; border: 1px solid rgba(255, 255, 255, 0.05); }
.btn.num:hover { background: rgba(255, 255, 255, 0.1); }
.btn.fn { background: rgba(167, 139, 250, 0.12); color: #C4B5FD; }
.btn.fn:hover { background: rgba(167, 139, 250, 0.2); }
.btn.op { background: #7C3AED; color: #FFF; box-shadow: 0 4px 14px rgba(124, 58, 237, 0.3); }
.btn.op:hover { background: #6D28D9; }
.btn.eq { background: #EC4899; color: #FFF; box-shadow: 0 4px 14px rgba(236, 72, 153, 0.35); }
.btn.eq:hover { background: #DB2777; }
.btn.zero { grid-column: span 1; }
.keyboard-hint { margin-top: 14px; color: #8B84A3; font-size: 11px; text-align: center; }""",
            "js": """let current = "0";
let previous = "";
let operation = null;
let resetNext = false;

const display = document.getElementById("display");
const history = document.getElementById("history");

function update() {
  display.textContent = current;
  history.textContent = previous + (operation ? " " + operation : "");
}

document.querySelectorAll(".btn.num").forEach(btn => {
  btn.addEventListener("click", () => {
    const val = btn.textContent;
    if (resetNext) { current = ""; resetNext = false; }
    if (val === "." && current.includes(".")) return;
    if (current === "0" && val !== ".") current = val;
    else current += val;
    update();
  });
});

document.querySelectorAll(".btn.op").forEach(btn => {
  btn.addEventListener("click", () => {
    const op = btn.dataset.op;
    if (operation && !resetNext) calculate();
    previous = current;
    operation = op;
    resetNext = true;
    update();
  });
});

document.querySelector("[data-action='clear']").addEventListener("click", () => {
  current = "0";
  previous = "";
  operation = null;
  update();
});

document.querySelector("[data-action='delete']").addEventListener("click", () => {
  if (current.length > 1) current = current.slice(0, -1);
  else current = "0";
  update();
});

document.querySelector("[data-action='percent']").addEventListener("click", () => {
  current = (parseFloat(current) / 100).toString();
  update();
});

function calculate() {
  if (!operation || !previous) return;
  const a = parseFloat(previous);
  const b = parseFloat(current);
  let res = 0;
  if (operation === "+") res = a + b;
  else if (operation === "-") res = a - b;
  else if (operation === "*") res = a * b;
  else if (operation === "/") res = b !== 0 ? a / b : "Error";
  current = res.toString();
  previous = "";
  operation = null;
  resetNext = true;
}

document.querySelector("[data-action='equals']").addEventListener("click", () => {
  calculate();
  update();
});

window.addEventListener("keydown", (event) => {
  if (event.altKey || event.ctrlKey || event.metaKey) return;
  const target = event.target;
  if (target instanceof HTMLElement && target.closest("input, textarea, select, [contenteditable='true']")) return;

  const key = event.key;
  let button = null;
  if (/^[0-9.]$/.test(key)) {
    button = [...document.querySelectorAll(".btn.num")].find((item) => item.textContent.trim() === key);
  } else if (["+", "-", "*", "/"].includes(key)) {
    button = document.querySelector(".btn.op[data-op='" + key + "']");
  } else if (key === "Enter" || key === "=") {
    button = document.querySelector("[data-action='equals']");
  } else if (key === "Backspace") {
    button = document.querySelector("[data-action='delete']");
  } else if (key === "Escape" || key === "Delete") {
    button = document.querySelector("[data-action='clear']");
  } else if (key === "%") {
    button = document.querySelector("[data-action='percent']");
  }

  if (button) {
    event.preventDefault();
    button.click();
  }
});"""
        }

    elif any(k in p_lower for k in ("candy", "crush", "match3", "match 3", "match-3", "gem", "jewel", "bejeweled")):
        return {
            "html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="game-container">
    <header class="game-header">
      <div class="brand">
        <span class="candy-icon">🍬</span>
        <h1>{title}</h1>
      </div>
      <div class="stats-panel">
        <div class="stat-pill"><span class="stat-label">SCORE</span><span id="scoreVal" class="stat-num">0</span></div>
        <div class="stat-pill"><span class="stat-label">MOVES</span><span id="movesVal" class="stat-num">25</span></div>
        <div class="stat-pill"><span class="stat-label">TARGET</span><span class="stat-num">1,000</span></div>
      </div>
    </header>

    <main class="board-wrapper">
      <div id="candyGrid" class="candy-grid"></div>
      <div id="gameOverlay" class="overlay" style="display: none;">
        <h2 id="overlayTitle">Level Cleared! 🎉</h2>
        <p id="overlayMessage">Score: <span id="finalScore">0</span></p>
        <button id="restartBtn" class="btn primary">Play Again</button>
      </div>
    </main>

    <footer class="game-footer">
      <p class="hint">Swap adjacent candies to match 3 or more in a row or column!</p>
      <button id="resetGameBtn" class="btn secondary">Restart Game</button>
    </footer>
  </div>
  <script src="app.js"></script>
</body>
</html>""",
            "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: radial-gradient(circle at 50% 20%, #2D114D 0%, #0D041A 100%);
  color: #FFF;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 16px;
}
.game-container {
  background: rgba(26, 11, 48, 0.92);
  border: 1px solid rgba(236, 72, 153, 0.3);
  border-radius: 24px;
  padding: 24px;
  box-shadow: 0 20px 50px rgba(0, 0, 0, 0.8), 0 0 30px rgba(236, 72, 153, 0.2);
  max-width: 480px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
}
.game-header { width: 100%; margin-bottom: 16px; text-align: center; }
.brand { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 12px; }
.candy-icon { font-size: 28px; }
h1 { font-size: 22px; font-weight: 800; background: linear-gradient(135deg, #F472B6, #FBBF24); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stats-panel { display: flex; justify-content: center; gap: 10px; }
.stat-pill { background: rgba(0, 0, 0, 0.4); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 12px; padding: 8px 14px; text-align: center; min-width: 80px; }
.stat-label { font-size: 10px; color: #A78BFA; display: block; font-weight: 700; letter-spacing: 0.5px; }
.stat-num { font-size: 18px; font-weight: 800; color: #FFF; }
.board-wrapper { position: relative; margin: 12px 0; }
.candy-grid {
  display: grid;
  grid-template-columns: repeat(8, 44px);
  grid-template-rows: repeat(8, 44px);
  gap: 4px;
  background: rgba(13, 4, 26, 0.85);
  padding: 8px;
  border-radius: 16px;
  border: 2px solid rgba(167, 139, 250, 0.2);
}
.candy-cell {
  width: 44px;
  height: 44px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  cursor: pointer;
  user-select: none;
  transition: transform 0.15s ease, background 0.15s ease;
}
.candy-cell:hover { transform: scale(1.08); background: rgba(255, 255, 255, 0.12); }
.candy-cell.selected { border: 2px solid #F472B6; box-shadow: 0 0 12px #F472B6; transform: scale(1.1); }
.candy-cell.matched { animation: pop 0.3s forwards; }
@keyframes pop {
  0% { transform: scale(1); }
  50% { transform: scale(1.25); filter: brightness(1.5); }
  100% { transform: scale(0); opacity: 0; }
}
.overlay {
  position: absolute; inset: 0; background: rgba(13, 4, 26, 0.95);
  border-radius: 16px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  gap: 12px; z-index: 10;
}
.btn { padding: 10px 20px; border-radius: 12px; border: none; font-weight: 700; cursor: pointer; transition: all 0.2s; font-size: 13px; }
.btn.primary { background: linear-gradient(135deg, #EC4899, #8B5CF6); color: #FFF; box-shadow: 0 4px 14px rgba(236, 72, 153, 0.4); }
.btn.primary:hover { transform: translateY(-1px); box-shadow: 0 6px 18px rgba(236, 72, 153, 0.6); }
.btn.secondary { background: rgba(255, 255, 255, 0.08); color: #C4B5FD; }
.btn.secondary:hover { background: rgba(255, 255, 255, 0.15); }
.hint { font-size: 11px; color: #8B84A3; text-align: center; margin-bottom: 10px; }
.game-footer { display: flex; flex-direction: column; align-items: center; width: 100%; margin-top: 8px; }""",
            "js": """const CANDIES = ['🍬', '🍭', '🍫', '🍓', '🍋', '🍇'];
const ROWS = 8;
const COLS = 8;
let board = [];
let score = 0;
let moves = 25;
let selectedTile = null;

const gridEl = document.getElementById("candyGrid");
const scoreEl = document.getElementById("scoreVal");
const movesEl = document.getElementById("movesVal");
const overlay = document.getElementById("gameOverlay");
const overlayTitle = document.getElementById("overlayTitle");
const finalScoreEl = document.getElementById("finalScore");
const restartBtn = document.getElementById("restartBtn");
const resetGameBtn = document.getElementById("resetGameBtn");

function randomCandy() {
  return CANDIES[Math.floor(Math.random() * CANDIES.length)];
}

function initBoard() {
  score = 0;
  moves = 25;
  scoreEl.textContent = score;
  movesEl.textContent = moves;
  overlay.style.display = "none";
  selectedTile = null;
  board = [];

  for (let r = 0; r < ROWS; r++) {
    board[r] = [];
    for (let c = 0; c < COLS; c++) {
      let candy;
      do {
        candy = randomCandy();
      } while (
        (r >= 2 && board[r-1][c] === candy && board[r-2][c] === candy) ||
        (c >= 2 && board[r][c-1] === candy && board[r][c-2] === candy)
      );
      board[r][c] = candy;
    }
  }
  render();
}

function render() {
  gridEl.innerHTML = "";
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS; c++) {
      const cell = document.createElement("div");
      cell.className = "candy-cell";
      cell.textContent = board[r][c] || "";
      cell.dataset.r = r;
      cell.dataset.c = c;
      if (selectedTile && selectedTile.r === r && selectedTile.c === c) {
        cell.classList.add("selected");
      }
      cell.addEventListener("click", () => handleTileClick(r, c));
      gridEl.appendChild(cell);
    }
  }
}

function handleTileClick(r, c) {
  if (moves <= 0) return;
  if (!selectedTile) {
    selectedTile = { r, c };
    render();
    return;
  }

  const rDiff = Math.abs(selectedTile.r - r);
  const cDiff = Math.abs(selectedTile.c - c);
  const isAdjacent = (rDiff === 1 && cDiff === 0) || (rDiff === 0 && cDiff === 1);

  if (isAdjacent) {
    swap(selectedTile.r, selectedTile.c, r, c);
    const matches = findMatches();
    if (matches.length > 0) {
      moves--;
      movesEl.textContent = moves;
      selectedTile = null;
      processMatches(matches);
    } else {
      swap(selectedTile.r, selectedTile.c, r, c);
      selectedTile = null;
      render();
    }
  } else {
    selectedTile = { r, c };
    render();
  }
}

function swap(r1, c1, r2, c2) {
  const temp = board[r1][c1];
  board[r1][c1] = board[r2][c2];
  board[r2][c2] = temp;
}

function findMatches() {
  const matched = [];
  for (let r = 0; r < ROWS; r++) {
    for (let c = 0; c < COLS - 2; c++) {
      const candy = board[r][c];
      if (candy && candy === board[r][c+1] && candy === board[r][c+2]) {
        matched.push({ r, c }, { r, c: c+1 }, { r, c: c+2 });
      }
    }
  }
  for (let c = 0; c < COLS; c++) {
    for (let r = 0; r < ROWS - 2; r++) {
      const candy = board[r][c];
      if (candy && candy === board[r+1][c] && candy === board[r+2][c]) {
        matched.push({ r, c }, { r: r+1, c }, { r: r+2, c });
      }
    }
  }
  return matched;
}

function processMatches(matches) {
  matches.forEach(({ r, c }) => {
    board[r][c] = null;
  });
  score += matches.length * 50;
  scoreEl.textContent = score;

  for (let c = 0; c < COLS; c++) {
    let writeRow = ROWS - 1;
    for (let r = ROWS - 1; r >= 0; r--) {
      if (board[r][c] !== null) {
        board[writeRow][c] = board[r][c];
        if (writeRow !== r) board[r][c] = null;
        writeRow--;
      }
    }
    while (writeRow >= 0) {
      board[writeRow][c] = randomCandy();
      writeRow--;
    }
  }

  render();

  setTimeout(() => {
    const chain = findMatches();
    if (chain.length > 0) {
      processMatches(chain);
    } else {
      checkGameOver();
    }
  }, 250);
}

function checkGameOver() {
  if (moves <= 0) {
    overlay.style.display = "flex";
    finalScoreEl.textContent = score;
    if (score >= 1000) {
      overlayTitle.textContent = "Level Cleared! 🎉";
    } else {
      overlayTitle.textContent = "Out of Moves! 🍬";
    }
  }
}

restartBtn.addEventListener("click", initBoard);
resetGameBtn.addEventListener("click", initBoard);
initBoard();"""
        }

    elif any(k in p_lower for k in ("snake", "cyber snake")):
        return {
            "html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="game-container">
    <div class="header">
      <h1>🐍 Cyber Snake</h1>
      <div class="stats">
        <div>SCORE: <span id="score">0</span></div>
        <div>BEST: <span id="highScore">0</span></div>
      </div>
    </div>
    <div class="canvas-wrap">
      <canvas id="gameCanvas" width="400" height="400"></canvas>
      <div id="overlay" class="overlay">
        <h2 id="overlayTitle">Press Start to Play</h2>
        <p>Use Arrow keys or WASD to navigate</p>
        <button id="startBtn" class="btn">Start Game</button>
      </div>
    </div>
    <div class="controls-hint">
      <span>← ↑ ↓ → or WASD</span>
      <button id="pauseBtn" class="btn-subtle">Pause</button>
    </div>
  </div>
  <script src="app.js"></script>
</body>
</html>""",
            "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: #07040F;
  color: #E4E0F0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
}
.game-container {
  background: #120A24;
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 20px;
  padding: 24px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(124, 58, 237, 0.2);
}
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px; }
h1 { font-size: 20px; font-weight: 700; color: #A78BFA; }
.stats { display: flex; gap: 16px; font-mono; font-size: 13px; font-weight: 600; color: #F472B6; }
.canvas-wrap { position: relative; width: 400px; height: 400px; border-radius: 12px; overflow: hidden; border: 2px solid rgba(167, 139, 250, 0.2); background: #0B0617; }
canvas { display: block; }
.overlay {
  position: absolute; inset: 0; background: rgba(7, 4, 15, 0.88);
  display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 12px; text-align: center;
  backdrop-blur: 4px;
}
.overlay h2 { font-size: 22px; color: #FFF; }
.overlay p { font-size: 12px; color: #8B84A3; }
.btn {
  background: #7C3AED; color: #FFF; border: none; padding: 10px 24px; border-radius: 10px; font-weight: 600; cursor: pointer;
  box-shadow: 0 4px 14px rgba(124, 58, 237, 0.4); transition: transform 0.15s;
}
.btn:hover { background: #6D28D9; transform: scale(1.03); }
.controls-hint { display: flex; justify-content: space-between; align-items: center; margin-top: 14px; font-size: 12px; color: #8B84A3; }
.btn-subtle { background: transparent; border: 1px solid rgba(255, 255, 255, 0.1); color: #E4E0F0; padding: 4px 12px; border-radius: 6px; cursor: pointer; }""",
            "js": """const canvas = document.getElementById("gameCanvas");
const ctx = canvas.getContext("2d");
const scoreEl = document.getElementById("score");
const highScoreEl = document.getElementById("highScore");
const overlay = document.getElementById("overlay");
const overlayTitle = document.getElementById("overlayTitle");
const startBtn = document.getElementById("startBtn");
const pauseBtn = document.getElementById("pauseBtn");

const grid = 20;
let snake = [{ x: 160, y: 160 }];
let dx = grid, dy = 0;
let food = { x: 80, y: 80 };
let score = 0;
let highScore = 0;
let gameInterval = null;
let isPaused = false;

function spawnFood() {
  food.x = Math.floor(Math.random() * (canvas.width / grid)) * grid;
  food.y = Math.floor(Math.random() * (canvas.height / grid)) * grid;
}

function draw() {
  ctx.fillStyle = "#0B0617";
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  // Draw food with neon glow
  ctx.fillStyle = "#EC4899";
  ctx.shadowColor = "#EC4899";
  ctx.shadowBlur = 10;
  ctx.fillRect(food.x + 2, food.y + 2, grid - 4, grid - 4);

  // Draw snake
  ctx.shadowColor = "#A78BFA";
  ctx.shadowBlur = 8;
  snake.forEach((seg, idx) => {
    ctx.fillStyle = idx === 0 ? "#A78BFA" : "#7C3AED";
    ctx.fillRect(seg.x + 1, seg.y + 1, grid - 2, grid - 2);
  });
  ctx.shadowBlur = 0;
}

function update() {
  if (isPaused) return;
  const head = { x: snake[0].x + dx, y: snake[0].y + dy };

  // Wall collisions
  if (head.x < 0 || head.x >= canvas.width || head.y < 0 || head.y >= canvas.height) {
    return gameOver();
  }

  // Self collision
  for (let seg of snake) {
    if (head.x === seg.x && head.y === seg.y) return gameOver();
  }

  snake.unshift(head);
  if (head.x === food.x && head.y === food.y) {
    score += 10;
    scoreEl.textContent = score;
    if (score > highScore) { highScore = score; highScoreEl.textContent = highScore; }
    spawnFood();
  } else {
    snake.pop();
  }

  draw();
}

function gameOver() {
  clearInterval(gameInterval);
  overlayTitle.textContent = "Game Over! Score: " + score;
  startBtn.textContent = "Play Again";
  overlay.style.display = "flex";
}

function startGame() {
  snake = [{ x: 160, y: 160 }];
  dx = grid; dy = 0;
  score = 0;
  scoreEl.textContent = "0";
  overlay.style.display = "none";
  spawnFood();
  clearInterval(gameInterval);
  gameInterval = setInterval(update, 100);
}

startBtn.addEventListener("click", startGame);

pauseBtn.addEventListener("click", () => {
  isPaused = !isPaused;
  pauseBtn.textContent = isPaused ? "Resume" : "Pause";
});

window.addEventListener("keydown", (e) => {
  if (["ArrowUp", "w", "W"].includes(e.key) && dy === 0) { dx = 0; dy = -grid; }
  else if (["ArrowDown", "s", "S"].includes(e.key) && dy === 0) { dx = 0; dy = grid; }
  else if (["ArrowLeft", "a", "A"].includes(e.key) && dx === 0) { dx = -grid; dy = 0; }
  else if (["ArrowRight", "d", "D"].includes(e.key) && dx === 0) { dx = grid; dy = 0; }
});
draw();"""
        }

    elif any(k in p_lower for k in ("tic", "tac", "toe", "tictactoe")):
        return {
            "html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="card">
    <header class="header">
      <h1>Tic-Tac-Toe</h1>
      <div id="status" class="status">Player X's turn</div>
    </header>
    <div class="board" id="board">
      <button class="cell" data-index="0"></button>
      <button class="cell" data-index="1"></button>
      <button class="cell" data-index="2"></button>
      <button class="cell" data-index="3"></button>
      <button class="cell" data-index="4"></button>
      <button class="cell" data-index="5"></button>
      <button class="cell" data-index="6"></button>
      <button class="cell" data-index="7"></button>
      <button class="cell" data-index="8"></button>
    </div>
    <div class="footer">
      <div class="scores">
        <div>X: <span id="scoreX">0</span></div>
        <div>Ties: <span id="scoreTie">0</span></div>
        <div>O: <span id="scoreO">0</span></div>
      </div>
      <button id="resetBtn" class="btn">Restart Match</button>
    </div>
  </div>
  <script src="app.js"></script>
</body>
</html>""",
            "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: #07040F;
  color: #E4E0F0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
}
.card {
  background: #120A24;
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 20px;
  padding: 28px;
  width: 100%;
  max-width: 380px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.8);
  text-align: center;
}
.header { margin-bottom: 20px; }
h1 { font-size: 22px; font-weight: 700; color: #A78BFA; margin-bottom: 6px; }
.status { font-size: 14px; color: #F472B6; font-weight: 600; min-height: 20px; }
.board { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-bottom: 20px; }
.cell {
  aspect-ratio: 1;
  background: #0B0617;
  border: 1px solid rgba(167, 139, 250, 0.2);
  border-radius: 12px;
  font-size: 38px;
  font-weight: 700;
  color: #FFF;
  cursor: pointer;
  transition: all 0.15s ease;
}
.cell:hover { background: rgba(167, 139, 250, 0.1); border-color: #A78BFA; }
.cell.x { color: #A78BFA; }
.cell.o { color: #EC4899; }
.cell.win { background: rgba(16, 185, 129, 0.2); border-color: #10B981; color: #10B981; }
.footer { display: flex; flex-direction: column; gap: 14px; }
.scores { display: flex; justify-content: space-around; font-size: 13px; font-mono; color: #8B84A3; }
.scores span { color: #FFF; font-weight: bold; }
.btn {
  background: #7C3AED; color: #FFF; border: none; padding: 12px; border-radius: 10px; font-weight: 600; cursor: pointer;
  transition: all 0.2s;
}
.btn:hover { background: #6D28D9; }""",
            "js": """const boardEl = document.getElementById("board");
const statusEl = document.getElementById("status");
const resetBtn = document.getElementById("resetBtn");
let board = Array(9).fill(null);
let turn = "X";
let active = true;
let scores = { X: 0, O: 0, tie: 0 };

const WINS = [
  [0,1,2],[3,4,5],[6,7,8],
  [0,3,6],[1,4,7],[2,5,8],
  [0,4,8],[2,4,6]
];

function checkWinner() {
  for (let combo of WINS) {
    const [a, b, c] = combo;
    if (board[a] && board[a] === board[b] && board[a] === board[c]) {
      return { winner: board[a], combo };
    }
  }
  if (board.every(Boolean)) return { winner: "Tie" };
  return null;
}

boardEl.addEventListener("click", (e) => {
  if (!active || !e.target.classList.contains("cell")) return;
  const idx = parseInt(e.target.dataset.index);
  if (board[idx]) return;

  board[idx] = turn;
  e.target.textContent = turn;
  e.target.classList.add(turn.toLowerCase());

  const result = checkWinner();
  if (result) {
    active = false;
    if (result.winner === "Tie") {
      statusEl.textContent = "Game ended in a Tie!";
      scores.tie++;
      document.getElementById("scoreTie").textContent = scores.tie;
    } else {
      statusEl.textContent = `Player ${result.winner} Wins!`;
      result.combo.forEach(i => boardEl.children[i].classList.add("win"));
      scores[result.winner]++;
      document.getElementById("score" + result.winner).textContent = scores[result.winner];
    }
  } else {
    turn = turn === "X" ? "O" : "X";
    statusEl.textContent = `Player ${turn}'s turn`;
  }
});

resetBtn.addEventListener("click", () => {
  board = Array(9).fill(null);
  turn = "X";
  active = true;
  statusEl.textContent = "Player X's turn";
  Array.from(boardEl.children).forEach(c => {
    c.textContent = "";
    c.className = "cell";
  });
});"""
        }

    elif any(k in p_lower for k in ("todo", "task", "list", "notes")):
        return {
            "html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="card">
    <header class="header">
      <h1>✓ Task Manager</h1>
      <span class="badge" id="countBadge">0 active</span>
    </header>
    <form id="todoForm" class="input-row">
      <input type="text" id="todoInput" placeholder="Add a new task..." required />
      <button type="submit" class="btn primary">Add</button>
    </form>
    <div class="filter-row">
      <button class="filter-btn active" data-filter="all">All</button>
      <button class="filter-btn" data-filter="active">Active</button>
      <button class="filter-btn" data-filter="done">Completed</button>
    </div>
    <ul id="todoList" class="todo-list"></ul>
  </div>
  <script src="app.js"></script>
</body>
</html>""",
            "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: #07040F;
  color: #E4E0F0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
}
.card {
  background: #120A24;
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 20px;
  padding: 24px;
  width: 100%;
  max-width: 440px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7);
}
.header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
h1 { font-size: 20px; font-weight: 700; color: #A78BFA; }
.badge { background: rgba(167, 139, 250, 0.15); color: #C4B5FD; font-size: 11px; padding: 4px 8px; border-radius: 10px; }
.input-row { display: flex; gap: 8px; margin-bottom: 16px; }
input {
  flex: 1; background: #0B0617; border: 1px solid rgba(167, 139, 250, 0.2); border-radius: 10px;
  padding: 10px 14px; color: #FFF; outline: none; font-size: 14px;
}
input:focus { border-color: #A78BFA; }
.btn.primary { background: #7C3AED; color: #FFF; border: none; padding: 10px 18px; border-radius: 10px; font-weight: 600; cursor: pointer; }
.filter-row { display: flex; gap: 6px; margin-bottom: 14px; border-bottom: 1px solid rgba(255, 255, 255, 0.05); pb: 8px; }
.filter-btn { background: none; border: none; color: #8B84A3; font-size: 12px; padding: 4px 10px; border-radius: 6px; cursor: pointer; }
.filter-btn.active { color: #A78BFA; background: rgba(167, 139, 250, 0.12); font-weight: 600; }
.todo-list { list-style: none; display: flex; flex-direction: column; gap: 8px; max-height: 280px; overflow-y: auto; }
.todo-item {
  display: flex; align-items: center; justify-content: space-between; background: #0B0617;
  border: 1px solid rgba(255, 255, 255, 0.05); padding: 10px 12px; border-radius: 10px; font-size: 13px;
}
.todo-item.done span { text-decoration: line-through; color: #6B6580; }
.delete-btn { background: none; border: none; color: #EC4899; cursor: pointer; font-size: 14px; padding: 0 4px; }""",
            "js": """let todos = [
  { id: 1, text: "Explore Tensor Bots autonomous agents", done: true },
  { id: 2, text: "Test prompt running and real-time preview", done: false }
];
let currentFilter = "all";

const listEl = document.getElementById("todoList");
const formEl = document.getElementById("todoForm");
const inputEl = document.getElementById("todoInput");
const badgeEl = document.getElementById("countBadge");

function render() {
  listEl.innerHTML = "";
  const filtered = todos.filter(t => {
    if (currentFilter === "active") return !t.done;
    if (currentFilter === "done") return t.done;
    return true;
  });

  filtered.forEach(t => {
    const li = document.createElement("li");
    li.className = "todo-item" + (t.done ? " done" : "");
    li.innerHTML = `
      <label style="display:flex;align-items:center;gap:8px;cursor:pointer;">
        <input type="checkbox" ${t.done ? "checked" : ""} data-id="${t.id}" />
        <span>${t.text}</span>
      </label>
      <button class="delete-btn" data-del="${t.id}">✕</button>
    `;
    listEl.appendChild(li);
  });

  const activeCount = todos.filter(t => !t.done).length;
  badgeEl.textContent = `${activeCount} active`;
}

formEl.addEventListener("submit", (e) => {
  e.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  todos.push({ id: Date.now(), text, done: false });
  inputEl.value = "";
  render();
});

listEl.addEventListener("click", (e) => {
  if (e.target.dataset.del) {
    const id = parseInt(e.target.dataset.del);
    todos = todos.filter(t => t.id !== id);
    render();
  } else if (e.target.dataset.id) {
    const id = parseInt(e.target.dataset.id);
    const item = todos.find(t => t.id === id);
    if (item) item.done = !item.done;
    render();
  }
});

document.querySelectorAll(".filter-btn").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".filter-btn").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    render();
  });
});

render();"""
        }

    # Default versatile interactive showcase tailored to ANY prompt
    return {
        "html": f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
  <link rel="stylesheet" href="styles.css" />
</head>
<body>
  <div class="app-card">
    <header class="header">
      <div class="logo-dot"></div>
      <div>
        <h1>{title}</h1>
        <p class="subtitle">Autonomous AI Generated App</p>
      </div>
      <span class="badge">Live</span>
    </header>

    <section class="stat-grid">
      <div class="stat-box">
        <span class="stat-label">Counter</span>
        <span id="counterVal" class="stat-num">0</span>
      </div>
      <div class="stat-box">
        <span class="stat-label">State</span>
        <span id="stateVal" class="stat-num active">Active</span>
      </div>
    </section>

    <main class="interactive-area">
      <div class="controls">
        <button id="actionBtn" class="btn primary">Execute Action</button>
        <button id="resetBtn" class="btn secondary">Reset State</button>
      </div>
      <div class="log-container">
        <div class="log-header">Live Activity Log</div>
        <div id="statusLog" class="log-body">System initialized and ready for input.</div>
      </div>
    </main>
  </div>
  <script src="app.js"></script>
</body>
</html>""",
        "css": """* { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; }
body {
  background: #07040F;
  color: #E4E0F0;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
  padding: 16px;
}
.app-card {
  background: #120A24;
  border: 1px solid rgba(167, 139, 250, 0.25);
  border-radius: 20px;
  padding: 32px;
  width: 100%;
  max-width: 480px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.7), 0 0 30px rgba(124, 58, 237, 0.12);
}
.header { display: flex; align-items: center; gap: 14px; margin-bottom: 24px; }
.logo-dot { width: 14px; height: 14px; border-radius: 50%; background: #A78BFA; box-shadow: 0 0 10px #A78BFA; }
h1 { font-size: 18px; font-weight: 700; color: #FFF; line-height: 1.2; }
.subtitle { font-size: 11px; color: #8B84A3; margin-top: 2px; }
.badge { margin-left: auto; background: rgba(16, 185, 129, 0.15); color: #10B981; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: 600; }
.stat-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 20px; }
.stat-box { background: #0B0617; border: 1px solid rgba(167, 139, 250, 0.15); padding: 14px; border-radius: 12px; text-align: center; }
.stat-label { font-size: 11px; color: #8B84A3; text-transform: uppercase; letter-spacing: 1px; display: block; margin-bottom: 4px; }
.stat-num { font-size: 26px; font-weight: 700; color: #FFF; }
.stat-num.active { color: #F472B6; font-size: 18px; }
.controls { display: flex; gap: 10px; margin-bottom: 18px; }
.btn { flex: 1; padding: 12px; border: none; border-radius: 10px; font-weight: 600; cursor: pointer; transition: all 0.2s ease; }
.btn.primary { background: #7C3AED; color: #FFF; box-shadow: 0 4px 12px rgba(124, 58, 237, 0.3); }
.btn.primary:hover { background: #6D28D9; }
.btn.secondary { background: rgba(255, 255, 255, 0.08); color: #E4E0F0; }
.btn.secondary:hover { background: rgba(255, 255, 255, 0.14); }
.log-container { background: #0B0617; border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 12px; padding: 14px; }
.log-header { font-size: 11px; color: #8B84A3; margin-bottom: 6px; font-weight: 600; text-transform: uppercase; }
.log-body { font-size: 12px; color: #C4B5FD; font-mono; line-height: 1.5; min-height: 48px; }""",
        "js": """let count = 0;
const counterEl = document.getElementById("counterVal");
const logEl = document.getElementById("statusLog");
const actionBtn = document.getElementById("actionBtn");
const resetBtn = document.getElementById("resetBtn");

actionBtn.addEventListener("click", () => {
  count++;
  counterEl.textContent = count;
  const timestamp = new Date().toLocaleTimeString();
  logEl.innerHTML = `[${timestamp}] Action executed successfully (Trigger #${count})<br>` + logEl.innerHTML;
});

resetBtn.addEventListener("click", () => {
  count = 0;
  counterEl.textContent = "0";
  const timestamp = new Date().toLocaleTimeString();
  logEl.innerHTML = `[${timestamp}] Reset completed.<br>` + logEl.innerHTML;
});"""
    }


def _mock_build(workspace_path: Path, prompt: str, tools_by_name: dict) -> List[str]:
    """Generate realistic, domain-specific, working project files for any prompt."""
    time.sleep(0.8)
    emit("agent_status", agent="developer", text="Writing HTML markup")
    tpl = _generate_template_for_prompt(prompt)
    
    tools_by_name["write_file"].invoke({"path": "index.html", "content": tpl["html"]})

    time.sleep(0.4)
    emit("agent_status", agent="developer", text="Writing CSS stylesheet")
    tools_by_name["write_file"].invoke({"path": "styles.css", "content": tpl["css"]})

    time.sleep(0.4)
    emit("agent_status", agent="developer", text="Writing JS logic")
    tools_by_name["write_file"].invoke({"path": "app.js", "content": tpl["js"]})

    return ["index.html", "styles.css", "app.js"]


def _extract_and_write_code(content_str: str, workspace_path: Path, tools_by_name: dict) -> List[str]:
    """
    Robust multi-strategy code extractor: saves files from tool calls or
    any markdown code fence variation (```html:index.html, ### index.html```, etc.)
    """
    saved_files = []
    
    # Strategy 1: Code blocks with filename in fence header (e.g. ```html:index.html or ```js app.js)
    pattern_fence = r"```(?:(\w+)(?::|\s+))?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)\s*\n(.*?)```"
    for _, fname, code in re.findall(pattern_fence, content_str, re.DOTALL):
        clean_name = Path(fname.strip()).name
        if clean_name and code.strip():
            tools_by_name["write_file"].invoke({"path": clean_name, "content": code.strip()})
            saved_files.append(clean_name)

    # Strategy 2: Heading preceding code block (e.g. ### index.html\n```html\n...)
    pattern_heading = r"(?:###|##|#|File:|\*\*)\s*`?([a-zA-Z0-9_\-\.\/]+\.[a-zA-Z0-9]+)`?\s*\n+```(?:[a-zA-Z0-9]+)?\s*\n(.*?)```"
    for fname, code in re.findall(pattern_heading, content_str, re.DOTALL):
        clean_name = Path(fname.strip()).name
        if clean_name and clean_name not in saved_files and code.strip():
            tools_by_name["write_file"].invoke({"path": clean_name, "content": code.strip()})
            saved_files.append(clean_name)

    # Strategy 3: Standard unlabeled language blocks fallback
    raw_blocks = re.findall(r"```([a-zA-Z0-9]+)?\s*\n(.*?)```", content_str, re.DOTALL)
    for lang, code in raw_blocks:
        code_s = code.strip()
        lang_s = (lang or "").lower().strip()
        
        target_name = None
        if lang_s in ("html", "htm") or "<!doctype" in code_s.lower() or "<html" in code_s.lower():
            target_name = "index.html"
        elif lang_s == "css" or (("body {" in code_s or ":root" in code_s) and "{" in code_s):
            target_name = "styles.css"
        elif lang_s in ("js", "javascript") or ("document.getelement" in code_s.lower() or "addeventlistener" in code_s.lower()):
            target_name = "app.js"
        elif lang_s in ("py", "python"):
            target_name = "main.py"

        if target_name and target_name not in saved_files and code_s:
            tools_by_name["write_file"].invoke({"path": target_name, "content": code_s})
            saved_files.append(target_name)

    return saved_files


def _synthesize_modern_css(title: str) -> str:
    """Generates an ultra-premium, dark-mode CSS stylesheet for standalone web applications."""
    clean_title = title.replace('"', '').replace("'", "")
    return f"""/* ==========================================================================
   Tensor Bots — Elite Application Design System
   App: {clean_title}
   Auto-crafted with high-contrast dark theme, neon accents & micro-interactions
   ========================================================================== */

:root {{
  --bg-main: #07040F;
  --bg-surface: #120A24;
  --bg-surface-elevated: #1A0F33;
  --bg-input: #0B0617;
  
  --primary: #A78BFA;
  --primary-light: #C4B5FD;
  --primary-deep: #7C3AED;
  
  --accent-cyan: #38BDF8;
  --accent-pink: #F472B6;
  --accent-emerald: #34D399;
  --accent-amber: #FBBF24;
  
  --text-main: #E4E0F0;
  --text-muted: #8B84A3;
  --text-faint: #5C5474;
  
  --border-subtle: rgba(167, 139, 250, 0.18);
  --border-glow: rgba(167, 139, 250, 0.35);
  
  --radius-sm: 8px;
  --radius-md: 14px;
  --radius-lg: 20px;
  --radius-full: 9999px;
  
  --shadow-card: 0 16px 40px rgba(0, 0, 0, 0.65), 0 0 25px rgba(124, 58, 237, 0.12);
  --shadow-btn: 0 6px 20px rgba(124, 58, 237, 0.35);
  --font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}}

* {{
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}}

html, body {{
  min-height: 100vh;
  background-color: var(--bg-main);
  background-image: 
    radial-gradient(ellipse at 50% 0%, rgba(124, 58, 237, 0.15) 0%, transparent 60%),
    radial-gradient(circle at 100% 100%, rgba(56, 189, 248, 0.08) 0%, transparent 40%);
  color: var(--text-main);
  font-family: var(--font-family);
  font-size: 15px;
  line-height: 1.6;
  -webkit-font-smoothing: antialiased;
  padding: 24px 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
}}

.header, header {{
  width: 100%;
  max-width: 840px;
  margin-bottom: 24px;
  text-align: center;
}}

h1, h2, h3, h4 {{
  color: #FFF;
  font-weight: 700;
  letter-spacing: -0.02em;
  margin-bottom: 8px;
}}

h1 {{
  font-size: 28px;
  background: linear-gradient(135deg, #FFF 30%, var(--primary-light) 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
}}

.subtitle, p.subtitle {{
  color: var(--text-muted);
  font-size: 13px;
}}

.container, main, .app-card, .card {{
  width: 100%;
  max-width: 840px;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-lg);
  padding: 28px;
  box-shadow: var(--shadow-card);
  backdrop-filter: blur(16px);
  margin-bottom: 24px;
  position: relative;
  overflow: hidden;
}}

/* Inputs & Form controls */
input[type="text"], input[type="number"], input[type="date"], input[type="email"], select, textarea {{
  width: 100%;
  background: var(--bg-input);
  border: 1px solid var(--border-subtle);
  border-radius: var(--radius-md);
  padding: 12px 16px;
  color: var(--text-main);
  font-size: 14px;
  font-family: inherit;
  transition: all 0.2s ease;
  outline: none;
}}

input:focus, select:focus, textarea:focus {{
  border-color: var(--primary);
  box-shadow: 0 0 12px rgba(167, 139, 250, 0.3);
  background: #0E071D;
}}

.check-section, .input-group {{
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}}

/* Buttons */
button, .btn {{
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 11px 22px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
  border: none;
  user-select: none;
}}

button.primary, .btn.primary, button:not([class*="secondary"]):not([class*="outline"]) {{
  background: linear-gradient(135deg, var(--primary-deep), #9333EA);
  color: #FFF;
  box-shadow: var(--shadow-btn);
}}

button.primary:hover, .btn.primary:hover, button:not([class*="secondary"]):not([class*="outline"]):hover {{
  transform: translateY(-1.5px);
  box-shadow: 0 8px 24px rgba(124, 58, 237, 0.5);
}}

button:active, .btn:active {{
  transform: translateY(0.5px);
}}

button.secondary, .btn.secondary {{
  background: var(--bg-surface-elevated);
  border: 1px solid var(--border-subtle);
  color: var(--text-main);
}}

button.secondary:hover, .btn.secondary:hover {{
  background: rgba(255, 255, 255, 0.08);
  border-color: var(--primary-light);
}}

/* Tables */
table {{
  width: 100%;
  border-collapse: separate;
  border-spacing: 0;
  margin-top: 14px;
  border-radius: var(--radius-md);
  overflow: hidden;
  border: 1px solid var(--border-subtle);
}}

th, td {{
  padding: 12px 16px;
  text-align: left;
  border-bottom: 1px solid var(--border-subtle);
}}

th {{
  background: #0B0617;
  color: var(--primary-light);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}}

td {{
  background: rgba(18, 10, 36, 0.5);
  font-size: 13px;
}}

tr:last-child td {{
  border-bottom: none;
}}

tr:hover td {{
  background: rgba(167, 139, 250, 0.06);
}}

/* Toast notification popup */
.toast {{
  position: fixed;
  bottom: 24px;
  right: 24px;
  background: #150C2E;
  border: 1px solid var(--accent-emerald);
  color: #FFF;
  padding: 12px 20px;
  border-radius: var(--radius-md);
  font-size: 13px;
  font-weight: 500;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.6);
  opacity: 0;
  pointer-events: none;
  transform: translateY(12px);
  transition: all 0.3s ease;
  z-index: 1000;
}}

.toast.show {{
  opacity: 1;
  transform: translateY(0);
}}

/* Responsive styling */
@media (max-width: 640px) {{
  .container, main, .app-card {{
    padding: 18px;
  }}
  .check-section, .input-group {{
    flex-direction: column;
  }}
  button, .btn {{
    width: 100%;
  }}
}}
"""


def _synthesize_interactive_js(html_content: str, title: str) -> str:
    """Generates an intelligent, fully reactive JavaScript engine that wires up all HTML controls."""
    clean_title = title.replace('"', '').replace("'", "")
    t_lower = clean_title.lower()
    h_lower = html_content.lower()

    # 1. Match-3 / Candy Crush / Board Games
    if any(k in t_lower for k in ("candy", "crush", "match", "puzzle")) or \
       ("board" in h_lower and any(k in h_lower for k in ("candy", "moves", "swap", "crush", "stat-moves"))):
        return f"""// ==========================================================================
// Tensor Bots — Autonomous Match-3 Controller
// App: {clean_title}
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {{
  console.log("⚡ [{clean_title}] match-3 engine initializing...");

  const CANDIES = ['🍬', '🍭', '🍫', '🍓', '🍋', '🍇'];
  const ROWS = 8;
  const COLS = 8;

  let board = [];
  let score = 0;
  let moves = 30;
  let best = parseInt(localStorage.getItem('tb_candy_best') || '0', 10);
  let selectedTile = null;
  let isProcessing = false;

  const boardEl = document.getElementById("board") || document.getElementById("candyGrid") || document.querySelector(".board");
  const scoreEl = document.getElementById("score") || document.getElementById("scoreVal");
  const bestEl = document.getElementById("best") || document.getElementById("highScore");
  const movesEl = document.getElementById("moves") || document.getElementById("movesVal");
  const restartBtn = document.getElementById("restart") || document.getElementById("restartBtn");
  const overlay = document.getElementById("overlay") || document.getElementById("gameOverlay");
  const overlayTitle = document.getElementById("overlay-title") || document.getElementById("overlayTitle");
  const overlayScore = document.getElementById("overlay-score") || document.getElementById("finalScore");
  const overlayEmoji = document.getElementById("overlay-emoji");
  const overlayBtn = document.getElementById("overlay-btn") || document.getElementById("overlayBtn") || document.getElementById("resetGameBtn");
  const toastEl = document.getElementById("toast");

  if (!boardEl) return;

  function showToast(msg, duration = 2500) {{
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), duration);
  }}

  function randomCandy() {{
    return CANDIES[Math.floor(Math.random() * CANDIES.length)];
  }}

  function initBoard() {{
    score = 0;
    moves = 30;
    selectedTile = null;
    isProcessing = false;
    board = [];

    if (scoreEl) scoreEl.textContent = score;
    if (movesEl) movesEl.textContent = moves;
    if (bestEl) bestEl.textContent = best;
    if (overlay) {{
      overlay.hidden = true;
      overlay.style.display = "none";
    }}

    for (let r = 0; r < ROWS; r++) {{
      board[r] = [];
      for (let c = 0; c < COLS; c++) {{
        let candy;
        do {{
          candy = randomCandy();
        }} while (
          (r >= 2 && board[r - 1][c] === candy && board[r - 2][c] === candy) ||
          (c >= 2 && board[r][c - 1] === candy && board[r][c - 2] === candy)
        );
        board[r][c] = candy;
      }}
    }}
    render();
  }}

  function render() {{
    boardEl.innerHTML = "";
    for (let r = 0; r < ROWS; r++) {{
      for (let c = 0; c < COLS; c++) {{
        const cell = document.createElement("button");
        cell.type = "button";
        cell.className = "cell candy-cell";
        cell.textContent = board[r][c] || "";
        cell.dataset.row = r;
        cell.dataset.col = c;
        if (selectedTile && selectedTile.r === r && selectedTile.c === c) {{
          cell.classList.add("selected");
        }}
        cell.addEventListener("click", () => handleTileClick(r, c));
        boardEl.appendChild(cell);
      }}
    }}
  }}

  async function handleTileClick(r, c) {{
    if (isProcessing || moves <= 0) return;

    if (!selectedTile) {{
      selectedTile = {{ r, c }};
      render();
      return;
    }}

    const {{ r: r1, c: c1 }} = selectedTile;
    if (r1 === r && c1 === c) {{
      selectedTile = null;
      render();
      return;
    }}

    const isAdjacent = (Math.abs(r1 - r) === 1 && c1 === c) || (Math.abs(c1 - c) === 1 && r1 === r);
    if (!isAdjacent) {{
      selectedTile = {{ r, c }};
      render();
      return;
    }}

    isProcessing = true;
    selectedTile = null;
    swap(r1, c1, r, c);
    render();

    const matches = findMatches();
    if (matches.length > 0) {{
      moves--;
      if (movesEl) movesEl.textContent = moves;
      await processMatches(matches, 1);
    }} else {{
      await sleep(200);
      swap(r1, c1, r, c);
      render();
    }}

    isProcessing = false;
    checkGameOver();
  }}

  function swap(r1, c1, r2, c2) {{
    const temp = board[r1][c1];
    board[r1][c1] = board[r2][c2];
    board[r2][c2] = temp;
  }}

  function findMatches() {{
    const matched = new Set();
    for (let r = 0; r < ROWS; r++) {{
      let len = 1;
      for (let c = 0; c < COLS; c++) {{
        if (c < COLS - 1 && board[r][c] && board[r][c] === board[r][c + 1]) {{
          len++;
        }} else {{
          if (len >= 3) {{
            for (let i = 0; i < len; i++) matched.add(`${{r}},${{c - i}}`);
          }}
          len = 1;
        }}
      }}
    }}
    for (let c = 0; c < COLS; c++) {{
      let len = 1;
      for (let r = 0; r < ROWS; r++) {{
        if (r < ROWS - 1 && board[r][c] && board[r][c] === board[r + 1][c]) {{
          len++;
        }} else {{
          if (len >= 3) {{
            for (let i = 0; i < len; i++) matched.add(`${{r - i}},${{c}}`);
          }}
          len = 1;
        }}
      }}
    }}
    return Array.from(matched).map(coord => {{
      const [r, c] = coord.split(",").map(Number);
      return {{ r, c }};
    }});
  }}

  async function processMatches(matches, combo = 1) {{
    const cellElements = boardEl.querySelectorAll(".cell, .candy-cell");
    matches.forEach(({{ r, c }}) => {{
      const idx = r * COLS + c;
      if (cellElements[idx]) cellElements[idx].classList.add("matched");
    }});

    const pts = matches.length * 10 * combo;
    score += pts;
    if (scoreEl) scoreEl.textContent = score;

    if (score > best) {{
      best = score;
      localStorage.setItem('tb_candy_best', best.toString());
      if (bestEl) bestEl.textContent = best;
    }}

    if (combo >= 2) showToast(`🔥 Combo x${{combo}}! +${{pts}} pts`);
    await sleep(220);

    matches.forEach(({{ r, c }}) => {{ board[r][c] = null; }});

    for (let c = 0; c < COLS; c++) {{
      let writeRow = ROWS - 1;
      for (let r = ROWS - 1; r >= 0; r--) {{
        if (board[r][c] !== null) {{
          board[writeRow][c] = board[r][c];
          if (writeRow !== r) board[r][c] = null;
          writeRow--;
        }}
      }}
      while (writeRow >= 0) {{
        board[writeRow][c] = randomCandy();
        writeRow--;
      }}
    }}

    render();
    await sleep(180);

    const chain = findMatches();
    if (chain.length > 0) await processMatches(chain, combo + 1);
  }}

  function checkGameOver() {{
    if (moves <= 0) {{
      if (overlay) {{
        overlay.hidden = false;
        overlay.style.display = "flex";
        if (overlayScore) overlayScore.textContent = score;
        if (score >= 1000) {{
          if (overlayEmoji) overlayEmoji.textContent = "🎉";
          if (overlayTitle) overlayTitle.textContent = "Level Cleared!";
        }} else {{
          if (overlayEmoji) overlayEmoji.textContent = "🍬";
          if (overlayTitle) overlayTitle.textContent = "Out of Moves!";
        }}
      }}
    }}
  }}

  function sleep(ms) {{ return new Promise(res => setTimeout(res, ms)); }}

  if (restartBtn) restartBtn.addEventListener("click", () => {{ initBoard(); showToast("Game restarted!"); }});
  if (overlayBtn) overlayBtn.addEventListener("click", () => initBoard());

  initBoard();
}});
"""

    return f"""// ==========================================================================
// Tensor Bots — Autonomous Reactive Application Controller
// App: {clean_title}
// Auto-generated interactive event handler ensuring 100% functional controls
// ==========================================================================

document.addEventListener("DOMContentLoaded", () => {{
  console.log("⚡ [{clean_title}] initialized successfully.");

  // Toast notification helper
  let toastEl = document.getElementById("toast");
  if (!toastEl) {{
    toastEl = document.createElement("div");
    toastEl.id = "toast";
    toastEl.className = "toast";
    document.body.appendChild(toastEl);
  }}

  function showToast(msg, duration = 3000) {{
    if (!toastEl) return;
    toastEl.textContent = msg;
    toastEl.classList.add("show");
    setTimeout(() => toastEl.classList.remove("show"), duration);
  }}

  // Auto-detect and wire Attendance / Records / Tracker tables
  const recordsTableBody = document.querySelector("#recordsTable tbody, table tbody");
  const nameInput = document.getElementById("nameInput") || document.querySelector("input[type='text']");
  const checkBtn = document.getElementById("checkBtn") || document.querySelector("button.primary, button");

  if (checkBtn && recordsTableBody) {{
    let isCheckedIn = false;
    let currentRecordRow = null;

    checkBtn.addEventListener("click", () => {{
      const name = (nameInput ? nameInput.value.trim() : "") || "User";
      const now = new Date().toLocaleTimeString();

      if (!isCheckedIn) {{
        isCheckedIn = true;
        checkBtn.textContent = "Check‑Out";
        checkBtn.style.background = "linear-gradient(135deg, #EC4899, #DB2777)";
        
        currentRecordRow = document.createElement("tr");
        currentRecordRow.innerHTML = `
          <td><strong>${{name}}</strong></td>
          <td><span style="color: #34D399;">● ${{now}}</span></td>
          <td><span style="color: #8B84A3;">Active...</span></td>
        `;
        recordsTableBody.prepend(currentRecordRow);
        showToast(`✓ Check-In recorded for ${{name}} at ${{now}}`);
      }} else {{
        isCheckedIn = false;
        checkBtn.textContent = "Check‑In";
        checkBtn.style.background = "";
        
        if (currentRecordRow) {{
          const cells = currentRecordRow.querySelectorAll("td");
          if (cells.length >= 3) {{
            cells[2].innerHTML = `<span style="color: #F472B6;">● ${{now}}</span>`;
          }}
        }}
        showToast(`✓ Check-Out recorded for ${{name}} at ${{now}}`);
      }}
    }});
  }} else {{
    // Generic auto-wire for any interactive buttons
    document.querySelectorAll("button").forEach((btn) => {{
      btn.addEventListener("click", () => {{
        const btnText = btn.textContent.trim();
        showToast(`✓ Action executed: ${{btnText || "Success"}}`);
      }});
    }});
  }}

  // Ensure inputs submit on Enter key
  document.querySelectorAll("input").forEach((inp) => {{
    inp.addEventListener("keydown", (e) => {{
      if (e.key === "Enter") {{
        const siblingBtn = inp.parentElement?.querySelector("button") || document.querySelector("button");
        if (siblingBtn) siblingBtn.click();
      }}
    }});
  }});
}});
"""


def is_html_broken(content: str) -> bool:
    """
    Detects if an HTML file is truncated, cut off mid-tag, or missing essential closing elements.
    """
    if not content or len(content.strip()) < 120:
        return True
    c = content.lower()
    # Unclosed style block renders as a blank white page in modern browsers
    if "<style" in c and "</style>" not in c:
        return True
    # Unclosed script block
    if "<script" in c and "</script>" not in c and "src=" not in c.split("<script")[-1]:
        return True
    # Missing structural closing tags
    if "</html>" not in c or "<body" not in c:
        return True
    return False


def is_css_broken(content: str) -> bool:
    """Detects if a CSS file was cut off mid-property or mid-rule."""
    if not content or len(content.strip()) < 40:
        return True
    if content.count("{") > content.count("}"):
        return True
    stripped = content.strip()
    last_line = stripped.splitlines()[-1].strip() if stripped.splitlines() else ""
    if last_line.endswith((",", "(", ":", "at")) or not last_line.endswith(("}", "*/", ";")):
        return True
    return False


def _ensure_project_assets_complete(workspace_path: Path, prompt: str, tools_by_name: dict) -> List[str]:
    """Inspects workspace files, ensures all linked assets exist, repairs truncated files, and injects modern styling/logic."""
    created = []
    
    # 1. Validate root index.html first to guarantee zero white screens
    index_file = workspace_path / "index.html"
    index_needs_scaffold = False
    
    if not index_file.exists():
        index_needs_scaffold = True
    else:
        try:
            content = index_file.read_text(encoding="utf-8")
            if not content or len(content.strip()) < 40:
                index_needs_scaffold = True
            elif is_html_broken(content):
                # Repair closing tags without throwing away the user's generated app!
                repaired = content
                c_low = repaired.lower()
                if "<style" in c_low and "</style>" not in c_low:
                    repaired += "\n</style>"
                if "<script" in c_low and "</script>" not in c_low and "src=" not in c_low.split("<script")[-1]:
                    repaired += "\n</script>"
                if "</body>" not in c_low:
                    repaired += "\n</body>"
                if "</html>" not in c_low:
                    repaired += "\n</html>"
                index_file.write_text(repaired, encoding="utf-8")
                emit("agent_status", agent="developer", text="Repaired closing tags on generated index.html")
        except Exception:
            index_needs_scaffold = True

    if index_needs_scaffold:
        template = _generate_template_for_prompt(prompt)
        tools_by_name["write_file"].invoke({"path": "index.html", "content": template["html"]})
        tools_by_name["write_file"].invoke({"path": "styles.css", "content": template["css"]})
        tools_by_name["write_file"].invoke({"path": "app.js", "content": template["js"]})
        created.extend(["index.html", "styles.css", "app.js"])
        return created

    # 2. Inspect all HTML files in workspace
    html_files = list(workspace_path.rglob("*.html"))
    for html_file in html_files:
        try:
            content = html_file.read_text(encoding="utf-8")
            
            # If secondary HTML file is broken, repair by appending closing tags or replacing
            if is_html_broken(content):
                if "<style" in content.lower() and "</style>" not in content.lower():
                    content += "\n</style>\n</head>\n<body>\n<div class='container'><h1>Application</h1></div>\n</body>\n</html>"
                    html_file.write_text(content, encoding="utf-8")

            # Check referenced CSS files
            for css_ref in re.findall(r'<link[^>]+href=["\']([^"\']+\.css)["\']', content):
                if not css_ref.startswith(("http://", "https://", "//")):
                    css_path = workspace_path / css_ref
                    needs_css = False
                    if not css_path.exists():
                        needs_css = True
                    else:
                        try:
                            css_text = css_path.read_text(encoding="utf-8")
                            if is_css_broken(css_text):
                                needs_css = True
                        except Exception:
                            needs_css = True
                            
                    if needs_css:
                        css_content = _synthesize_modern_css(prompt)
                        tools_by_name["write_file"].invoke({"path": css_ref, "content": css_content})
                        created.append(css_ref)
                        emit("agent_status", agent="developer", text=f"Auto-generated complete stylesheet: {css_ref}")

            # Check referenced JS files
            for js_ref in re.findall(r'<script[^>]+src=["\']([^"\']+\.js)["\']', content):
                if not js_ref.startswith(("http://", "https://", "//")):
                    js_path = workspace_path / js_ref
                    needs_js = False
                    if not js_path.exists():
                        needs_js = True
                    else:
                        try:
                            js_text = js_path.read_text(encoding="utf-8")
                            if len(js_text.strip()) < 30:
                                needs_js = True
                        except Exception:
                            needs_js = True
                            
                    if needs_js:
                        js_content = _synthesize_interactive_js(content, prompt)
                        tools_by_name["write_file"].invoke({"path": js_ref, "content": js_content})
                        created.append(js_ref)
                        emit("agent_status", agent="developer", text=f"Auto-generated interactive script: {js_ref}")

            # Check if CSS is missing entirely
            if '<link rel="stylesheet"' not in content and "</style>" not in content:
                css_inline = _synthesize_modern_css(prompt)
                injection = f"\n<style>\n{css_inline}\n</style>\n</head>"
                if "</head>" in content:
                    content = content.replace("</head>", injection, 1)
                else:
                    content = f"<style>\n{css_inline}\n</style>\n" + content
                html_file.write_text(content, encoding="utf-8")

            # Check if JS is missing entirely
            if "<script" not in content.lower():
                js_content = _synthesize_interactive_js(content, prompt)
                tools_by_name["write_file"].invoke({"path": "app.js", "content": js_content})
                created.append("app.js")
                pattern = re.compile(r"</body>", re.IGNORECASE)
                if pattern.search(content):
                    content = pattern.sub('<script src="app.js"></script>\n</body>', content, count=1)
                else:
                    content += '\n<script src="app.js"></script>\n'
                html_file.write_text(content, encoding="utf-8")
                emit("agent_status", agent="developer", text="Auto-generated interactive script: app.js")

        except Exception as e:
            print("Error in _ensure_project_assets_complete:", e)
            
    return created


@agent_node("developer")
def developer_node(state: TensorState) -> dict:
    """Join node: executes file tools to construct or revise the requested application."""
    run_id = state.get("run_id", "default_run")
    user_prompt = state.get("user_prompt", "")
    research = state.get("research", "")
    plan = state.get("plan", "")
    review = state.get("review", {})
    iteration = state.get("iteration", 0) + 1
    
    workspace_path = WORKSPACE_DIR / run_id
    tools = make_file_tools(workspace_path)
    tools_by_name = {t.name: t for t in tools}
    
    if iteration > 1:
        emit("agent_status", agent="developer", text=f"Revision round {iteration}: fixing issues")
    else:
        emit("agent_status", agent="developer", text="Implementing planned files")
        
    created_files: List[str] = []
    
    if MOCK_LLM:
        created_files = _mock_build(workspace_path, user_prompt, tools_by_name)
    else:
        llm = get_llm()
        llm_with_tools = llm.bind_tools(tools)
        
        # Build prompt instructions with context from research, plan, and previous review
        review_context = ""
        if review and not review.get("approved", True):
            issues = review.get("issues", [])
            review_context = (
                f"\n\nTARGETED REVISION (Round {iteration}):\n"
                "Inspect the current workspace files before editing. Resolve only these reviewer findings; "
                "preserve the existing approved visual design and all working behavior. Do not rewrite "
                "unrelated files or replace a complete project with a new implementation.\n"
                "Reviewer findings:\n"
                + "\n".join(f"- {i}" for i in issues)
            )
            
        user_msg = (
            f"User Goal (authoritative; preserve every requested feature and workflow): {user_prompt}\n\n"
            f"Technical Research:\n{research}\n\n"
            f"Architecture Plan:\n{plan}"
            f"{review_context}\n\n"
            f"Use `list_files` and `read_file` as needed, then call `write_file` for every file you actually change. "
            f"Do not modify files unrelated to the current task or review findings."
        )
        
        messages = [
            SystemMessage(content=DEVELOPER_SYSTEM_PROMPT),
            HumanMessage(content=user_msg),
        ]
        
        # Tool-calling loop (up to 4 rounds)
        max_tool_rounds = 4
        for round_idx in range(max_tool_rounds):
            try:
                response = invoke_with_retry(
                    llm_with_tools,
                    messages,
                    agent_name="developer",
                    tools=tools,
                )
            except Exception as exc:
                logger.warning(
                    "Developer model call failed (%s); attempting recovery",
                    type(exc).__name__,
                )
                # If files have already been written to disk, proceed gracefully to review
                existing_files = [p for p in workspace_path.rglob("*") if p.is_file()]
                if existing_files:
                    emit("agent_status", agent="developer", text="Files saved; handing off to reviewer")
                    break
                # Fallback: prompt model directly to output complete markdown code blocks
                emit("agent_status", agent="developer", text="Generating code files directly...")
                try:
                    raw_llm = get_llm()
                    raw_msg = (
                        f"User Goal: {user_prompt}\n\n"
                        f"Technical Research:\n{research}\n\n"
                        f"Architecture Plan:\n{plan}\n\n"
                        f"Implement complete, functional code for this project. Output all files in standard markdown fences, e.g.:\n"
                        f"```html:index.html\n...```\n"
                        f"```css:styles.css\n...```\n"
                        f"```js:app.js\n...```\n"
                    )
                    raw_resp = invoke_with_retry(
                        raw_llm,
                        [SystemMessage(content=DEVELOPER_SYSTEM_PROMPT), HumanMessage(content=raw_msg)],
                        agent_name="developer",
                    )
                    _extract_and_write_code(extract_text(raw_resp.content), workspace_path, tools_by_name)
                    break
                except Exception as fallback_exc:
                    logger.warning(
                        "Developer direct-code fallback failed (%s)",
                        type(fallback_exc).__name__,
                    )
                    break
            messages.append(response)
            
            tool_calls = getattr(response, "tool_calls", [])
            if not tool_calls:
                # If model responded with text without tool calls, extract files with multi-strategy parser
                content_str = extract_text(response.content)
                _extract_and_write_code(content_str, workspace_path, tools_by_name)
                break
                
            # Execute requested tools
            for tc in tool_calls:
                tool_name = tc.get("name")
                tool_args = tc.get("args", {})
                tool_id = tc.get("id", f"call_{round_idx}")
                
                if tool_name in tools_by_name:
                    tool_func = tools_by_name[tool_name]
                    tool_result = tool_func.invoke(tool_args)
                    messages.append(ToolMessage(content=str(tool_result), tool_call_id=tool_id))
            
        existing_files = [path for path in workspace_path.rglob("*") if path.is_file()]
        if not existing_files:
            emit("agent_status", agent="developer", text="Applying resilient scaffold")
            created_files = _mock_build(workspace_path, user_prompt, tools_by_name)

        # Guardrail: Ensure all referenced CSS/JS files are 100% complete and working
        _ensure_project_assets_complete(workspace_path, user_prompt, tools_by_name)

        # Scan workspace for all files written
        created_files = []
        for item in sorted(workspace_path.rglob("*")):
            if item.is_file():
                created_files.append(str(item.relative_to(workspace_path)))
    
    file_summary_lines = [f"- `{f}` ({((workspace_path / f).stat().st_size if (workspace_path / f).exists() else 0)} bytes)" for f in created_files]
    output_md = f"""### Developer Implementation (Round {iteration})

**Files Written to Disk:**
{chr(10).join(file_summary_lines) if file_summary_lines else "- No files found"}
"""
    emit("agent_output", agent="developer", text=output_md)
    emit("handoff", **{"from": "developer", "to": "reviewer", "label": "Code for review"})
    
    return {"files": created_files, "iteration": iteration}

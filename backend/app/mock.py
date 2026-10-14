"""
Tensor Bots - Offline Demonstration Mock Engine.

# TEACH: Provides deterministic, zero-cost LLM responses so attendees can
# run, debug, and understand the full multi-agent workflow offline without API keys.
"""

import re
import time
from typing import Any
from langchain_core.messages import AIMessage


def _extract_prompt_text(prompt: Any) -> str:
    """Extract string content from string or list of message objects."""
    if isinstance(prompt, str):
        return prompt
    if isinstance(prompt, list):
        parts = []
        for p in prompt:
            if hasattr(p, "content"):
                parts.append(str(p.content))
            elif isinstance(p, dict) and "content" in p:
                parts.append(str(p["content"]))
            else:
                parts.append(str(p))
        return "\n".join(parts)
    return str(prompt)


def mock_response(agent_name: str = "agent", schema: Any = None, prompt: Any = "") -> Any:
    """
    Generate realistic canned responses for each agent in the workflow.
    Simulates network latency with a brief sleep (0.8-2s).
    """
    time.sleep(1.0)
    prompt_text = _extract_prompt_text(prompt)

    if agent_name == "manager":
        if schema is not None:
            # TEACH: Manager planning returns structured AgentBriefs for teammates
            from app.state import AgentBriefs
            return AgentBriefs(
                researcher="Focus on single-page architecture using vanilla HTML, CSS, and modern JavaScript without external dependencies.",
                planner="Plan a clean 3-file structure: index.html for semantic layout, styles.css for modern styling, and app.js for state logic.",
                developer="Implement modular, clean code with responsive design, working event listeners, and robust state management.",
                reviewer="Inspect file completeness, UI responsiveness, and ensure all interactive elements function properly."
            )
        else:
            # TEACH: Final manager exit node generates wrap-up summary
            summary = (
                "### Project Delivery Summary\n\n"
                "The application was successfully built, styled, and verified across all criteria:\n"
                "- `index.html`: Semantic layout and structured UI containers\n"
                "- `styles.css`: Responsive, modern dark-mode styling\n"
                "- `app.js`: Interactive event listeners and state management\n\n"
                "All reviewer standards passed with zero detected issues."
            )
            return AIMessage(content=summary)

    elif agent_name == "researcher":
        # TEACH: Researcher produces architectural guidelines and constraints
        research_md = (
            "### Architectural & Technical Research\n\n"
            "1. **Core Constraints:** Standalone single-page application using vanilla HTML5, CSS3, and ES6+ JavaScript. No build step or package dependencies.\n"
            "2. **Recommended Patterns:** Event-driven architecture with a centralized state object. Use CSS flexbox/grid for responsive layouts.\n"
            "3. **Edge Cases to Avoid:** Unhandled DOM element queries, input validation failures, and broken event listener bindings.\n"
            "4. **Implementation Strategy:** Keep structure semantic in `index.html`, visual design in `styles.css`, and reactive logic in `app.js`."
        )
        return AIMessage(content=research_md)

    elif agent_name == "planner":
        # TEACH: Planner drafts exact file blueprints and UX specifications
        plan_md = (
            "### Application Architecture & Implementation Plan\n\n"
            "1. **Target Files:**\n"
            "   - `index.html`: Main container, header, controls, and dynamic content displays.\n"
            "   - `styles.css`: Modern dark theme, flexbox/grid layout, typography, and micro-interactions.\n"
            "   - `app.js`: State management, event handlers, and DOM render updates.\n"
            "2. **UI/UX Breakdown:** Header with application title, primary interaction card, and feedback status.\n"
            "3. **Verification Checklist:** Verify all controls work, layout is responsive, and zero console errors."
        )
        return AIMessage(content=plan_md)

    elif agent_name == "developer":
        # TEACH: Developer generates full working code in index.html, styles.css, app.js
        dev_code = (
            "### index.html\n"
            "```html\n"
            "<!DOCTYPE html>\n"
            "<html lang=\"en\">\n"
            "<head>\n"
            "  <meta charset=\"UTF-8\">\n"
            "  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
            "  <title>Tensor Bots Application</title>\n"
            "  <link rel=\"stylesheet\" href=\"styles.css\">\n"
            "</head>\n"
            "<body>\n"
            "  <div class=\"app-container\">\n"
            "    <header class=\"header\">\n"
            "      <h1>Tensor Bots App</h1>\n"
            "      <p class=\"subtitle\">Generated by Multi-Agent Workflow</p>\n"
            "    </header>\n"
            "    <main class=\"main-card\">\n"
            "      <div class=\"display-box\">\n"
            "        <span class=\"label\">Counter</span>\n"
            "        <span id=\"counter-value\" class=\"value\">0</span>\n"
            "      </div>\n"
            "      <div class=\"actions\">\n"
            "        <button id=\"btn-decrement\" class=\"btn secondary\">-</button>\n"
            "        <button id=\"btn-reset\" class=\"btn outline\">Reset</button>\n"
            "        <button id=\"btn-increment\" class=\"btn primary\">+</button>\n"
            "      </div>\n"
            "    </main>\n"
            "  </div>\n"
            "  <script src=\"app.js\"></script>\n"
            "</body>\n"
            "</html>\n"
            "```\n\n"
            "### styles.css\n"
            "```css\n"
            ":root {\n"
            "  --bg-color: #0f172a;\n"
            "  --card-bg: #1e293b;\n"
            "  --text-main: #f8fafc;\n"
            "  --text-muted: #94a3b8;\n"
            "  --primary: #3b82f6;\n"
            "  --primary-hover: #2563eb;\n"
            "  --radius: 12px;\n"
            "}\n\n"
            "* {\n"
            "  box-sizing: border-box;\n"
            "  margin: 0;\n"
            "  padding: 0;\n"
            "  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n"
            "}\n\n"
            "body {\n"
            "  background-color: var(--bg-color);\n"
            "  color: var(--text-main);\n"
            "  min-height: 100vh;\n"
            "  display: flex;\n"
            "  align-items: center;\n"
            "  justify-content: center;\n"
            "  padding: 1.5rem;\n"
            "}\n\n"
            ".app-container {\n"
            "  width: 100%;\n"
            "  max-width: 440px;\n"
            "  text-align: center;\n"
            "}\n\n"
            ".header h1 {\n"
            "  font-size: 1.8rem;\n"
            "  font-weight: 700;\n"
            "  margin-bottom: 0.25rem;\n"
            "}\n\n"
            ".subtitle {\n"
            "  color: var(--text-muted);\n"
            "  font-size: 0.9rem;\n"
            "  margin-bottom: 1.5rem;\n"
            "}\n\n"
            ".main-card {\n"
            "  background: var(--card-bg);\n"
            "  padding: 2rem;\n"
            "  border-radius: var(--radius);\n"
            "  box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3);\n"
            "  border: 1px solid rgba(255, 255, 255, 0.08);\n"
            "}\n\n"
            ".display-box {\n"
            "  display: flex;\n"
            "  flex-direction: column;\n"
            "  gap: 0.5rem;\n"
            "  margin-bottom: 1.5rem;\n"
            "}\n\n"
            ".display-box .value {\n"
            "  font-size: 3.5rem;\n"
            "  font-weight: 800;\n"
            "  color: var(--primary);\n"
            "}\n\n"
            ".actions {\n"
            "  display: flex;\n"
            "  gap: 0.75rem;\n"
            "  justify-content: center;\n"
            "}\n\n"
            ".btn {\n"
            "  padding: 0.6rem 1.25rem;\n"
            "  border: none;\n"
            "  border-radius: 8px;\n"
            "  font-size: 1rem;\n"
            "  font-weight: 600;\n"
            "  cursor: pointer;\n"
            "  transition: background-color 0.15s ease;\n"
            "}\n\n"
            ".btn.primary {\n"
            "  background: var(--primary);\n"
            "  color: #fff;\n"
            "}\n\n"
            ".btn.primary:hover {\n"
            "  background: var(--primary-hover);\n"
            "}\n\n"
            ".btn.secondary {\n"
            "  background: #334155;\n"
            "  color: #fff;\n"
            "}\n\n"
            ".btn.secondary:hover {\n"
            "  background: #475569;\n"
            "}\n\n"
            ".btn.outline {\n"
            "  background: transparent;\n"
            "  color: var(--text-muted);\n"
            "  border: 1px solid #475569;\n"
            "}\n\n"
            ".btn.outline:hover {\n"
            "  color: var(--text-main);\n"
            "  border-color: var(--text-muted);\n"
            "}\n"
            "```\n\n"
            "### app.js\n"
            "```javascript\n"
            "document.addEventListener('DOMContentLoaded', () => {\n"
            "  let count = 0;\n"
            "  const counterEl = document.getElementById('counter-value');\n"
            "  const incBtn = document.getElementById('btn-increment');\n"
            "  const decBtn = document.getElementById('btn-decrement');\n"
            "  const resetBtn = document.getElementById('btn-reset');\n\n"
            "  function updateDisplay() {\n"
            "    if (counterEl) counterEl.textContent = count;\n"
            "  }\n\n"
            "  if (incBtn) {\n"
            "    incBtn.addEventListener('click', () => {\n"
            "      count += 1;\n"
            "      updateDisplay();\n"
            "    });\n"
            "  }\n"
            "  if (decBtn) {\n"
            "    decBtn.addEventListener('click', () => {\n"
            "      count -= 1;\n"
            "      updateDisplay();\n"
            "    });\n"
            "  }\n"
            "  if (resetBtn) {\n"
            "    resetBtn.addEventListener('click', () => {\n"
            "      count = 0;\n"
            "      updateDisplay();\n"
            "    });\n"
            "  }\n"
            "});\n"
            "```"
        )
        return AIMessage(content=dev_code)

    elif agent_name == "reviewer":
        # TEACH: Reviewer returns ReviewVerdict with approved=False on round 1 and approved=True on round 2
        from app.state import ReviewVerdict
        m = re.search(r"Iteration:\s*(\d+)", prompt_text)
        round_num = int(m.group(1)) if m else 1
        if round_num <= 1:
            return ReviewVerdict(
                approved=False,
                issues=["Improve button hover transitions and add responsive styling for small screens."],
                summary="Changes requested: improve button hover states and responsive styling."
            )
        else:
            return ReviewVerdict(
                approved=True,
                issues=[],
                summary="Approved: all files exist, are functional, responsive, and satisfy requirements."
            )

    return AIMessage(content="Mock response completed.")

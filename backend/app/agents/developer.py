import logging
import re
from pathlib import Path
from typing import Dict, List
from langchain_core.messages import SystemMessage, HumanMessage

from app.config import WORKSPACE_DIR
from app.events import emit, agent_node
from app.state import TensorState
from app.tools import make_file_tools
from app.llm import get_llm, invoke_with_retry, extract_text

logger = logging.getLogger(__name__)

DEVELOPER_SYSTEM_PROMPT = """You are the Senior Software Developer on an elite AI engineering team.
Your job is to implement the requested application using three separate files:
1. `index.html` - Semantic HTML5 markup linking `styles.css` and `app.js`.
2. `styles.css` - Modern, responsive, high-contrast CSS styling.
3. `app.js` - Complete interactive ES6+ JavaScript handling state and event listeners.

CRITICAL RULES:
1. Write 100% complete, fully working code. Never output placeholders, stubs, or "// TODO".
2. Use vanilla HTML5, CSS3, and ES6 JavaScript. No npm packages or external build steps.
3. Every button, input, slider, or control in HTML must have working event listeners in JavaScript.
4. Keep the code concise, clean, and modular (~50-120 lines per file).

OUTPUT FORMAT:
Provide the full contents for all three files using markdown code blocks with clear headers:

### index.html
```html
...
```

### styles.css
```css
...
```

### app.js
```javascript
...
```
"""


def extract_project_files(text: str) -> Dict[str, str]:
    """Extracts index.html, styles.css, and app.js from the LLM response."""
    files: Dict[str, str] = {}
    text = text.replace("\r\n", "\n")

    # Match ### filename or filename followed by code block
    pattern = re.compile(
        r"(?:###\s*|\*\*|File:\s*)?`?([a-zA-Z0-9_\-\.\/]+\.(?:html|css|js))`?\*?\*?\s*\n+```(?:html|css|javascript|js)?\n([\s\S]*?)(?:```|$)",
        re.IGNORECASE,
    )
    for m in pattern.finditer(text):
        fname = Path(m.group(1).strip().lower()).name
        code = m.group(2).strip()
        if fname in ("index.html", "styles.css", "app.js") or fname.endswith((".html", ".css", ".js")):
            if code and (fname not in files or len(files[fname]) < 20):
                files[fname] = code

    # Fallback by language fences if file headers were omitted
    if not any(k.endswith(".html") for k in files):
        m = re.search(r"```html\n([\s\S]*?)(?:```|$)", text, re.IGNORECASE)
        if m and m.group(1).strip():
            files["index.html"] = m.group(1).strip()
    if not any(k.endswith(".css") for k in files):
        m = re.search(r"```css\n([\s\S]*?)(?:```|$)", text, re.IGNORECASE)
        if m and m.group(1).strip():
            files["styles.css"] = m.group(1).strip()
    if not any(k.endswith(".js") for k in files):
        m = re.search(r"```(?:javascript|js)\n([\s\S]*?)(?:```|$)", text, re.IGNORECASE)
        if m and m.group(1).strip():
            files["app.js"] = m.group(1).strip()

    # Map to canonical names
    canonical: Dict[str, str] = {}
    for k, v in files.items():
        if k.endswith(".html") and ("index.html" not in canonical or k == "index.html"):
            canonical["index.html"] = v
        elif k.endswith(".css") and ("styles.css" not in canonical or k == "styles.css"):
            canonical["styles.css"] = v
        elif k.endswith(".js") and ("app.js" not in canonical or k == "app.js"):
            canonical["app.js"] = v

    return canonical


def is_html_broken(content: str) -> bool:
    """Helper to verify basic HTML completeness."""
    return not content or "</html>" not in content.lower()


def is_css_broken(content: str) -> bool:
    """Helper to verify basic CSS completeness."""
    return not content or content.count("{") != content.count("}")


@agent_node("developer")
def developer_node(state: TensorState) -> dict:
    """Developer agent: generates or revises HTML, CSS, and JS using the LLM API."""
    run_id = state.get("run_id", "default_run")
    user_prompt = state.get("user_prompt", "").strip() or "Interactive Web Application"
    briefs = state.get("briefs", {})
    developer_brief = briefs.get("developer", "")
    research = state.get("research", "")
    plan = state.get("plan", "")
    review = state.get("review", {})
    iteration = state.get("iteration", 0) + 1

    workspace_path = WORKSPACE_DIR / run_id
    tools = make_file_tools(workspace_path)
    tools_by_name = {t.name: t for t in tools}

    is_revision = iteration > 1 or (bool(review) and not review.get("approved", True))

    if is_revision:
        emit("agent_status", agent="developer", text=f"Revision round {iteration}: applying requested changes...")
        issues = review.get("issues", [])
        review_summary = review.get("summary", "")

        existing_code = ""
        for fname in ("index.html", "styles.css", "app.js"):
            fpath = workspace_path / fname
            if fpath.exists():
                existing_code += f"\n### Existing {fname}:\n```{fname.split('.')[-1]}\n{fpath.read_text(encoding='utf-8')[:3000]}\n```\n"

        issues_text = "\n".join(f"- {i}" for i in issues) if issues else "- Fix reported issues."
        user_msg = f"""Revise this application to resolve code review feedback.

ORIGINAL REQUEST: {user_prompt}
REVIEWER SUMMARY: {review_summary}
ISSUES TO FIX:
{issues_text}

EXISTING CODE:
{existing_code}

Provide the complete updated code for index.html, styles.css, and app.js."""
    else:
        emit("agent_status", agent="developer", text="Generating HTML, CSS, and JS code via LLM...")
        user_msg = f"""Implement the web application according to these specifications:

USER REQUEST: {user_prompt}
PROJECT MANAGER BRIEF: {developer_brief}
TECHNICAL RESEARCH: {research}
ARCHITECTURE PLAN: {plan}

Write the complete code for index.html, styles.css, and app.js."""

    messages = [
        SystemMessage(content=DEVELOPER_SYSTEM_PROMPT),
        HumanMessage(content=user_msg),
    ]

    llm = get_llm()
    response = invoke_with_retry(llm, messages, agent_name="developer")
    files_dict = extract_project_files(extract_text(response.content))

    # Ensure index.html references styles.css and app.js cleanly
    if "index.html" in files_dict:
        html = files_dict["index.html"]
        html = re.sub(r'<link[^>]+href=["\'](?:styles?\.css)["\'][^>]*>', '', html)
        html = re.sub(r'<script[^>]+src=["\'](?:scripts?|app)\.js["\'][^>]*></script>', '', html)
        if "</head>" in html:
            html = html.replace("</head>", '  <link rel="stylesheet" href="styles.css">\n</head>', 1)
        else:
            html = '<link rel="stylesheet" href="styles.css">\n' + html
        if "</body>" in html:
            html = html.replace("</body>", '  <script src="app.js"></script>\n</body>', 1)
        else:
            html = html + '\n<script src="app.js"></script>'
        if "</html>" not in html.lower():
            html += "\n</html>"
        files_dict["index.html"] = html

    # Write files to disk
    for fname in ("index.html", "styles.css", "app.js"):
        if fname in files_dict and files_dict[fname].strip():
            tools_by_name["write_file"].invoke({"path": fname, "content": files_dict[fname]})

    created_files = [str(p.relative_to(workspace_path)) for p in sorted(workspace_path.rglob("*")) if p.is_file()]
    summary_lines = [f"- `{f}` ({(workspace_path / f).stat().st_size} bytes)" for f in created_files]

    output_md = f"""### Developer Implementation (Round {iteration})

**Files Written to Disk:**
{chr(10).join(summary_lines) if summary_lines else "- No files found"}
"""
    emit("agent_output", agent="developer", text=output_md)
    emit("handoff", **{"from": "developer", "to": "reviewer", "label": "Code for review"})

    return {"files": created_files, "iteration": iteration}

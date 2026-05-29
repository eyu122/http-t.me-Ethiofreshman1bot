from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
import os, hmac, hashlib, time
from config import FILES_DIR, SECRET_KEY, BASE_URL

app = FastAPI()

def generate_token(filepath: str, expires_in=3600):
    expire_time = int(time.time()) + expires_in
    message = f"{filepath}:{expire_time}"
    sig = hmac.new(
        SECRET_KEY.encode(),
        message.encode(),
        hashlib.sha256
    ).hexdigest()
    return f"{expire_time}:{sig}"

def verify_token(filepath: str, token: str) -> bool:
    try:
        expire_time, sig = token.split(":", 1)
        if int(expire_time) < time.time():
            return False
        message = f"{filepath}:{expire_time}"
        expected = hmac.new(
            SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(sig, expected)
    except:
        return False

@app.get("/view/{category}/{filename}")
async def view_file(category: str, filename: str, token: str):
    filepath = f"{category}/{filename}"

    if not verify_token(filepath, token):
        raise HTTPException(status_code=403, detail="Link expired or invalid")

    full_path = os.path.join(FILES_DIR, category, filename)
    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="File not found")

    with open(full_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    safe_content = html_content.replace('"', '&quot;')

    viewer_html = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Viewer</title>
  <style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #1a1a1a; }}
    iframe {{ width: 100vw; height: 100vh; border: none; display: block; }}
  </style>
  <script>
    document.addEventListener('contextmenu', e => e.preventDefault());
    document.addEventListener('keydown', e => {{
      if ((e.ctrlKey || e.metaKey) && ['s','u','p'].includes(e.key.toLowerCase())) {{
        e.preventDefault();
      }}
    }});
  </script>
</head>
<body>
  <iframe srcdoc="{safe_content}" sandbox="allow-scripts allow-same-origin"></iframe>
</body>
</html>"""

    return HTMLResponse(
        content=viewer_html,
        headers={{
            "Cache-Control": "no-store, no-cache",
            "Content-Disposition": "inline",
        }}
    )

def get_view_url(category: str, filename: str) -> str:
    filepath = f"{category}/{filename}"
    token = generate_token(filepath)
    return f"{BASE_URL}/view/{category}/{filename}?token={token}"

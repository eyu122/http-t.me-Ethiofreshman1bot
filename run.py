import threading
import uvicorn
from bot import main as run_bot
from server import app as web_app

def start_server():
    uvicorn.run(web_app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    print("✅ Web server started!")
    print("✅ Bot is starting...")
    run_bot()

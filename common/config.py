import os

# Network config
MASTER_HOST = "0.0.0.0"
MASTER_PORT = 5000
DASHBOARD_PORT = 8000

# Worker config
DEFAULT_INTERVAL = 2.0

HEARTBEAT_TIMEOUT = 60.0   # seconds

# Path to save screenshots
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
SCREEN_SAVE_DIR = os.path.join(BASE_DIR, "master", "saved_screens")

os.makedirs(SCREEN_SAVE_DIR, exist_ok=True)

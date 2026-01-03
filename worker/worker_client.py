import socket
import time
import os
import sys
import psutil

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from common.config import MASTER_PORT, DEFAULT_INTERVAL

from worker.capture import capture_screen
from worker.utils.compress import compress_image
from worker.sender import send_message, start_command_listener

# USER CONFIG

MASTER_IP = "192.168.100.10"   # Change with our master server IP address  
WORKER_ID = "server_PC"          

ENABLE_COMMAND_LISTENER = False

current_interval = DEFAULT_INTERVAL

# System Stats

def get_system_stats():
    """Return CPU %, RAM %, system uptime."""
    try:
        cpu = psutil.cpu_percent(interval=0.0)   # Non-blocking
        ram = psutil.virtual_memory().percent
        uptime = time.time() - psutil.boot_time()
    except Exception:
        cpu, ram, uptime = "N/A", "N/A", "N/A"

    return cpu, ram, uptime


def set_interval(new_int):
    global current_interval
    current_interval = float(new_int)
    print(f"[WORKER {WORKER_ID}] Interval updated to {current_interval}s")

# Connection Handler

def connect_to_master():
    """Connect to master server with auto-retry """
    while True:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            print(f"[WORKER {WORKER_ID}] Connecting to master {MASTER_IP}:{MASTER_PORT} ...")
            sock.connect((MASTER_IP, MASTER_PORT))
            print(f"[WORKER {WORKER_ID}] Connected successfully!")
            return sock
        except Exception as e:
            try:
                sock.close()
            except Exception:
                pass
            print(f"[WORKER {WORKER_ID}] Failed to connect: {e}")
            print("[WORKER] Retrying in 5 seconds...")
            time.sleep(5)

# Main Worker Loop

def worker_loop(sock):
    """Main screenshot + data sending loop."""
    global current_interval

    if ENABLE_COMMAND_LISTENER:
        start_command_listener(sock, WORKER_ID, set_interval)

    while True:
        try:
            img_bytes = b""
            try:
                img = capture_screen()
                img_bytes = compress_image(img, quality=60)
            except Exception as e:
                print(f"[WORKER {WORKER_ID}] Screenshot failed: {e}")

            if not img_bytes:
                time.sleep(current_interval)
                continue

            # Get performance stats
            cpu, ram, uptime = get_system_stats()

            # Build header
            header = {
                "type": "screenshot",
                "worker_id": WORKER_ID,
                "timestamp": time.time(),
                "interval": current_interval,
                "format": "jpeg",
                "cpu": cpu,
                "ram": ram,
                "uptime": uptime
            }

            send_message(sock, header, img_bytes)
            time.sleep(current_interval)

        except (ConnectionResetError, ConnectionAbortedError, BrokenPipeError):
            print(f"[WORKER {WORKER_ID}] Lost connection to master!")
            try:
                sock.close()
            except Exception:
                pass
            return  

        except Exception as e:
            print(f"[WORKER {WORKER_ID}] Error in worker loop: {e}")
            time.sleep(2)

# Program Entry

def main():
    while True:
        sock = connect_to_master()
        worker_loop(sock)  


if __name__ == "__main__":
    main()

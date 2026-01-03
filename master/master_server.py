import socket
import threading
import json
import time
import os
import sys

# Path setup

CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
sys.path.append(PROJECT_ROOT)

from common.config import (
    MASTER_HOST,
    MASTER_PORT,
    SCREEN_SAVE_DIR,
    DASHBOARD_PORT
)

from master.utils.image_decode import decode_image
import master.dashboard as dashboard

# Global worker state

workers = {}
workers_lock = threading.Lock()

# Socket helpers

def recv_exact(conn, n):
    data = b""
    while len(data) < n:
        chunk = conn.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Socket closed")
        data += chunk
    return data


def recv_message(conn):
    header_len_bytes = recv_exact(conn, 4)
    header_len = int.from_bytes(header_len_bytes, "big")

    header_json = recv_exact(conn, header_len).decode()
    header = json.loads(header_json)

    payload_size = header.get("payload_size", 0)
    payload = b""
    if payload_size > 0:
        payload = recv_exact(conn, payload_size)

    return header, payload

# Worker update helper

def update_worker(worker_id, **kwargs):
    with workers_lock:
        info = workers.setdefault(
            worker_id,
            {
                "worker_id": worker_id,
                "status": "online",
                "last_timestamp": 0,
                "current_interval": 0,
                "cpu": "N/A",
                "ram": "N/A",
                "uptime": "N/A",
                "last_image_filename": None,
                "conn": None,
            },
        )
        info.update(kwargs)

# Client handler (receive-only thread)

def client_handler(conn, addr):
    print(f"[MASTER] Worker connected from {addr}")
    worker_id = None

    try:
        while True:
            header, payload = recv_message(conn)

            if header.get("type") != "screenshot":
                continue

            worker_id = header.get("worker_id")
            ts = header.get("timestamp", time.time())

            # Update worker metadata (heartbeat)
            update_worker(
                worker_id,
                status="online",
                last_timestamp=ts,
                current_interval=header.get("interval"),
                cpu=header.get("cpu", "N/A"),
                ram=header.get("ram", "N/A"),
                uptime=header.get("uptime", "N/A"),
                conn=conn,
            )

            # Save screenshot 
            if payload:
                try:
                    img = decode_image(payload)

                    # Ensure directory exists
                    os.makedirs(SCREEN_SAVE_DIR, exist_ok=True)
                    
                    fname = f"{worker_id}_{int(ts * 1000)}.jpg"
                    path = os.path.join(SCREEN_SAVE_DIR, fname)

                    img.save(path, "JPEG")

                    update_worker(
                        worker_id,
                        last_image_filename=fname,
                        last_timestamp=ts
                    )

                    print(f"[MASTER] Saved screenshot → {fname}")

                except Exception as e:
                    print(f"[MASTER] Image save failed: {e}")

    except Exception as e:
        print(f"[MASTER] Connection error: {e}")

    finally:
        if worker_id:
            with workers_lock:
                if worker_id in workers:
                    workers[worker_id]["status"] = "offline"
                    workers[worker_id]["conn"] = None

        try:
            conn.close()
        except Exception:
            pass

        print(f"[MASTER] Worker {worker_id} disconnected")

# TCP server
def start_tcp():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((MASTER_HOST, MASTER_PORT))
    server.listen()

    print(f"[MASTER] Listening on {MASTER_HOST}:{MASTER_PORT}")

    while True:
        conn, addr = server.accept()
        threading.Thread(
            target=client_handler,
            args=(conn, addr),
            daemon=True,
        ).start()

# MAIN
def main():
    
    dashboard.init(workers, None, SCREEN_SAVE_DIR)

    threading.Thread(
        target=dashboard.start,
        args=(DASHBOARD_PORT,),
        daemon=True,
    ).start()

    # Start TCP server
    start_tcp()


if __name__ == "__main__":
    main()

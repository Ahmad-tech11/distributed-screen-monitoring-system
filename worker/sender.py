import json
import threading


def send_message(sock, header, payload_bytes=None):
    """Send JSON header + optional binary payload."""
    if payload_bytes is None:
        payload_bytes = b""

    header["payload_size"] = len(payload_bytes)
    header_bytes = json.dumps(header).encode()

    try:
        sock.sendall(len(header_bytes).to_bytes(4, "big"))
        sock.sendall(header_bytes)

        if payload_bytes:
            sock.sendall(payload_bytes)

    except Exception as e:
        print(f"[WORKER] Error sending message: {e}")
        raise


def recv_exact(sock, n):
    """Receive exactly n bytes or raise connection error."""
    data = b""
    while len(data) < n:
        chunk = sock.recv(n - len(data))
        if not chunk:
            raise ConnectionError("Connection closed by master")
        data += chunk
    return data


def recv_message(sock):
    header_len_bytes = recv_exact(sock, 4)
    header_len = int.from_bytes(header_len_bytes, "big")

    header_json = recv_exact(sock, header_len).decode()
    header = json.loads(header_json)

    payload_size = header.get("payload_size", 0)
    payload = b""
    if payload_size > 0:
        payload = recv_exact(sock, payload_size)

    return header, payload


def start_command_listener(sock, worker_id, on_change_interval):
    """
    Listens to master commands in a separate thread.
    """

    def loop():
        while True:
            try:
                header, payload = recv_message(sock)

                if header.get("type") != "command":
                    continue

                action = header.get("action")

                # HANDLE INTERVAL UPDATE
                
                if action == "change_interval":
                    new_int = float(header.get("new_interval", 2))
                    print(f"[WORKER {worker_id}] Interval changed → {new_int}s")
                    on_change_interval(new_int)

                
                elif action == "ping":
                    print(f"[WORKER {worker_id}] PING received from master")

                elif action == "shutdown":
                    print(f"[WORKER {worker_id}] Shutdown command received.")
            except ConnectionError:
                print(f"[WORKER {worker_id}] Disconnected from master (command listener)")
                break

            except Exception as e:
                print(f"[WORKER {worker_id}] Command listener error: {e}")
                break

    threading.Thread(target=loop, daemon=True).start()

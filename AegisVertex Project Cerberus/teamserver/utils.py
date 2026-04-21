import ssl
import os
import secrets
from logger import logger


def load_ssl_context(cert_path: str, key_path: str) -> ssl.SSLContext:
    if not cert_path or not key_path:
        logger.error("SSL paths are empty.")
        return None

    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        logger.error(f"SSL certificate or key file not found at: {cert_path}")
        return None

    try:
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)

        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        context.options |= ssl.OP_NO_TLSv1
        context.options |= ssl.OP_NO_TLSv1_1

        context.set_ciphers('ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384')
        context.load_cert_chain(certfile=cert_path, keyfile=key_path)

        logger.info(f"SSL Context loaded successfully using {cert_path}")
        return context

    except ssl.SSLError as e:
        logger.error(f"Cryptographic error during SSL setup: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error loading SSL context: {e}")
        return None


def generate_beacon_id() -> str:
    return secrets.token_hex(4)
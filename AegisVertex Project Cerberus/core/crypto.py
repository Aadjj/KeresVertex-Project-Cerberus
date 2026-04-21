from cryptography.fernet import Fernet
import hashlib
import base64
from core.config import settings

class CerberusCrypto:
    def __init__(self):
        self.cipher = Fernet(settings.FERNET_KEY.encode())

    def encrypt(self, data: str) -> str:
        return self.cipher.encrypt(data.encode()).decode()

    def decrypt(self, token: str) -> str:
        return self.cipher.decrypt(token.encode()).decode()

    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

crypto = CerberusCrypto()
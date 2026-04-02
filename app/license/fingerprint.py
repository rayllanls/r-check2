"""Device fingerprint — vincula licença ao dispositivo."""
import hashlib
import platform
import uuid


def get_device_id() -> str:
    """ID único e estável do dispositivo. Sem dados pessoais."""
    raw = "|".join([
        platform.node(),
        platform.machine(),
        platform.processor(),
        str(uuid.getnode()),
    ])
    return hashlib.sha256(raw.encode()).hexdigest()[:32]

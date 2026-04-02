"""Cache de validação para uso offline."""
import time
from app.config import LICENSE_GRACE_HOURS


def is_within_grace_period(last_validated: float) -> bool:
    """Retorna True se ainda dentro do período de graça offline."""
    if last_validated == 0:
        return False
    elapsed_hours = (time.time() - last_validated) / 3600
    return elapsed_hours < LICENSE_GRACE_HOURS

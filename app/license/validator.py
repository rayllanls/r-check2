"""
Validação de licença.
Em DEV_MODE: sempre retorna válido sem bater na API.
"""
import time
from app.config import DEV_MODE, DEV_PLAN


class LicenseValidator:

    def validate(self, token: str = "") -> tuple[bool, str]:
        """
        Retorna (is_valid, plan).
        Em DEV_MODE sempre retorna (True, DEV_PLAN).
        """
        if DEV_MODE:
            return True, DEV_PLAN

        # TODO Fase 6: implementar validação real com a API
        raise NotImplementedError("Validação de licença implementar na Fase 6")

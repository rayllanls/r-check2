"""Testes do sistema de licença."""
import time
import pytest
from app.license.cache import is_within_grace_period
from app.license.fingerprint import get_device_id
from app.license.validator import LicenseValidator


def test_grace_period_recent() -> None:
    assert is_within_grace_period(time.time() - 3600) is True  # 1h atrás


def test_grace_period_expired() -> None:
    assert is_within_grace_period(time.time() - 80 * 3600) is False  # 80h atrás


def test_grace_period_never() -> None:
    assert is_within_grace_period(0.0) is False


def test_device_id_stable() -> None:
    assert get_device_id() == get_device_id()
    assert len(get_device_id()) == 32


def test_validator_dev_mode() -> None:
    """Em DEV_MODE o validator deve sempre retornar válido."""
    from app.config import DEV_MODE
    if DEV_MODE:
        valid, plan = LicenseValidator().validate()
        assert valid is True
        assert plan == "team"

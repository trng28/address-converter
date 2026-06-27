from .vietnam_address_converter import normalize as _impl
from .vietnam_address_converter.normalize import *  # noqa: F401,F403


def __getattr__(name: str):
    return getattr(_impl, name)

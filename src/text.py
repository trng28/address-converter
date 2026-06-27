from .vietnam_address_converter import text as _impl
from .vietnam_address_converter.text import *  # noqa: F401,F403


def __getattr__(name: str):
    return getattr(_impl, name)

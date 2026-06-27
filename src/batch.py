from .vietnam_address_converter import batch as _impl
from .vietnam_address_converter.batch import *  # noqa: F401,F403


def __getattr__(name: str):
    return getattr(_impl, name)

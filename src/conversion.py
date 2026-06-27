from .vietnam_address_converter import conversion as _impl
from .vietnam_address_converter.conversion import *  # noqa: F401,F403


def __getattr__(name: str):
    return getattr(_impl, name)

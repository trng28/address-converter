from .vietnam_address_converter import converter as _impl
from .vietnam_address_converter.converter import *  # noqa: F401,F403


def __getattr__(name: str):
    return getattr(_impl, name)

from .vietnam_address_converter import utils as _impl
from .vietnam_address_converter.utils import *  # noqa: F401,F403


def __getattr__(name: str):
    return getattr(_impl, name)

from __future__ import annotations

from vietnam_address_converter import __version__, auto_convert_address, create_converter


def test_package_imports() -> None:
    assert __version__
    assert callable(auto_convert_address)
    assert create_converter() is not None

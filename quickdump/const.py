from pathlib import Path
from typing import Optional, Union

from starlette.middleware.cors import ALL_METHODS as STARLETTE_METHODS

DUMP_FILE_EXTENSION = ".qd"

# Starlette Route is typed as taking a list[str] instead of tuple[str, ...]
ALL_METHODS = list(STARLETTE_METHODS)

_default_dump_dir: Path = Path.home() / ".quickdump"
_default_label = "default_dump"


def configure(
    default_path: Optional[Union[Path, str]] = None,
    default_label: Optional[str] = None,
) -> None:
    if default_path is not None:
        global _default_dump_dir
        _default_dump_dir = Path(default_path)

    if default_label is not None:
        global _default_label
        _default_label = default_label

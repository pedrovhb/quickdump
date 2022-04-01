from pathlib import Path
from typing import Optional, Any

from .const import configure
from .dumper import QuickDumper, iter_all_dumps, iter_dumps


def qd(
    *objs: Any,
    label: Optional[str] = None,
    output_dir: Optional[Path] = None,
    force_flush: bool = False,
) -> None:
    return QuickDumper(label, output_dir).dump(*objs, force_flush=force_flush)


__all__ = ("QuickDumper", "configure", "iter_dumps", "iter_all_dumps", "qd")

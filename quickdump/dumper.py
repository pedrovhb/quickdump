import gzip
import time
import zlib
from datetime import datetime
from functools import cached_property
from io import BufferedIOBase, BytesIO
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    ClassVar,
    Dict,
    Generator,
    Optional,
    Tuple,
    Type,
    TypeVar,
)

import dill
import pyzstd
from loguru import logger

from quickdump.const import (
    COMPRESSED_DUMP_FILE_EXTENSION,
    DEFAULT_DUMP_DIRNAME,
    DEFAULT_DUMP_LABEL,
    Suffix,
)


def _default_path() -> Path:
    return Path(Path.home() / DEFAULT_DUMP_DIRNAME)


T = TypeVar("T")


def _dill_load(stream: BufferedIOBase) -> Generator[Any, None, None]:
    while True:
        try:
            yield from dill.load(stream)
        except EOFError:
            break


class QuickDumper:
    label: str
    suffix: str
    output_dir: Path

    __instances: ClassVar[Dict[Tuple[str, str], "QuickDumper"]] = {}

    def __init__(
        self,
        label: str = DEFAULT_DUMP_LABEL,
        suffix: str = Suffix.NoSuffix,
        output_dir: Optional[Path] = None,
    ):
        if output_dir is None:
            output_dir = _default_path()

        self.label = label
        self.suffix = str(suffix)
        self.output_dir = output_dir

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            raise FileNotFoundError

        self._ctx_manager_open = False
        self._buffer = []

    def __enter__(self) -> "QuickDumper":
        self._ctx_manager_open = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self._ctx_manager_open = False
        self.dump(flush=True)

    def __new__(
        cls: Type["QuickDumper"],
        label: str = DEFAULT_DUMP_LABEL,
        suffix: str = Suffix.NoSuffix,
        output_dir: Optional[Path] = None,
    ) -> "QuickDumper":

        # Apply flyweight pattern (todo - double check)
        if (label, suffix) not in cls.__instances:
            obj = super().__new__(cls)
            cls.__init__(obj, label, suffix, output_dir)
            cls.__instances[(label, suffix)] = obj
        return cls.__instances[(label, suffix)]

    def render_suffix(self) -> str:
        return datetime.now().strftime(self.suffix)

    @cached_property
    def file_basename(self) -> str:
        if suffix := self.render_suffix():
            return f"{self.label}___{suffix}"
        return self.label

    @cached_property
    def compressed_file(self) -> Path:
        filename = f"{self.file_basename}.{COMPRESSED_DUMP_FILE_EXTENSION}"
        return Path(self.output_dir) / filename

    def dump(self, *objs: Any, flush: Optional[bool] = None) -> None:
        if (self._ctx_manager_open and flush is None) or flush is False:
            self._buffer.extend(objs)
        else:
            with pyzstd.ZstdFile(self.compressed_file, mode="ab") as comp_fd:
                if self._buffer:
                    dill.dump(self._buffer, comp_fd)
                    self._buffer = []
                if objs:
                    dill.dump(objs, comp_fd)

    def iter_dumped(self) -> Generator[Any, None, None]:
        for file in self.output_dir.iterdir():
            if not file.is_file():
                continue

            if file.suffix == f".{COMPRESSED_DUMP_FILE_EXTENSION}":
                yield from _dill_load(pyzstd.ZstdFile(file))

            else:
                logger.warning(f"Unrecognized file format {file.suffix}")

    __call__ = dump


if __name__ == "__main__":

    qd = QuickDumper("some_label")
    qd2 = QuickDumper("some_other_label")
    qd3 = QuickDumper("some_third_label")
    qd4 = QuickDumper("some_fourth_label")

    test_size = 10000

    t0 = time.perf_counter()
    for i in range(test_size):
        qd(("one", "two", i))
    t_non_ctx_manager = time.perf_counter() - t0

    t0 = time.perf_counter()
    with qd2:
        for i in range(test_size):
            qd2(("one", "two", i))
    t_ctx_manager = time.perf_counter() - t0

    t0 = time.perf_counter()
    qd3(*(("one", "two", i) for i in range(test_size)))
    t_starred = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(test_size):
        qd4(("one", "two", i), flush=False)
    qd4(flush=True)
    t_flush_once = time.perf_counter() - t0

    print("===================")
    print(f"Some label objs:")
    for dumped_obj in qd.iter_dumped():
        print(dumped_obj)

    print("===================")
    print(f"Some other label objs:")
    for dumped_obj in qd2.iter_dumped():
        print(dumped_obj)

    print(
        f"""
                {t_starred=}
            {t_ctx_manager=}
        {t_non_ctx_manager=}
             {t_flush_once=}
        """
    )

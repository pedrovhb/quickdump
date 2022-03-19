import gzip
from datetime import datetime
from functools import cached_property
from io import BytesIO
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
from loguru import logger

from .const import (
    COMPRESSED_DUMP_FILE_EXTENSION,
    DEFAULT_DUMP_DIRNAME,
    DEFAULT_DUMP_LABEL,
    DUMP_FILE_EXTENSION,
    ONE_MEGABYTE,
    Suffix,
)


def _default_path() -> Path:
    return Path.home() / DEFAULT_DUMP_DIRNAME


T: TypeVar = TypeVar("T")


def _dill_load(io_interface: BinaryIO) -> Generator[Any, None, None]:
    while True:
        try:
            yield dill.load(io_interface)
        except EOFError:
            break


class QuickDumper:
    label: str
    suffix: str
    output_dir: Path
    max_uncompressed_size: int

    __instances: ClassVar[Dict[Tuple[str, str], "QuickDumper"]] = {}

    def __init__(
        self,
        label: str = DEFAULT_DUMP_LABEL,
        suffix: str = Suffix.NoSuffix,
        output_dir: Optional[Path] = None,
        max_uncompressed_size: int = 10 * ONE_MEGABYTE,
    ):
        if output_dir is None:
            output_dir = _default_path()

        self.label = label
        self.suffix = str(suffix)
        self.output_dir = output_dir
        self.max_uncompressed_size = max_uncompressed_size

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            raise FileNotFoundError

    def __new__(
        cls: Type["QuickDumper"],
        label: str = DEFAULT_DUMP_LABEL,
        suffix: str = Suffix.NoSuffix,
        output_dir: Optional[Path] = None,
        max_uncompressed_size: int = 10 * ONE_MEGABYTE,
    ) -> "QuickDumper":
        if (label, suffix) not in cls.__instances:
            obj = super().__new__(cls)
            cls.__init__(obj, label, suffix, output_dir, max_uncompressed_size)
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
    def uncompressed_file(self) -> Path:
        filename = f"{self.file_basename}.{DUMP_FILE_EXTENSION}"
        return Path(self.output_dir) / filename

    @cached_property
    def compressed_file(self) -> Path:
        filename = f"{self.file_basename}.{COMPRESSED_DUMP_FILE_EXTENSION}"
        return Path(self.output_dir) / filename

    def dump(self, *objs: Any, skip_compression_check: bool = False) -> None:

        with self.uncompressed_file.open("ab") as fd_uncompressed:
            for obj in objs:
                dill.dump(obj, fd_uncompressed)

        if not skip_compression_check:
            if self._requires_compression():
                self._compress()

    def _compress(self) -> None:
        logger.info(f"Compressing QuickDump data for label {self.label}")

        # Open uncompressed data, and compress it into a binary blob
        with self.uncompressed_file.open("rb") as fd_uncompressed:
            blob = gzip.compress(fd_uncompressed.read())

        # Write compressed blob
        with self.compressed_file.open("ab") as fd_compressed:
            dill.dump(blob, fd_compressed)

        # Truncate uncompressed file
        self.uncompressed_file.write_bytes(b"")

    def _requires_compression(self) -> bool:
        stat = self.uncompressed_file.stat()
        return stat.st_size >= self.max_uncompressed_size

    def iter_dumped(self) -> Generator[Any, None, None]:
        for file in self.output_dir.iterdir():
            if not file.is_file():
                continue

            if file.suffix == f".{DUMP_FILE_EXTENSION}":
                with file.open("rb") as fd_uncompressed:
                    yield from _dill_load(fd_uncompressed)

            elif file.suffix == f".{COMPRESSED_DUMP_FILE_EXTENSION}":
                with file.open("rb") as fd_compressed:
                    blob = gzip.decompress(dill.load(fd_compressed))
                    yield from _dill_load(BytesIO(blob))

            else:
                logger.warning(f"Unrecognized file format {file.suffix}")

    __call__ = dump


if __name__ == "__main__":

    qd = QuickDumper("some_label")
    qd("abd")
    qd2 = QuickDumper("some_other_label")
    qd3 = QuickDumper("some_label", suffix=Suffix.Minute)

    qd2("fguhsugfdh", datetime.now())
    qd3("ufhgufhdus", datetime.now())

    print(qd is qd3)
    print(qd is qd2)

    for dumped_obj in qd.iter_dumped():
        print(dumped_obj)

    for dumped_obj in qd2.iter_dumped():
        print(dumped_obj)

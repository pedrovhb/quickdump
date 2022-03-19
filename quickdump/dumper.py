import gzip
from dataclasses import dataclass, field
from functools import cached_property
from io import BytesIO
from pathlib import Path
from typing import Any

import dill
import tqdm as tqdm
from loguru import logger


_MEGABYTE = 10 ** 6


def _default_path() -> Path:
    return Path.home() / ".quickdump"


@dataclass(frozen=True)
class QuickDumper:
    label: str = field(default="unlabeled_dump")
    output_dir: Path = field(default_factory=_default_path)
    max_uncompressed_size: int = field(default=10 * _MEGABYTE)

    def __post_init__(self):
        self._validate_output_dir()

    def _validate_output_dir(self) -> None:
        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True, exist_ok=True)
        if not self.output_dir.exists() or not self.output_dir.is_dir():
            raise FileNotFoundError

    @cached_property
    def file_basename(self) -> str:
        return self.label

    @cached_property
    def uncompressed_file(self) -> Path:
        return Path(self.output_dir) / f"{self.label}.qd"

    @cached_property
    def compressed_file(self) -> Path:
        return Path(self.output_dir) / f"{self.label}.cqd"

    def dump(self, *objs: Any, skip_compression_check: bool = False) -> None:

        with self.uncompressed_file.open("ab") as fd:
            for obj in objs:
                dill.dump(obj, fd)

        if not skip_compression_check:
            if self._requires_compression():
                self._compress()

    def _compress(self):
        logger.info(f"Compressing QuickDump data for label {self.label}")

        # Open uncompressed data, and compress it into a binary blob
        with self.uncompressed_file.open("rb") as fd:
            blob = gzip.compress(fd.read())

        # Write compressed blob
        with self.compressed_file.open("ab") as fd_compressed:
            dill.dump(blob, fd_compressed)

        # Truncate uncompressed file
        self.uncompressed_file.write_bytes(b"")

    def _requires_compression(self) -> bool:
        stat = self.uncompressed_file.stat()
        return stat.st_size >= self.max_uncompressed_size

    def _dill_load(self, fd):
        while True:
            try:
                yield dill.load(fd)
            except EOFError:
                break

    def iter_dumped(self):

        if self.compressed_file.exists():
            logger.info(f"Yielding from compressed file.")
            with self.compressed_file.open("rb") as fd:
                blob = gzip.decompress(dill.load(fd))
                yield from self._dill_load(BytesIO(blob))

        logger.info(f"Yielding from uncompressed file.")
        with self.uncompressed_file.open("rb") as fd:
            yield from self._dill_load(fd)

    __call__ = dump


if __name__ == "__main__":

    qd = QuickDumper("some_label")

    for i in tqdm.tqdm(range(1000000)):
        qd({"hello": f"world {i}"})

    for obj in qd.iter_dumped():
        print(obj)

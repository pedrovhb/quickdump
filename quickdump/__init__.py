import atexit
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, TypeAlias
from uuid import uuid4

import zstandard
from zstandard import ZstdCompressor
import dill
from loguru import logger
from pydantic import BaseModel, PrivateAttr, FilePath, Field
from ulid import ULID

CHUNK_SIZE = 32768


class AutoPrefix:
    @staticmethod
    def date():
        return datetime.now().strftime("%Y_%m_%d_")

    @staticmethod
    def datetime():
        return datetime.now().strftime("%Y_%m_%d__%H_%M_%S_")

    @staticmethod
    def uuid():
        return uuid4().hex

    @staticmethod
    def ulid():
        return ULID().hex


PrefixT: TypeAlias = tuple[str | Callable[[], str]]


class QuickDumper(BaseModel):
    file_name: str | Path = "dump.qd"
    output_dir: Path = Path.home() / ".quickdump"
    dump_every: timedelta | None = None

    file_prefixes: PrefixT = Field(default=(AutoPrefix.date, AutoPrefix.ulid))
    prefix_separator: str = "__"

    _crt_file_created_at: datetime = PrivateAttr(default_factory=datetime.now)
    _crt_file: Path | None = PrivateAttr(default=None)
    _file_unfinished: bool = PrivateAttr(default=False)
    _produced_files: set = PrivateAttr(default_factory=set)

    _zstd_chunker: "ZstdCompressionChunker" = PrivateAttr()  # type: ignore

    def get_auto_prefixes(self) -> list[str]:
        return [p() if callable(p) else p for p in self.file_prefixes]

    def get_output_file(self) -> Path:
        file_name: str
        file_dir: Path

        # Get the file name as a string
        if isinstance(self.file_name, Path):
            file_name = self.file_name.name
        else:
            file_name = self.file_name

        # Apply auto-prefix to file name, if applicable
        if auto_prefixes := self.get_auto_prefixes():
            file_name = self.prefix_separator.join((*auto_prefixes, file_name))

        # Get the file directory as a Path
        if (file_dir := self.output_dir) is None:
            if isinstance(self.file_name, Path):
                file_dir = self.file_name.parent
            else:
                file_dir = Path(".")

        # Build file Path obj
        file = file_dir / file_name

        # Add new file to the list of files created by this Dumper instance
        if file not in self._produced_files:
            self._produced_files.add(file)

        return file

    def _create_zstd_chunker(self):
        return ZstdCompressor().chunker(chunk_size=CHUNK_SIZE)

    @property
    def output_file(self) -> Path:
        """Current output file, as a Path object.

        If the dumper instance hasn't yet written to a file, or if this is the
        first time we access this property after the previous file has gone
        stale, a new file path is generated with `get_output_file` and returned.

        Returns:
            A path object with the current dump output location.

        """

        requires_new_file = self._crt_file is None

        if self.dump_every is not None:
            rotation_time = self._crt_file_created_at + self.dump_every
            if datetime.now() > rotation_time:
                requires_new_file = True

        if requires_new_file:

            if self._crt_file is not None:
                self._finish_file(self._crt_file)

            self._crt_file_created_at = datetime.now()
            self._crt_file = self.get_output_file()
            self._zstd_chunker = self._create_zstd_chunker()

            logger.info(f"Dumping to new file: {self._crt_file}")

        return self._crt_file

    @property
    def produced_files(self) -> set[Path]:
        """Set of files produced by the dumper so far."""
        return self._produced_files

    def add(self, *objs: Any) -> int:
        """Add one or more objects to the compressed file dump.

        Args:
            objs: The objects to be dumped to disk.

        Returns:
            The number of (compressed) bytes written to disk.
        """
        written = 0
        with (file := self.output_file.open("a+b")) as fd:
            for obj in objs:
                bin_obj = dill.dumps(obj)
                for out_chunk in self._zstd_chunker.compress(bin_obj):
                    written += fd.write(out_chunk)

        if not self._file_unfinished:
            self._file_unfinished = True
            atexit.register(self.finish)

        obj_count = f"{(l := len(objs))} object{'s' if l > 1 else ''}"
        logger.info(f"Dumped {obj_count} to {file} ({written} bytes).")

        return written

    def finish(self) -> int:
        """Finish compression and write finalizing data to disk.

        This method is scheduled to be run automatically at program exit. It
        can also be called manually

        Returns:
            The number of (compressed) bytes written to disk.

        """
        if not self._file_unfinished:
            logger.warning(f"Attempted to finish already finished file.")
            return
        return self._finish_file(self.output_file)

    def _finish_file(self, file: FilePath) -> int:
        written = 0
        with file.open("a+b") as fd:
            for out_chunk in self._zstd_chunker.finish():
                written += fd.write(out_chunk)

        logger.info(f"Finished writing to {file}.")
        self._file_unfinished = False
        atexit.unregister(self.finish)

        return written

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()


class QuickDumpLoader(BaseModel):
    input_file: Path

    def iter_objects(self):
        with open(self.input_file, "rb") as fh:
            dctx = zstandard.ZstdDecompressor()
            with dctx.stream_reader(fh) as reader:
                while True:
                    try:
                        yield dill.load(reader)
                    except EOFError:
                        return

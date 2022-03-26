import atexit
import time
from functools import cached_property
from itertools import chain
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Type, TypeAlias, Union

import cloudpickle
import structlog.stdlib
from lz4.frame import LZ4FrameFile

from quickdump.const import DUMP_FILE_EXTENSION, _default_dump_dir, _default_label
from quickdump.utils import slugify

DumpGenerator: TypeAlias = Generator[Any, None, None]


def _yield_objs(file: Path) -> DumpGenerator:
    with LZ4FrameFile(file, mode="rb") as compressed_fd:
        while True:
            try:
                yield from cloudpickle.load(compressed_fd)
            except EOFError:
                break


def iter_dumps(
    *labels: str,
    dump_location: Optional[Union[Path, str]] = None,
) -> DumpGenerator:
    selected_labels = labels or [_default_label]
    dump_location = Path(dump_location or _default_dump_dir)

    for label in selected_labels:
        if dump_location.is_file():
            file_path = dump_location
        else:
            filename = Path(label).with_suffix(DUMP_FILE_EXTENSION)
            file_path = dump_location / filename

        if QuickDumper.check_requires_flush(label):
            QuickDumper(label).flush()

        yield from _yield_objs(file_path)


def iter_all_dumps(dump_dir: Optional[Path] = None) -> DumpGenerator:
    dump_dir = dump_dir or Path(_default_dump_dir)

    for file in dump_dir.iterdir():
        if not file.is_file():
            continue
        if file.suffix == DUMP_FILE_EXTENSION:
            yield from _yield_objs(file)


class QuickDumper:
    label: str
    output_dir: Path
    _frame_file: LZ4FrameFile
    _requires_flush: bool

    _instances: Dict[str, "QuickDumper"] = {}

    def __new__(
        cls: Type["QuickDumper"],
        label: Optional[str] = None,
        output_dir: Optional[Path] = None,
    ) -> "QuickDumper":

        if label is None:
            label = _default_label
        label = slugify(label)

        # Apply flyweight pattern
        self = cls._instances.get(label)
        if self is None:
            self = object().__new__(cls)
            cls.initialize(self, label=label, output_dir=output_dir)
            cls._instances[label] = self

        return self

    @classmethod
    def initialize(
        cls,
        self,
        label: str,
        output_dir: Optional[Path] = None,
    ) -> None:

        self.label = label
        self.logger.info(f"Initializing QuickDumper for label {label}")

        out_dir = output_dir if output_dir is not None else _default_dump_dir
        self.output_dir = Path(out_dir)

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)

        if not self.output_dir.exists() or not self.output_dir.is_dir():
            raise FileNotFoundError

        self._frame_file = LZ4FrameFile(self.dump_file_path, mode="ab")
        self._requires_flush = False
        atexit.register(self.flush)

    @property
    def logger(self) -> structlog.stdlib.BoundLogger:
        logger = structlog.stdlib.get_logger(label=self.label)
        return logger

    @classmethod
    def check_requires_flush(cls, label: str) -> bool:
        if label in cls._instances:
            return cls._instances[label]._requires_flush
        return False

    @cached_property
    def dump_file_path(self) -> Path:
        filename = Path(self.label).with_suffix(DUMP_FILE_EXTENSION)
        return self.output_dir / filename

    def flush(self) -> None:
        if self._requires_flush:

            # region revert_me
            # todo - revert once patch to lz4 fixing flush is released
            self._frame_file.close()
            self._frame_file = LZ4FrameFile(
                self.dump_file_path, mode="ab", auto_flush=True
            )
            # endregion

            # self._frame_file.flush()  todo re-add
            self._requires_flush = False

    def iter_dumps(self) -> DumpGenerator:
        yield from iter_dumps(self.label, dump_location=self.dump_file_path)

    def dump(self, *objs: Any, force_flush: bool = False) -> None:
        cloudpickle.dump(objs, self._frame_file)
        self._requires_flush = True

        if force_flush:
            self.flush()

    __call__ = dump


if __name__ == "__main__":

    qd = QuickDumper("some_label")
    qd2 = QuickDumper("some_other_label")

    qd3 = QuickDumper("some_label")

    test_size = 10

    t0 = time.perf_counter()
    qd(*[("one", "two", i) for i in range(test_size)])
    t_one_dump = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(test_size):
        qd2(("one", "two", i * 2))
    t_multiple_dumps = time.perf_counter() - t0

    print("===================")
    print(f"Some label objs:")
    for dumped_obj in qd.iter_dumps():
        print(dumped_obj)

    print("===================")
    print(f"Some other label objs:")
    for dumped_obj in qd2.iter_dumps():
        print(dumped_obj)

    print(
        f"""
              t_one_dump: {t_one_dump}
        t_multiple_dumps: {t_multiple_dumps}
        """
    )

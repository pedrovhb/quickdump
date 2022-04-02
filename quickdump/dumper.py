import atexit
from functools import cached_property
from pathlib import Path
from typing import (
    Any,
    Dict,
    Generator,
    Optional,
    Type,
    TypeAlias,
    Union,
    Callable,
)

import dill
from loguru import logger
from lz4.frame import LZ4FrameFile

from quickdump.const import (
    DUMP_FILE_EXTENSION,
    _default_dump_dir,
    _default_label,
)
from quickdump.utils import slugify

DumpGenerator: TypeAlias = Generator[Any, None, None]


def _yield_objs(file: Path) -> DumpGenerator:
    logger.debug(f"Yielding objects from file {file}")
    with LZ4FrameFile(file, mode="rb") as compressed_fd:
        unpickler = dill.Unpickler(compressed_fd)
        # patched = partial(unpickler.dispatch.get, default=lambda a, b: str(b))
        # unpickler.dispatch.get = patched
        while True:
            try:
                yield from unpickler.load()
            except EOFError:
                break


def iter_dumps(
        *labels: str,
        dump_location: Optional[Union[Path, str]] = None,
        filter_fun: Optional[Callable[[Any], bool]] = None,
        raise_filter_fun_exceptions: bool = False,
) -> DumpGenerator:
    selected_labels = labels or [_default_label]
    dump_location = Path(dump_location or _default_dump_dir)

    logger.debug(
        f"Iterating over dumps for labels"
        f" {selected_labels} in {dump_location}"
    )

    for label in selected_labels:
        if dump_location.is_file():
            file_path = dump_location
        else:
            filename = Path(label).with_suffix(DUMP_FILE_EXTENSION)
            file_path = dump_location / filename

        if QuickDumper.check_requires_flush(label):
            QuickDumper(label).flush()

        if filter_fun is None:
            yield from _yield_objs(file_path)
        else:
            for obj in _yield_objs(file_path):
                try:
                    if filter_fun(obj):
                        yield obj
                except Exception as e:
                    logger.warning(
                        f"Exception raised while filtering "
                        f"dumps for {label} with function"
                        f" {filter_fun.__qualname__}: {e} (object: {obj})",
                    )
                    if raise_filter_fun_exceptions:
                        raise e


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
    _pickler: dill.Pickler

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
            self: "QuickDumper",
            label: str,
            output_dir: Optional[Path] = None,
    ) -> None:

        self.label = label
        logger.debug(f"Initializing QuickDumper for label {label}")

        out_dir = output_dir if output_dir is not None else _default_dump_dir
        self.output_dir = Path(out_dir)

        if not self.output_dir.exists():
            self.output_dir.mkdir(parents=True)

        if not self.output_dir.exists() or not self.output_dir.is_dir():
            raise FileNotFoundError

        self._frame_file = LZ4FrameFile(self.dump_file_path, mode="ab")
        self._requires_flush = False
        atexit.register(self.flush)

        self._pickler = dill.Pickler(self._frame_file)
        # self._patch_pickler(self._pickler)

    # def default_pickle_fun(self, pickler: Pickler, obj: Any) -> str:
    #     return str(obj)
    #
    # def _patch_pickler(self, pickler: dill.Pickler) -> None:
    #     patched = partial(pickler.dispatch.get, default=self.default_pickle_fun)
    #     pickler.dispatch.get = patched

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
        if not self._requires_flush:
            return

        if not self._frame_file.writable():
            return

        # region revert_me
        # todo - revert once patch to lz4 fixing flush is released
        #  https://github.com/python-lz4/python-lz4/pull/245
        self._frame_file.close()
        self._frame_file = LZ4FrameFile(
            self.dump_file_path,
            mode="ab",
            auto_flush=True,
        )
        self._pickler = dill.Pickler(self._frame_file)
        # endregion

        # self._frame_file.flush()  todo re-add after reverting above
        self._requires_flush = False

    def iter_dumps(
            self,
            *labels: str,
            filter_fun: Optional[Callable[[Any], bool]] = None,
            dump_location: Optional[Path] = None,
            reraise_filter_fun_exceptions: bool = False,
    ) -> DumpGenerator:

        if not labels:
            labels = (self.label,)

        if dump_location is None:
            dump_location = self.dump_file_path.parent

        yield from iter_dumps(
            *labels,
            dump_location=dump_location,
            filter_fun=filter_fun,
            raise_filter_fun_exceptions=reraise_filter_fun_exceptions,
        )

    def dump(
            self,
            *objs: Any,
            label: Optional[str] = None,
            force_flush: bool = False,
    ) -> None:

        if label is not None:
            return QuickDumper(
                label=label,
                output_dir=self.output_dir,
            ).dump(*objs, force_flush=force_flush)

        self._pickler.dump(objs)
        self._requires_flush = True

        self.flush()
        # if force_flush:
        #     self.flush()

    __call__ = dump

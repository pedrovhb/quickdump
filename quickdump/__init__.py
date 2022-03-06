import atexit
from datetime import datetime
from pathlib import Path
from random import randint
from typing import TypeAlias, Literal
from uuid import uuid4

import dill
import zstandard
from ulid import ULID

CHUNK_SIZE = 32768


AutoPrefix: TypeAlias = Literal["date", "datetime", "uid", "ulid", "none"]


class Dumper:
    def __init__(
        self,
        output_file: Path | str | None = None,
        file_prefix: str | None = None,
        auto_prefix: AutoPrefix = "none",
        use_quickdump_dir: bool = False,
    ):
        self.cctx = zstandard.ZstdCompressor()
        self.chunker = self.cctx.chunker(chunk_size=CHUNK_SIZE)

        now = datetime.now()
        match auto_prefix:
            case "none":
                auto_prefix = ""
            case "date":
                auto_prefix = now.strftime("%Y_%m_%d_")
            case "datetime":
                auto_prefix = now.strftime("%Y_%m_%d__%H_%M_%S_")
            case "uid":
                auto_prefix = uuid4().hex
            case "ulid":
                auto_prefix = ULID().hex
            case _:
                raise ValueError

        if isinstance(output_file, str):
            output_file = Path(output_file)

        file_prefix = f"{file_prefix}_" if file_prefix else ""
        auto_prefix = f"{auto_prefix}_" if auto_prefix else ""
        prefix = file_prefix + auto_prefix

        if output_file is None:
            # Remove trailing slash
            prefix = prefix[:-1]
            file = Path(prefix)
        else:
            file = output_file.with_name(f"{prefix}{output_file.name}")

        if use_quickdump_dir:
            qd_dir = Path.home() / ".quickdump"
            if not qd_dir.exists():
                qd_dir.mkdir()
            self.output_file = qd_dir / file.name
        else:
            self.output_file = file

        atexit.register(self.finish)

    def add(self, obj):
        bin_obj = dill.dumps(obj)
        for out_chunk in self.chunker.compress(bin_obj):
            with self.output_file.open("a+b") as fd:
                fd.write(out_chunk)

    def finish(self):
        atexit.unregister(self.finish)
        for out_chunk in self.chunker.finish():
            with self.output_file.open("a+b") as fd:
                fd.write(out_chunk)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.finish()


class DumpLoader:
    def __init__(self, input_file: Path):
        self.input_file = input_file

    def iter_objects(self):
        with open(self.input_file, "rb") as fh:
            dctx = zstandard.ZstdDecompressor()
            with dctx.stream_reader(fh) as reader:
                while True:
                    try:
                        yield dill.load(reader)
                    except EOFError:
                        return

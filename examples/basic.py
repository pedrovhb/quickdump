import random
import time
from dataclasses import dataclass
from datetime import datetime, timedelta

from quickdump import Dumper, DumpLoader


@dataclass
class SomeObj:
    a: int
    b: datetime
    c: bytes


if __name__ == "__main__":

    with Dumper(
        file_name="test_dump.qd",
        dump_every=timedelta(seconds=2),
    ) as dumper:

        for i in range(100):
            time.sleep(0.1)
            obj = SomeObj(i, datetime.now(), random.randbytes(10))
            print(f"Dumping obj: {obj}")
            dumper.add(obj)

        dumper.add({"hello!"}, [1, 2, 3])

    for file in dumper.produced_files:
        for loaded_obj in DumpLoader(input_file=file).iter_objects():
            print(loaded_obj)
    # Prints - SomeObj(a=0, b=datetime.datetime(2022, 3, 6, 12, 52, 28, 99256), c=b';?w\xeb\xaa}\xe8\xb9tJ')
    #          ...
    #          SomeObj(a=99, b=datetime.datetime(2022, 3, 6, 12, 52, 28, 175175), c=b'%\x93\xdc\x93\x9e\x08@\xed\xe1\n')
    # Saves the objects in one file in each run on the ~/.quickdump dir.

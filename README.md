# quickdump


Quickly store arbitrary Python objects in unique files.

* Files are appended to, so no data is lost
* Optionally generate unique file names based on current time/date, uid, 
or [ulid](https://github.com/mdomke/python-ulid)
* Optionally create and use a `~/.quickdump` hidden directory in the home folder

```python
import random
from dataclasses import dataclass
from datetime import datetime

from quickdump import Dumper, DumpLoader


@dataclass
class SomeObj:
    a: int
    b: datetime
    c: bytes


if __name__ == "__main__":

    with Dumper(
        file_prefix="some_obj",
        auto_prefix="ulid",
        use_quickdump_dir=True,
    ) as dumper:

        for i in range(100):
            dumper.add(SomeObj(i, datetime.now(), random.randbytes(10)))

    file = dumper.output_file

    for loaded_obj in DumpLoader(file).iter_objects():
        print(loaded_obj)
    # Prints - SomeObj(a=0, b=datetime.datetime(2022, 3, 6, 12, 52, 28, 99256), c=b';?w\xeb\xaa}\xe8\xb9tJ')
    #          ...
    #          SomeObj(a=99, b=datetime.datetime(2022, 3, 6, 12, 52, 28, 175175), c=b'%\x93\xdc\x93\x9e\x08@\xed\xe1\n')
    # Saves the objects in one file in each run on the ~/.quickdump dir.

```
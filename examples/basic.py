from dataclasses import dataclass
from datetime import datetime

from quickdump import QuickDumper


@dataclass
class SomeObj:
    a: int
    b: datetime
    c: str
    d: float
    dd: float


class Anotherobj(SomeObj):
    pass


if __name__ == "__main__":

    dumper = QuickDumper("some_label")
    dumper({"hello!"}, [1, 2, 3])

    print("================================")
    print("================================")
    print("== Reading values:")
    for loaded_obj in dumper.iter_dumps():
    print(loaded_obj)

    for loaded_obj in dumper.iter_dumps():
    print(loaded_obj)

    """
    Prints -
        2022-03-19 20:06:30.013 | INFO     | quickdump.dumper:split_suffix:135 - Iterating objects from label 
                                                                                 suffixed_label, file suffix 2022_03_19
        SomeObj(a=0, b=datetime.datetime(2022, 3, 19, 20, 6, 29, 771534), c='0558d9410f6f54edf4fa')
        SomeObj(a=1, b=datetime.datetime(2022, 3, 19, 20, 6, 29, 783656), c='6af57f2d09d6ec58abd6')
        SomeObj(a=4, b=datetime.datetime(2022, 3, 19, 20, 6, 29, 796162), c='c034256b754a5fff4421')
        SomeObj(a=9, b=datetime.datetime(2022, 3, 19, 20, 6, 29, 807980), c='bc06aeff5bba95aa3fdb')
        SomeObj(a=16, b=datetime.datetime(2022, 3, 19, 20, 6, 29, 819521), c='5883ded95317840428e4')
        ...
    """

    # Prints - SomeObj(a=0, b=datetime.datetime(2022, 3, 6, 12, 52, 28, 99256), c=b';?w\xeb\xaa}\xe8\xb9tJ')
    #          ...
    #          SomeObj(a=99, b=datetime.datetime(2022, 3, 6, 12, 52, 28, 175175), c=b'%\x93\xdc\x93\x9e\x08@\xed\xe1\n')
    # Saves the objects in one file in each run on the ~/.quickdump dir.

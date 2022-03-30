import time
from pathlib import Path

from quickdump import QuickDumper

if __name__ == "__main__":

    # todo -
    #  from quickdump import qd
    #  ...
    #  qd(obj, obj2, label="label")

    # qd = QuickDumper("some_label", output_dir=Path("."))
    qd2 = QuickDumper("some_other_label", output_dir=Path("."))

    qd3 = QuickDumper("some_label")

    test_size = 10

    t0 = time.perf_counter()
    # qd(*[("one", "two", i) for i in range(test_size)])
    t_one_dump = time.perf_counter() - t0

    t0 = time.perf_counter()
    for i in range(test_size):
        qd2([("one", "two", i * 2)])
    t_multiple_dumps = time.perf_counter() - t0

    print("===================")
    print(f"Some label objs:")
    # for dumped_obj in qd.iter_dumps():
    #     print(dumped_obj)

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

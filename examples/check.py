from quickdump import qd

a = "hello"
qd(a, label="test1")
qd("pedro", label="test1")


def filter_even_len(obj):
    if obj % 2 != 0:
        return False
    return True


for obj in qd.iter_dumps("mylabel"):
    print(obj)

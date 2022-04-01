import quickdump

qd = quickdump.QuickDumper("mitm_test")

for obj in qd.iter_dumps():
    if not isinstance(obj, tuple):
        print(obj)
print("hi!")

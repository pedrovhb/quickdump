import quickdump

qd = quickdump.QuickDumper("mitm_test")

for obj in qd.iter_dumped():
    if not isinstance(obj, tuple):
        print(obj)
print("hi!")

from decimal import Decimal

from quickdump import qd, QuickDumper

# Quickly dump (almost) any object you like
for i in range(10):
    result = Decimal(i) ** Decimal("0.5")
    qd(result)

# And use them whenever it's convenient later
for obj in qd.iter_dumps():
    print(obj)

# Dump objects assigning a label
qd("Armação", "Campeche", "Solidão", label="beaches")

# Or create a dumper with a pre-configured label
beach_dumper = QuickDumper("beaches")
beach_dumper("Morro das Pedras", "Açores", "Gravatá")

# Iterate over multiple labels (including the default):
for obj in qd.iter_dumps("beaches", "default_dump"):
    print(obj)


# Iterate only over objects that match some filter
def filter_initial_a(obj):
    return not obj.startswith("A")


for obj in qd.iter_dumps("beaches", filter_fun=filter_initial_a):
    print(obj)

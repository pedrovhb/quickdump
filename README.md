# quickdump

Quickly store arbitrary Python objects in local files.

*Library status - this is an experimental work in progress that hasn't been
battle-tested at all. The API will change often between versions, and you may
lose all your data due to silly bugs.*

---

### Features

- Store arbitrary objects locally
- No config or boilerplate required
- Dump to TCP server
- Dump to HTTP server

### Notes

(todo - rewrite this in a coherent manner)

- Currently, compression is applied per call to `dump`. This isn't very
  efficient (probably?)
- Labels are slugified to prevent errors from invalid characters in the filename

---
Quickly dump (almost) any object you like:

```python
from quickdump import qd, QuickDumper
from decimal import Decimal

for i in range(10):
      result = Decimal(i) ** Decimal("0.5")
      qd(result)
```

And use them whenever it's convenient later:

```python
for obj in qd.iter_dumps():
      print(obj)  # 0
      # 1.000000000000000000000000000
      # 1.414213562373095048801688724
      # ...
```

Dump objects assigning a label, or create a dumper with a pre-configured label:

```python
qd("Armação", "Campeche", "Solidão", label="beaches")

beach_dumper = QuickDumper("beaches")
beach_dumper("Morro das Pedras", "Açores", "Gravatá")
```

Iterate over multiple labels (including the default):

```python
for obj in qd.iter_dumps("beaches", "default_dump"):
      print(obj)
```

Iterate only over objects that match some filter:

```python
def filter_initial_a(obj):
      return not obj.startswith("A")


for obj in qd.iter_dumps("beaches", filter_fun=filter_initial_a):
      print(obj)  # Campeche
      # ...
```

## Someday™

- [ ] Enable simple serialization of unpicklable types (e.g. save a `socket`
  type property of some object as `socket`'s string representation instead of
  just ignoring the object)
- [ ] Quickdump by piping from shell
- [ ] Function decorator able to log function inputs and/or outputs
- [ ] Real time visualization of dumped data and metadata

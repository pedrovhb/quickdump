# quickdump

Quickly store arbitrary Python objects in unique files.

*Library status - this is an experimental work in progress that hasn't been
battle-tested at all. The API may change often between versions, and you may
lose all your data.*

---

### Features

- Store arbitrary objects with `cloudpickle` locally
- No config or boilerplate required
- Dump from TCP server
- Dump from HTTP server

### Notes
(todo - rewrite this in a coherent manner)

  - If an object from a library is dumped, the Python interpreter (or virtual
    environment) must have the library installed.
  - Currently, compression is applied per call to `dump`. This isn't very efficient.
  - Labels are slugified to prevent errors from invalid characters in the filename.

---
```python
from quickdump import QuickDumper, iter_dumps

if __name__ == "__main__":
    qd = QuickDumper("some_label")
    test_size = 1000
    qd(*[("one", "two", i) for i in range(test_size)])

    # In a separate run...
    
    for obj in iter_dumps("some_label"):
        print(obj)
    # or:
    for obj in qd.iter_dumps():
        print(obj)
```

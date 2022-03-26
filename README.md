# quickdump

Quickly store arbitrary Python objects in unique files.

*Library status - this is an experimental work in progress that hasn't been
battle-tested at all. The API may change often between versions, and you may
lose all your data.*

---

- If an object from a library is dumped, the Python interpreter (or virtual
  environment) must have the library installed.

```python
from datetime import datetime
from quickdump import QuickDumper


class MyObj:

    def __init__(self, first, second):
        self.first = first
        self.second = second

    @property
    def doubled_second(self):
        return self.second * 2


if __name__ == "__main__":
    with QuickDumper("some_obj") as qd:
        for i in range(100):
            obj = MyObj(first=datetime.now(), second=i)
            qd(obj)
    
    ... 
    
    for obj in QuickDumper("some_obj").iter_dumped():
        print(obj, obj.doubled_second)
```

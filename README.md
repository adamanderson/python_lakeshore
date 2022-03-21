# python_lakeshore
Some python classes for control of Lakeshore devices. The Lakeshore 350 and 218 temperature controllers are currently supported.

## Usage
Instantiate a client (e.g. for a Lakeshore 350 temperature controller:
```
from driver import Lakeshore350
device = Lakeshore350('192.168.0.13', ['A', 'B', 'C', 'D'])
```
Get the temperature:
```
t = box.get_temps()
print(t)
```

# lufft-python
A Python API/driver for communication to Weatherstations made by the German company Lufft (e.g. WS600-UMB) via Serial-Port
It implements their Lufft UMB-Protocol. You just need a USB-to-RS485 dongle and connect it to your PWS according to the wiring diagram you find in the manual.

This class does not replace the UMB-config-tool, because its not able to set the config values in your PWS at the moment.

## Usage

### In your python-script

```python
from WS_UMB import WS_UMB

with WS_UMB() as umb:
    value, status = umb.onlineDataQuery(SomeChannelNumber)
    if status != 0:
        print(umb.checkStatus(status))
    else:
        print(value)
```
### As a standalone python-program:

```shell
$ ./WS_UMB.py 100 111 200 300 460 580
```

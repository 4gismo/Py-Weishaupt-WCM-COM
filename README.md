# Py-Weishaupt-WCM-COM

[![PyPI - License](https://img.shields.io/github/license/4gismo/Py-Weishaupt-WCM-COM)](LICENSE)

Python library for reading process values from **Weishaupt WCM-COM** heating system network modules.

Used as the backend for the [HA-Weishaupt-WCM-COM](https://github.com/4gismo/HA-Weishaupt-WCM-COM) Home Assistant integration.

---

## Protocol

Communicates with the WCM-COM module via **HTTP POST** with **HTTP Digest Authentication**. Requests and responses use a proprietary JSON telegram format (`"prot": "coco"`).

Each parameter is identified by a numeric ID. The response bytes are decoded as signed/unsigned 16-bit or 32-bit integers and converted to engineering values (temperatures divided by 10, etc.).

---

## Parameters Read

| ID | Name | Type | Unit |
|---|---|---|---|
| 1 | Error | VALUE | — |
| 2 | Heat Demand | TEMP | °C |
| 5 | Room Temperature | TEMP | °C |
| 8 | Mixed External Temperature | TEMP | °C |
| 12 | Outside Temperature | TEMP | °C |
| 14 | Warm Water Temperature | TEMP | °C |
| 81 | Flame | VALUE | — |
| 82 | Heating | VALUE | — |
| 83 | Warm Water | VALUE | — |
| 118 | Buffer Sensor B10 | TEMP | °C |
| 274 | Operation Mode | VALUE | — |
| 325 | Flue Gas Temperature | TEMP | °C |
| 373 | Operation Phase | VALUE | — |
| 466 | Pump | VALUE | — |
| 700 | Time Since Last Service | VALUE | h |
| 1497 | Gas Valve 1 | VALUE | — |
| 1498 | Gas Valve 2 | VALUE | — |
| 2572 | Damped Outside Temperature | TEMP | °C |
| 3101 | Flow Temperature | TEMP | °C |
| 3158 | Burner Starts | VALUE32 | — |
| 3159 | Burner Hours | VALUE32 | h |
| 3793 | Oil Meter (low) | VALUE | L |
| 4176 | Load Setting | DECIMAL | kW |

---

## Installation

```bash
pip install git+https://github.com/4gismo/Py-Weishaupt-WCM-COM.git@master
```

---

## Usage

```python
from weishaupt_wcm_com import heat_exchanger
import json

result = heat_exchanger.process_values("192.168.1.100", "user", "password")
data = json.loads(result)
print(data["Flow Temperature"])   # e.g. 65.3
print(data["Outside Temperature"])  # e.g. 8.2
```

`process_values()` returns a JSON string on success, or raises an exception on connection/auth/format errors.

---

## License

Apache License 2.0 — see [LICENSE](LICENSE)

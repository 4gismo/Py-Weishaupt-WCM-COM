# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

→ See also: [Root CLAUDE.md](../CLAUDE.md)

## Purpose

Pure Python library that communicates with the Weishaupt WCM-COM heating module. Used as the backend dependency for `HA-Weishaupt-WCM-COM`. Published via pip from the `master` branch.

## Install & Build

```bash
pip install -e .                  # local editable install
pip install requests              # only runtime dependency
make build                        # build sdist + wheel
```

## Key File: `weishaupt_wcm_com/heat_exchanger.py`

All logic lives in this single file:

- **`QUERYTELEGRAM_1`** (18 params) / **`QUERYTELEGRAM_2`** (12 params) — two JSON telegram strings sent to `/parameter.json`. Split is required because the device silently ignores parameters beyond ~19 valid IDs per request.
- **`QUERIES`** — list of `[id, name, type, scale?]`. Name must exactly match the key string used in the HA component's `const.py`. Scale (optional 4th element) multiplies the decoded value.
- **`_process_telegram(telegram, result)`** — inner loop; writes decoded values into `result` dict.
- **`process_values(server, username, password)`** — makes two HTTP POST requests, merges results, **returns a `dict`** directly. Raises on any error (caller in `api.py` handles exceptions).
- **`set_operating_mode(server, username, password, mode_value)`** — writes parameter 274 (Betriebsart HK) using a type-6 write telegram (command byte 2 instead of 1).

## Protocol Details

- Endpoint: `POST http://<host>/parameter.json`
- Auth: HTTP Digest Auth
- Request body: `{"prot":"coco","telegramm":[...]}` — array of parameter requests
- Telegram formats:
  - 8-byte: `[10, 0, 1, ID, 0, 0, 0, 0]` — most parameters (read)
  - 6-byte: `[6, 0, 1, ID, 0, 0]` — used for IDs 5, 8, 274 (read)
  - Write: same format with command byte `2` instead of `1`; value at bytes 6/7
- Response: device always returns 8-byte messages; values at positions `message[6]` (low) and `message[7]` (high)
- Oil Meter uses two IDs: `3793` (low word, VALUE) + `3792` (high × 1000)

## Decoding

```
TEMP          → _to_int16(b6, b7) / 10.0   (signed, e.g. 200 → 20.0°C)
VALUE         → (b6 | b7<<8)               (unsigned integer, no division)
DECIMAL_VALUE → (b6 | b7<<8) / 10.0
scale factor  → result *= scale             (e.g. Brennerstarts: 138 × 1000 = 138000)
```

**Important:** Some parameters use VALUE type even though their unit is °C — e.g. ID 3102 (Sonderniveau Heizbetrieb, P18) returns raw 60 = 60°C with no division.

## Current Parameter List

| ID | Name | Type | Notes |
|---|---|---|---|
| 1 | Error | VALUE | |
| 2 | Heat Demand | TEMP | |
| 5 | Room Temperature | TEMP | 6-byte telegram; Normal-Raumtemp setpoint |
| 8 | Mixed External Temperature | TEMP | 6-byte telegram; Absenk-Raumtemp setpoint |
| 12 | Outside Temperature | TEMP | |
| 14 | Warm Water Temperature | TEMP | |
| 31 | Min Flow Temp | TEMP | P30 |
| 34 | Flow Temp Hysteresis | DECIMAL_VALUE | P32 |
| 39 | Max Flow Temp | TEMP | P31 |
| 81 | Flame | VALUE | 0/1 |
| 82 | Heating | VALUE | 0/1 |
| 83 | Warm Water | VALUE | 0/1 |
| 138 | Burner Load | VALUE | % |
| 274 | Operating Mode | VALUE | 6-byte telegram; writable via `set_operating_mode()` |
| 323 | Burner Lockout Time | VALUE | P34, min |
| 325 | Flue Gas Temperature | TEMP | |
| 345 | Max DHW Output | DECIMAL_VALUE | P38, % |
| 373 | Operating Phase | VALUE | |
| 384 | Max DHW Charge Time | VALUE | P52, min |
| 466 | Pump | VALUE | 0/1 |
| 700 | Time Since Last Service | VALUE ×10 | hours |
| 1497 | Gas Valve 1 | VALUE | 0/1 |
| 1498 | Gas Valve 2 | VALUE | 0/1 |
| 2560 | System Frost Protection | TEMP | P23 |
| 3101 | Flow Temperature | TEMP | |
| 3102 | Heating Special Level | VALUE | P18; raw value = °C, no division |
| 3158 | Burner Starts | VALUE ×1000 | |
| 3159 | Burner Hours | VALUE ×100 | hours |
| 3793/3792 | Oil Meter | VALUE (combined) | L |

## Discovering New Parameters

HTML element IDs in the device's web interface XML source are hex-encoded protocol IDs:
`idT0C1D` → `0x0C1D` → `3101` → Vorlauftemperatur.

Use `scan_parameters.py` (Mac/Linux) or `scan_parameters_windows.py` (Windows) to scan IDs 0–9999. Batch size must stay ≤ 15.

```bash
python3 scan_parameters.py <host> <username> <password>
```

## Syntax Check

```bash
python3 -c "import ast; ast.parse(open('weishaupt_wcm_com/heat_exchanger.py').read()); print('OK')"
```

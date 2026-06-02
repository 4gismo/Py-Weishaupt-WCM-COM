import requests
import json
import logging
from requests.auth import HTTPDigestAuth

_LOGGER = logging.getLogger(__name__)

ENDPOINT = "/parameter.json"

# Two separate requests — device processes max ~19 valid parameters per request
QUERYTELEGRAM_1 = (
    '{"prot":"coco","telegramm":[[10,0,1,3793,0,0,0,0],[10,0,1,3792,0,0,0,0],[10,0,1,12,0,0,0,0],[10,0,1,14,0,0,0,0],[10,0,1,3101,0,0,0,0],[10,0,1,325,0,0,0,0],[6,0,1,5,0,0],[6,0,1,274,0,0],[6,0,1,8,0,0],[10,0,1,81,0,0,0,0],[10,0,1,1497,0,0,0,0],[10,0,1,1498,0,0,0,0],[10,0,1,466,0,0,0,0],[10,0,1,82,0,0,0,0],[10,0,1,83,0,0,0,0],[10,0,1,1,0,0,0,0],[10,0,1,373,0,0,0,0],[10,0,1,2,0,0,0,0]]}'
)
QUERYTELEGRAM_2 = (
    '{"prot":"coco","telegramm":[[10,0,1,3102,0,0,0,0],[10,0,1,700,0,0,0,0],[10,0,1,3158,0,0,0,0],[10,0,1,3159,0,0,0,0]]}'
)

VALUE = 1
TEMP = 2
DECIMAL_VALUE = 3

# ID, Name, Type, Scale (optional — result is multiplied by scale)
QUERIES = [
    [3793, "Oil Meter", VALUE],
    [12, "Outside Temperature", TEMP],
    [14, "Warm Water Temperature", TEMP],
    [3101, "Flow Temperature", TEMP],
    [3102, "Return Temperature", TEMP],
    [325, "Flue Gas Temperature", TEMP],
    [5, "Room Temperature", TEMP],
    [274, "Operating Mode", VALUE],
    [8, "Mixed External Temperature", TEMP],
    [81, "Flame", VALUE],
    [1497, "Gas Valve 1", VALUE],
    [1498, "Gas Valve 2", VALUE],
    [466, "Pump", VALUE],
    [82, "Heating", VALUE],
    [83, "Warm Water", VALUE],
    [1, "Error", VALUE],
    [373, "Operating Phase", VALUE],
    [2, "Heat Demand", TEMP],
    [700, "Time Since Last Service", VALUE],
    [3158, "Burner Starts", VALUE, 1000],
    [3159, "Burner Hours", VALUE, 100],
]

def _to_int16(lowByte, highByte):
    raw = (lowByte & 0xFF) | ((highByte & 0xFF) << 8)
    if raw >= 0x8000:
        raw -= 0x10000
    return raw

def getTemperture(lowByte, highByte):
    return _to_int16(lowByte, highByte) / 10.0

def getValue(lowByte, highByte):
    return (lowByte & 0xFF) | ((highByte & 0xFF) << 8)

def getDecimalValue(lowByte, highByte):
    return ((lowByte & 0xFF) | ((highByte & 0xFF) << 8)) / 10.0

def _process_telegram(telegram, result):
    for message in telegram:
        for reading in QUERIES:
            if message[3] == reading[0]:
                scale = reading[3] if len(reading) > 3 else 1
                if reading[2] == TEMP:
                    result[reading[1]] = getTemperture(message[6], message[7])
                elif reading[2] == VALUE:
                    result[reading[1]] = getValue(message[6], message[7]) * scale
                elif reading[2] == DECIMAL_VALUE:
                    result[reading[1]] = getDecimalValue(message[6], message[7]) * scale
        if message[3] == 3792:
            result["Oil Meter"] = result.get("Oil Meter", 0) + message[6] * 1000

def set_operating_mode(server, username, password, mode_value: int):
    """Write Operating Mode HK (parameter 274) to the device.

    Uses type-6 telegram matching the read format for ID 274 ([6,0,1,274,0,0]),
    with command byte 2 (write) instead of 1 (read).
    """
    try:
        auth = HTTPDigestAuth(username, password)
        url = "http://" + server + ENDPOINT
        telegram = json.dumps({
            "prot": "coco",
            "telegramm": [[6, 0, 2, 274, 0, 0, mode_value & 0xFF, (mode_value >> 8) & 0xFF]]
        })
        req = requests.post(url, auth=auth, data=telegram, timeout=5)
        req.raise_for_status()
    except requests.exceptions.ConnectionError as e:
        _LOGGER.error("WCM-COM connection failed when setting operating mode: %s", e)
        raise
    except requests.exceptions.Timeout as e:
        _LOGGER.error("WCM-COM request timed out when setting operating mode: %s", e)
        raise
    except requests.exceptions.HTTPError as e:
        _LOGGER.error("WCM-COM HTTP error when setting operating mode: %s", e)
        raise
    except requests.exceptions.RequestException as e:
        _LOGGER.error("WCM-COM request failed when setting operating mode: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("WCM-COM unexpected error when setting operating mode: %s", e)
        raise


def process_values(server, username, password):
    try:
        result = {}
        auth = HTTPDigestAuth(username, password)
        url = "http://" + server + ENDPOINT

        for telegram_str in [QUERYTELEGRAM_1, QUERYTELEGRAM_2]:
            req = requests.post(url, auth=auth, data=telegram_str, timeout=5)
            _process_telegram(json.loads(req.text)["telegramm"], result)

        return json.dumps(result)
    except requests.exceptions.ConnectionError as e:
        _LOGGER.error("WCM-COM connection failed (host unreachable?): %s", e)
        raise
    except requests.exceptions.Timeout as e:
        _LOGGER.error("WCM-COM request timed out after 5s: %s", e)
        raise
    except requests.exceptions.HTTPError as e:
        _LOGGER.error("WCM-COM HTTP error (wrong credentials?): %s", e)
        raise
    except requests.exceptions.RequestException as e:
        _LOGGER.error("WCM-COM request failed: %s", e)
        raise
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        _LOGGER.error("WCM-COM unexpected response format: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("WCM-COM unexpected error: %s", e)
        raise

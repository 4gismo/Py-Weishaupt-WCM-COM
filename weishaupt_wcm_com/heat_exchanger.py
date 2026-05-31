import requests
import json
import logging
from requests.auth import HTTPDigestAuth

_LOGGER = logging.getLogger(__name__)


ENDPOINT = "/parameter.json"
QUERYTELEGRAM = (
    '{"prot":"coco","telegramm":[[10,0,1,4176,0,0,0,0],[10,0,1,3793,0,0,0,0],[10,0,1,3792,0,0,0,0],[10,0,1,12,0,0,0,0],[10,0,1,14,0,0,0,0],[10,0,1,3101,0,0,0,0],[10,0,1,325,0,0,0,0],[10,0,1,3197,0,0,0,0],[6,0,1,5,0,0],[6,0,1,274,0,0],[6,0,1,8,0,0],[10,0,1,81,0,0,0,0],[10,0,1,1497,0,0,0,0],[10,0,1,1498,0,0,0,0],[10,0,1,466,0,0,0,0],[10,0,1,82,0,0,0,0],[10,0,1,83,0,0,0,0],[10,0,1,1,0,0,0,0],[10,0,1,373,0,0,0,0],[10,0,1,2,0,0,0,0],[10,0,1,118,0,0,0,0],[10,0,1,700,0,0,0,0],[10,0,1,2572,0,0,0,0],[10,0,1,3158,0,0,0,0],[10,0,1,3159,0,0,0,0]]}'
)

VALUE = 1
TEMP = 2
DECIMAL_VALUE = 3
VALUE32 = 4

# ID, Name, Type
QUERIES = [
    [3793, "Oil Meter", VALUE],
    [4176, "Load Setting", DECIMAL_VALUE],
    [12, "Outside Temperature", TEMP],
    [14, "Warm Water Temperature", TEMP],
    [3101, "Flow Temperature", TEMP],
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
    [118, "Buffer Sensor B10", TEMP],
    [700, "Time Since Last Service", VALUE],
    [2572, "Damped Outside Temperature", TEMP],
    [3158, "Burner Starts", VALUE32],
    [3159, "Burner Hours", VALUE32],
]

def _to_int16(lowByte, highByte):
    raw = (lowByte & 0xFF) | ((highByte & 0xFF) << 8)   # 256 * highByte
    if raw >= 0x8000:  # signed 16-bit
        raw -= 0x10000
    return raw

def getTemperture(lowByte, highByte):
    return _to_int16(lowByte, highByte) / 10.0

def getValue(lowByte, highByte):
    return (lowByte & 0xFF) | ((highByte & 0xFF) << 8)

def getDecimalValue(lowByte, highByte):
    return ((lowByte & 0xFF) | ((highByte & 0xFF) << 8)) / 10.0

def getValue32(b4, b5, b6, b7):
    return (b4 & 0xFF) | ((b5 & 0xFF) << 8) | ((b6 & 0xFF) << 16) | ((b7 & 0xFF) << 24)

def process_values(server, username, password):
    try:
        req = requests.post(
            "http://" + server + ENDPOINT,
            auth=HTTPDigestAuth(username, password),
            data=QUERYTELEGRAM,
            timeout=5)
        telegram = json.loads(req.text)["telegramm"]
        for message in telegram:
            _LOGGER.warning("RAW id=%s bytes=%s", message[3], message[4:])
        result = {}
        for message in telegram:
            for reading in QUERIES:
                if message[3] == reading[0]:
                    if reading[2] == TEMP:
                        result[reading[1]] = getTemperture(message[6], message[7])
                    elif reading[2] == VALUE:
                        result[reading[1]] = getValue(message[6], message[7])
                    elif reading[2] == DECIMAL_VALUE:
                        result[reading[1]] = getDecimalValue(message[6], message[7])
                    elif reading[2] == VALUE32:
                        result[reading[1]] = getValue32(message[4], message[5], message[6], message[7])
            # special handling for oil meter high byte (ID 3792 adds 1000s to ID 3793 low value)
            if message[3] == 3792:
                result["Oil Meter"] = result.get("Oil Meter", 0) + message[6] * 1000
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
        _LOGGER.error("WCM-COM request error: %s", e)
        raise
    except (KeyError, IndexError, json.JSONDecodeError) as e:
        _LOGGER.error("WCM-COM unexpected response format: %s", e)
        raise
    except Exception as e:
        _LOGGER.error("WCM-COM unexpected error: %s", e)
        raise


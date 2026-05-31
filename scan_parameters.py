"""
Weishaupt WCM-COM Parameter Scanner
Scans all IDs 0-9999 and reports which ones the device responds to.

Usage:
    python3 scan_parameters.py <host> <username> <password>

Example:
    python3 scan_parameters.py 192.168.1.100 user password
"""

import json
import sys
import time
import requests
from requests.auth import HTTPDigestAuth

ENDPOINT = "/parameter.json"
BATCH_SIZE = 15
TIMEOUT = 10


def scan(host, username, password, id_from=0, id_to=9999):
    found = {}
    total = id_to - id_from + 1
    batches = range(id_from, id_to + 1, BATCH_SIZE)

    print(f"Scanning IDs {id_from}–{id_to} on http://{host}")
    print(f"Batch size: {BATCH_SIZE} | Batches: {len(list(batches))} | Est. time: ~{len(list(batches))}s\n")

    for batch_start in range(id_from, id_to + 1, BATCH_SIZE):
        batch_ids = list(range(batch_start, min(batch_start + BATCH_SIZE, id_to + 1)))

        telegram = json.dumps({
            "prot": "coco",
            "telegramm": [[10, 0, 1, id, 0, 0, 0, 0] for id in batch_ids]
        })

        try:
            resp = requests.post(
                f"http://{host}{ENDPOINT}",
                auth=HTTPDigestAuth(username, password),
                data=telegram,
                timeout=TIMEOUT,
            )
            messages = json.loads(resp.text).get("telegramm", [])

            returned_ids = {m[3] for m in messages}
            for msg in messages:
                id_ = msg[3]
                if id_ in batch_ids:  # only report IDs we requested
                    found[id_] = msg[4:]

        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] batch {batch_start}–{batch_ids[-1]}")
            continue
        except Exception as e:
            print(f"  [ERROR] batch {batch_start}: {e}")
            continue

        pct = min(batch_ids[-1] + 1, id_to + 1) / total * 100
        new_in_batch = [id_ for id_ in batch_ids if id_ in found]
        if new_in_batch:
            for id_ in new_in_batch:
                b = found[id_]
                val_16 = (b[2] & 0xFF) | ((b[3] & 0xFF) << 8)
                val_temp = val_16 / 10.0
                print(f"  FOUND id={id_:5d}  raw={b}  val={val_16}  temp={val_temp:.1f}°C")

        sys.stdout.write(f"\r  Progress: {pct:.1f}%  ({batch_ids[-1]+1}/{total})  Found: {len(found)}")
        sys.stdout.flush()

    print(f"\n\nScan complete. {len(found)} IDs responded.\n")

    print("=" * 60)
    print(f"{'ID':>6}  {'Bytes':20}  {'val16':>6}  {'temp':>8}")
    print("-" * 60)
    for id_, b in sorted(found.items()):
        val_16 = (b[2] & 0xFF) | ((b[3] & 0xFF) << 8)
        val_temp = val_16 / 10.0
        print(f"{id_:6d}  {str(b):20}  {val_16:6d}  {val_temp:7.1f}°C")
    print("=" * 60)

    # Save to file
    out = "scan_results.json"
    with open(out, "w") as f:
        json.dump({str(k): v for k, v in found.items()}, f, indent=2)
    print(f"\nResults saved to {out}")


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    scan(sys.argv[1], sys.argv[2], sys.argv[3])

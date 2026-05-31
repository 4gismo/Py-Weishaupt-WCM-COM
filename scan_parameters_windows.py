# Weishaupt WCM-COM Parameter Scanner
# Fuer Windows - einfach per Doppelklick starten
#
# Voraussetzung: Python installiert (https://www.python.org/downloads/)
# Nach der Python-Installation einmalig im Terminal ausfuehren:
#   pip install requests

import json
import sys
import os
import requests
from requests.auth import HTTPDigestAuth

ENDPOINT = "/parameter.json"
BATCH_SIZE = 15
TIMEOUT = 10


def scan(host, username, password):
    id_from = 0
    id_to = 9999
    total = id_to - id_from + 1
    num_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
    found = {}

    print("=" * 60)
    print("  Weishaupt WCM-COM Parameter Scanner")
    print("=" * 60)
    print(f"  Host     : {host}")
    print(f"  IDs      : {id_from} - {id_to}")
    print(f"  Batches  : {num_batches}  (~{num_batches} Sekunden)")
    print("=" * 60)
    print()

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

            for msg in messages:
                id_ = msg[3]
                if id_ in batch_ids:
                    found[id_] = msg[4:]
                    b = msg[4:]
                    val_16 = (b[2] & 0xFF) | ((b[3] & 0xFF) << 8)
                    val_temp = val_16 / 10.0
                    print(f"  GEFUNDEN  ID={id_:5d}  Rohwert={b}  Wert={val_16}  Temp={val_temp:.1f} Grad C")

        except requests.exceptions.Timeout:
            print(f"  [TIMEOUT] Batch {batch_start}-{batch_ids[-1]} - Weiter...")
            continue
        except requests.exceptions.ConnectionError:
            print(f"\n  [FEHLER] Geraet nicht erreichbar unter http://{host}")
            print("  Bitte IP-Adresse pruefen.")
            break
        except Exception as e:
            print(f"  [FEHLER] Batch {batch_start}: {e}")
            continue

        pct = min(batch_ids[-1] + 1, total) / total * 100
        print(f"  Fortschritt: {pct:.0f}%  (ID bis {batch_ids[-1]})  Gefunden: {len(found)}", end="\r")

    print()
    print()
    print("=" * 60)
    print(f"  Scan abgeschlossen. {len(found)} IDs gefunden.")
    print("=" * 60)
    print(f"  {'ID':>6}  {'Rohbytes':22}  {'Wert':>6}  {'Als Temp':>10}")
    print(f"  {'-'*6}  {'-'*22}  {'-'*6}  {'-'*10}")
    for id_, b in sorted(found.items()):
        val_16 = (b[2] & 0xFF) | ((b[3] & 0xFF) << 8)
        val_temp = val_16 / 10.0
        print(f"  {id_:6d}  {str(b):22}  {val_16:6d}  {val_temp:9.1f} C")
    print("=" * 60)

    # Ergebnis speichern
    out_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "scan_ergebnis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump({str(k): v for k, v in sorted(found.items())}, f, indent=2, ensure_ascii=False)

    print()
    print(f"  Ergebnis gespeichert in: {out_path}")
    print()


def main():
    print()
    print("=" * 60)
    print("  Weishaupt WCM-COM Parameter Scanner")
    print("  Bitte Zugangsdaten eingeben:")
    print("=" * 60)
    print()

    host = input("  IP-Adresse der Heizung (z.B. 192.168.1.100): ").strip()
    username = input("  Benutzername: ").strip()
    password = input("  Passwort: ").strip()

    print()
    print("  Starte Scan... (kann 5-10 Minuten dauern)")
    print()

    scan(host, username, password)

    print()
    input("  Fertig. Druecke Enter zum Beenden.")


if __name__ == "__main__":
    main()

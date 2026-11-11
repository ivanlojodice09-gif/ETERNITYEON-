#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ETERNITYEON — Arduino seriale → OSC → TouchDesigner

Formato seriale atteso, una riga per campione:
    0.1234,0.2345,0.3456,0.4567

Messaggi OSC inviati:
    /sensor/a
    /sensor/b
    /sensor/c
    /sensor/noise

Dipendenze:
    python -m pip install pyserial python-osc
"""

import argparse
import math
import sys

import serial
from pythonosc.udp_client import SimpleUDPClient


OSC_ADDRESSES = (
    "/sensor/a",
    "/sensor/b",
    "/sensor/c",
    "/sensor/noise",
)


def parse_values(line):
    """Restituisce quattro numeri finiti oppure None se la riga non è valida."""
    try:
        values = [float(part.strip()) for part in line.split(",")]
    except ValueError:
        return None

    if len(values) != len(OSC_ADDRESSES):
        return None

    if not all(math.isfinite(value) for value in values):
        return None

    return values


def main():
    parser = argparse.ArgumentParser(
        description="Invia i dati seriali Arduino a TouchDesigner via OSC."
    )
    parser.add_argument(
        "--serial-port",
        required=True,
        help="Porta seriale Arduino, per esempio COM3 o /dev/ttyACM0.",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=9600,
        help="Baud rate seriale (predefinito: 9600).",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Indirizzo del computer che esegue TouchDesigner.",
    )
    parser.add_argument(
        "--osc-port",
        type=int,
        default=10000,
        help="Porta OSC in ascolto in TouchDesigner (predefinito: 10000).",
    )
    args = parser.parse_args()

    try:
        client = SimpleUDPClient(args.host, args.osc_port)
        with serial.Serial(
            args.serial_port,
            args.baud,
            timeout=1,
            write_timeout=1,
        ) as arduino:
            # Molte schede si riavviano quando la porta seriale viene aperta.
            arduino.reset_input_buffer()

            print(
                f"Seriale: {args.serial_port} a {args.baud} baud\n"
                f"OSC: {args.host}:{args.osc_port}\n"
                "Bridge avviato. Premi Ctrl+C per fermarlo."
            )

            while True:
                raw_line = arduino.readline()
                if not raw_line:
                    continue

                line = raw_line.decode("utf-8", errors="replace").strip()
                values = parse_values(line)

                # Ignora righe iniziali o non conformi, come il messaggio
                # "ETERNITYEON Arduino Ready" dello sketch.
                if values is None:
                    continue

                for address, value in zip(OSC_ADDRESSES, values):
                    client.send_message(address, value)

    except KeyboardInterrupt:
        print("\nBridge terminato.")
    except (serial.SerialException, OSError) as error:
        print(f"Errore di connessione: {error}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
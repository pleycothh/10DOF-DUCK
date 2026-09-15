#!/usr/bin/env python3
"""Small interactive PC console for the H723 three-joint PD POC.

Example:
    python pc_pd_poc.py --port COM12
    python pc_pd_poc.py --port /dev/ttyUSB0

The script transmits KEEP at 50 Hz after ARM.  If it is closed, the H723
watchdog disarms the leg within 250 ms.
"""

from __future__ import annotations

import argparse
import queue
import threading
import time

import serial


def reader(port: serial.Serial, lines: queue.Queue[str]) -> None:
    while True:
        try:
            line = port.readline().decode("ascii", errors="replace").strip()
        except serial.SerialException:
            return
        if line:
            lines.put(line)


def console_input(commands: queue.Queue[str]) -> None:
    """Keep stdin blocking in a helper thread so KEEP is never interrupted."""
    while True:
        try:
            command = input("> ").strip()
        except EOFError:
            command = "quit"
        commands.put(command)
        if command.lower() in {"quit", "exit"}:
            return


def main() -> None:
    parser = argparse.ArgumentParser(description="H723 three-joint PD POC console")
    parser.add_argument("--port", required=True)
    parser.add_argument("--baud", type=int, default=115200)
    args = parser.parse_args()

    with serial.Serial(args.port, args.baud, timeout=0.1) as port:
        lines: queue.Queue[str] = queue.Queue()
        threading.Thread(target=reader, args=(port, lines), daemon=True).start()
        commands: queue.Queue[str] = queue.Queue()
        threading.Thread(target=console_input, args=(commands,), daemon=True).start()

        print("Connected. Commands: POWER ON, POWER OFF, ZERO, ARM, DISARM, CLEAR, SET a b c, "
              "GAINS kp kd torque_cap, PULSE joint torque, quit")
        armed = False
        next_keep = time.monotonic()

        try:
            while True:
                while not lines.empty():
                    print(lines.get_nowait())

                now = time.monotonic()
                if armed and now >= next_keep:
                    port.write(b"KEEP\n")
                    next_keep = now + 0.02

                try:
                    command = commands.get(timeout=0.005)
                except queue.Empty:
                    continue

                if command.lower() in {"quit", "exit"}:
                    port.write(b"DISARM\n")
                    break

                if command:
                    port.write((command + "\n").encode("ascii"))

                if command == "ARM":
                    armed = True
                    next_keep = time.monotonic()
                elif command in {"DISARM", "CLEAR", "POWER OFF"}:
                    armed = False
        except KeyboardInterrupt:
            port.write(b"DISARM\n")


if __name__ == "__main__":
    main()

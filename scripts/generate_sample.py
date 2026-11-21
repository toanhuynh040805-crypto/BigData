"""Generate reproducible SYNTHETIC minute-level data for an offline demo.

These are not measurements from UCI. Never report model scores from this
fixture as scientific evidence about real electrical consumption.
"""
from __future__ import annotations

import argparse
import math
from datetime import datetime, timedelta
from pathlib import Path

HEADER = (
    "Date;Time;Global_active_power;Global_reactive_power;Voltage;"
    "Global_intensity;Sub_metering_1;Sub_metering_2;Sub_metering_3\n"
)
DEFAULT_OUTPUT = Path("data/sample/household_power_consumption.txt")


def generate(output: Path, days: int = 70) -> int:
    if days < 1:
        raise ValueError("days must be positive")
    output.parent.mkdir(parents=True, exist_ok=True)
    start = datetime(2008, 1, 1)
    count = 0
    with output.open("w", encoding="utf-8", newline="") as file:
        file.write(HEADER)
        for minute in range(days * 1440):
            instant = start + timedelta(minutes=minute)
            hour = instant.hour + instant.minute / 60
            daily = 0.5 * (1 + math.cos((hour - 20) * math.pi / 12))
            weekly = 0.16 if instant.weekday() >= 5 else 0.0
            power = 0.48 + daily * 1.6 + weekly + 0.07 * math.sin(minute / 131)
            reactive = power * 0.12
            voltage = 231 + 2 * math.sin(minute / 240)
            intensity = power * 1000 / voltage
            sub1 = 0.8 + (3.2 if 11 <= hour < 14 else 0)
            sub2 = 0.6 + (2.5 if 8 <= hour < 10 else 0)
            sub3 = 1.8 + (2.1 if 18 <= hour < 23 else 0)
            file.write(
                f"{instant:%d/%m/%Y};{instant:%H:%M:%S};"
                f"{power:.4f};{reactive:.4f};{voltage:.3f};"
                f"{intensity:.4f};{sub1:.3f};{sub2:.3f};{sub3:.3f}\n"
            )
            count += 1
    return count


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--days", type=int, default=70)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    count = generate(args.output, args.days)
    print(f"Created {count:,} SYNTHETIC measurements: {args.output}")


if __name__ == "__main__":
    main()

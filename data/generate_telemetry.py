import csv
import random
from datetime import datetime, timedelta


OUTPUT_FILE = "data/loom_telemetry.csv"

LOOMS = [
    ("L001", "Air-Jet"),
    ("L002", "Rapier"),
    ("L003", "Projectile"),
    ("L004", "Water-Jet"),
]


def normal_reading(loom_id, loom_type, timestamp):
    return {
        "timestamp": timestamp,
        "loom_id": loom_id,
        "loom_type": loom_type,
        "rpm": random.randint(650, 780),
        "temperature": round(random.uniform(48, 62), 1),
        "vibration": round(random.uniform(0.8, 2.5), 2),
        "motor_current": round(random.uniform(9, 14), 2),
        "warp_tension": round(random.uniform(27, 34), 1),
        "weft_tension": round(random.uniform(22, 29), 1),
        "humidity": round(random.uniform(52, 68), 1),
        "production_rate": round(random.uniform(88, 99), 1),
        "efficiency": round(random.uniform(87, 98), 1),
        "defect_rate": round(random.uniform(0.3, 1.8), 2),
        "machine_status": "NORMAL",
        "fault_type": "",
    }


def bearing_fault(loom_id, loom_type, timestamp):
    row = normal_reading(loom_id, loom_type, timestamp)

    row.update({
        "rpm": random.randint(520, 610),
        "temperature": round(random.uniform(65, 78), 1),
        "vibration": round(random.uniform(4.5, 7.5), 2),
        "motor_current": round(random.uniform(15, 19), 2),
        "efficiency": round(random.uniform(65, 80), 1),
        "defect_rate": round(random.uniform(2.5, 5.0), 2),
        "machine_status": "CRITICAL",
        "fault_type": "BEARING_FAULT",
    })

    return row


def overheating_fault(loom_id, loom_type, timestamp):
    row = normal_reading(loom_id, loom_type, timestamp)

    row.update({
        "temperature": round(random.uniform(72, 90), 1),
        "motor_current": round(random.uniform(15, 20), 2),
        "rpm": random.randint(570, 650),
        "efficiency": round(random.uniform(68, 82), 1),
        "machine_status": "WARNING",
        "fault_type": "OVERHEATING",
    })

    return row


def tension_fault(loom_id, loom_type, timestamp):
    row = normal_reading(loom_id, loom_type, timestamp)

    row.update({
        "warp_tension": round(random.uniform(38, 45), 1),
        "weft_tension": round(random.uniform(32, 38), 1),
        "efficiency": round(random.uniform(70, 84), 1),
        "defect_rate": round(random.uniform(3.0, 6.0), 2),
        "machine_status": "WARNING",
        "fault_type": "YARN_TENSION_FAULT",
    })

    return row


def production_fault(loom_id, loom_type, timestamp):
    row = normal_reading(loom_id, loom_type, timestamp)

    row.update({
        "rpm": random.randint(500, 590),
        "production_rate": round(random.uniform(55, 75), 1),
        "efficiency": round(random.uniform(55, 75), 1),
        "defect_rate": round(random.uniform(2.0, 4.0), 2),
        "machine_status": "WARNING",
        "fault_type": "LOW_PRODUCTION",
    })

    return row


def generate_dataset():
    rows = []

    start_time = datetime.now() - timedelta(hours=2)

    for i in range(10):
        loom_id, loom_type = random.choice(LOOMS)
        timestamp = start_time + timedelta(minutes=i * 5)

        rows.append(
            normal_reading(
                loom_id,
                loom_type,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

    fault_generators = [
        bearing_fault,
        bearing_fault,
        bearing_fault,
        overheating_fault,
        overheating_fault,
        overheating_fault,
        tension_fault,
        tension_fault,
        production_fault,
        production_fault,
    ]

    for i, fault_generator in enumerate(fault_generators, start=10):
        loom_id, loom_type = random.choice(LOOMS)
        timestamp = start_time + timedelta(minutes=i * 5)

        rows.append(
            fault_generator(
                loom_id,
                loom_type,
                timestamp.strftime("%Y-%m-%d %H:%M:%S"),
            )
        )

    with open(OUTPUT_FILE, "w", newline="") as file:
        fieldnames = rows[0].keys()

        writer = csv.DictWriter(file, fieldnames=fieldnames)

        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows)} telemetry records.")
    print(f"Saved to {OUTPUT_FILE}")


if __name__ == "__main__":
    generate_dataset()
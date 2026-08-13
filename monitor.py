import hashlib
import json
import os
import logging
import argparse


MONITORED_DIR = "monitored_files"
BASELINE_FILE = "baseline.json"
LOG_FILE = "integrity.log"


logging.basicConfig(
    filename=LOG_FILE,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

def calculate_hash(file_path):
    with open(file_path, "rb") as file:
        file_data = file.read()

    return hashlib.sha256(file_data).hexdigest()


def scan_directory(directory):
    hashes = {}

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            hashes[file_path] = calculate_hash(file_path)

    return hashes

parser = argparse.ArgumentParser(
    description="SHA-256 File Integrity Monitor"
)

group = parser.add_mutually_exclusive_group()

group.add_argument(
    "--baseline",
    action="store_true",
    help="Create a new baseline of monitored files"
)

group.add_argument(
    "--check",
    action="store_true",
    help="Check monitored files against the baseline"
)

args = parser.parse_args()


current_state = scan_directory(MONITORED_DIR)

if args.baseline:
    with open(BASELINE_FILE, "w") as file:
        json.dump(current_state, file, indent=4)

    message = "[BASELINE CREATED]"
    print(message)
    logging.info(message)

elif args.check:
    if not os.path.exists(BASELINE_FILE):
        print("[ERROR] No baseline found. Run with --baseline first.")
        raise SystemExit(1)

    with open(BASELINE_FILE, "r") as file:
        baseline = json.load(file)

    changes_found = False

    for file_path, current_hash in current_state.items():
        if file_path not in baseline:
            message = f"[NEW] {file_path}"
            print(message)
            logging.warning(message)
            changes_found = True

        elif current_hash != baseline[file_path]:
            message = f"[MODIFIED] {file_path}"
            print(message)
            logging.warning(message)
            changes_found = True

    for file_path in baseline:
        if file_path not in current_state:
            message = f"[DELETED] {file_path}"
            print(message)
            logging.warning(message)
            changes_found = True

    if not changes_found:
        message = "[OK] No file changes detected"
        print(message)
        logging.info(message)

else:
    parser.print_help()

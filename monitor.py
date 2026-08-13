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
    sha256 = hashlib.sha256()

    with open(file_path, "rb") as file:
        while chunk := file.read(65536):
            sha256.update(chunk)

    return sha256.hexdigest()


def scan_directory(directory):
    hashes = {}

    for root, _, files in os.walk(directory):
        for filename in files:
            file_path = os.path.join(root, filename)
            hashes[file_path] = calculate_hash(file_path)

    return hashes

def compare_states(baseline, current_state):
    changes = []

    for file_path, current_hash in current_state.items():
        if file_path not in baseline:
            changes.append(("NEW", file_path))

        elif current_hash != baseline[file_path]:
            changes.append(("MODIFIED", file_path))

    for file_path in baseline:
        if file_path not in current_state:
            changes.append(("DELETED", file_path))

    return changes


if __name__ == "__main__":
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
    
        changes = compare_states(baseline, current_state)

        if changes:
            for change_type, file_path in changes:
                message = f"[{change_type}] {file_path}"
                print(message)
                logging.warning(message)

        else:
            message = "[OK] No file changes detected"
            print(message)
            logging.info(message)

    else:
        parser.print_help()

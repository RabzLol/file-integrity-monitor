import hashlib
import json
import os
import logging


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


current_state = scan_directory(MONITORED_DIR)

if not os.path.exists(BASELINE_FILE):
    with open(BASELINE_FILE, "w") as file:
        json.dump(current_state, file, indent=4)

    message = "[BASELINE CREATED]"
    print(message)
    logging.info(message)

else:
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

import hashlib
import json
import os
import logging
import argparse


MONITORED_DIR = "monitored_files"
BASELINE_FILE = "baseline.json"
LOG_FILE = "integrity.log"


LOG_FILE = "integrity.log"

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
            
            if not os.path.isfile(file_path):
                continue

            try:
                hashes[file_path] = calculate_hash(file_path)

            except (PermissionError, FileNotFoundError, OSError) as error:
                message = f"[ERROR] Could not hash {file_path}: {error}"
                print(message)
                logging.error(message)

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

    parser.add_argument(
        "--directory",
        default=MONITORED_DIR,
        help="Directory to monitor (default: monitored_files)"
    )

    parser.add_argument(
        "--baseline-file",
        default=BASELINE_FILE,
        help="Path to the baseline file (default: baseline.json)"
    )
    parser.add_argument(
        "--log-file",
        default=LOG_FILE,
        help="Path to the log file (default: integrity.log)"
    )
    
    args = parser.parse_args()
    
    logging.basicConfig(
        filename=args.log_file,
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    
    
    if args.baseline:
        current_state = scan_directory(args.directory)
        baseline_data = {
            "directory": os.path.abspath(args.directory),
            "files": current_state
        }

        with open(args.baseline_file, "w") as file:
            json.dump(baseline_data, file, indent=4)

        message = "[BASELINE CREATED]"
        print(message)
        logging.info(message)

    elif args.check:
        if not os.path.exists(args.baseline_file):
            print("[ERROR] No baseline found. Run with --baseline first.")
            raise SystemExit(1)

        with open(args.baseline_file, "r") as file:
            baseline_data = json.load(file)

        baseline_directory = baseline_data["directory"]
        baseline = baseline_data["files"]

        current_directory = os.path.abspath(args.directory)

        if current_directory != baseline_directory:
            print("[ERROR] The selected directory does not match the baseline.")
            raise SystemExit(1)

        current_state = scan_directory(args.directory)

        changes = compare_states(baseline, current_state)

        if changes:
            for change_type, file_path in changes:
                message = f"[{change_type}] {file_path}"
                print(message)
                logging.warning(message)

            raise SystemExit(2)

        else:
             message = "[OK] No file changes detected"
             print(message)
             logging.info(message)

             raise SystemExit(0)

    else:
        parser.print_help()

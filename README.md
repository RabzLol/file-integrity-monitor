# Python File Integrity Monitor

A command-line File Integrity Monitoring (FIM) tool written in Python that uses SHA-256 hashing to detect unauthorized or unexpected changes to files.

This project was built as a cybersecurity learning project to explore file integrity monitoring, hashing, filesystem operations, logging, automated testing, CLI design, and defensive programming.

## Overview

File integrity monitoring is used to detect changes to files by comparing their current state against a known baseline.

This tool creates SHA-256 hashes for files in a selected directory and stores them in a baseline. Future scans compare the current hashes against that baseline.

The monitor can detect:

- New files
- Modified files
- Deleted files

## Features

- SHA-256 file hashing
- Recursive directory scanning
- NEW, MODIFIED, and DELETED file detection
- Chunked file hashing for large files
- Custom directories using `--directory`
- Custom baseline locations using `--baseline-file`
- Baseline directory validation
- Logging of detected changes
- Error handling for inaccessible files
- Special-file filtering
- CLI exit codes for automation
- Automated unit and CLI tests
- Temporary test environments to avoid modifying real monitored files

## Security Concept

The monitor creates a baseline containing SHA-256 hashes representing the expected state of files.

For example:

```text
Original file
     |
     v
SHA-256
     |
     v
Stored baseline hash

Later scan
     |
     v
New SHA-256 hash
     |
     v
Compare with baseline
     |
     +---- Same ------> No change
     |
     +---- Different -> MODIFIED
```

Files appearing after the baseline was created are reported as `NEW`.

Files that existed in the baseline but no longer exist are reported as `DELETED`.

## Installation

Clone the repository:

```bash
git clone <git clone https://github.com/RabzLol/file-integrity-monitor.git>
cd file-integrity-monitor
```

The project uses Python's standard library and does not currently require third-party Python packages.

Check Python:

```bash
python --version
```

## Usage

### Create a baseline

```bash
python monitor.py --baseline
```

### Check file integrity

```bash
python monitor.py --check
```

### Monitor a custom directory

```bash
python monitor.py --baseline --directory ~/Documents
```

Later check the same directory:

```bash
python monitor.py --check --directory ~/Documents
```

### Use a custom baseline file

```bash
python monitor.py \
    --baseline \
    --directory ~/Documents \
    --baseline-file documents-baseline.json
```

Check it with:

```bash
python monitor.py \
    --check \
    --directory ~/Documents \
    --baseline-file documents-baseline.json
```

### View CLI help

```bash
python monitor.py --help
```

## Exit Codes

The monitor provides exit codes so it can be used in scripts and automated security workflows.

| Exit Code | Meaning |
|---|---|
| `0` | Integrity check completed with no detected changes |
| `1` | Configuration or program error |
| `2` | File integrity changes detected |

The exit code can be inspected on Linux with:

```bash
python monitor.py --check
echo $?
```

## Testing

The project includes automated tests using Python's `unittest` framework.

Run the complete test suite:

```bash
python -m unittest discover -s tests -v
```

The test suite covers areas including:

- SHA-256 hashing
- Directory scanning
- New file detection
- Modified file detection
- Deleted file detection
- Multiple simultaneous changes
- Filesystem error handling
- CLI exit codes
- Missing baseline handling
- Incorrect directory handling

Temporary directories are used in CLI tests to keep testing isolated from real monitored files.

## Project Structure

```text
file-integrity-monitor/
├── monitor.py
├── README.md
├── .gitignore
├── monitored_files/
└── tests/
    └── test_monitor.py
```

Runtime files such as `baseline.json` and `integrity.log` are excluded from version control.

## Troubleshooting / Errors I Solved

Building the project involved debugging several real development issues.

### FileNotFoundError

Early testing attempted to hash:

```text
monitored_files/test.txt
```

before the file existed.

This helped reinforce that filesystem operations need to account for missing paths and that test environments must be prepared before files are accessed.

## Docker

The File Integrity Monitor can also run inside Docker.

### Build the image

```bash
docker build -t file-integrity-monitor .
```

### View CLI help

```bash
docker run --rm file-integrity-monitor --help
```

### Container Security

The Docker image uses a dedicated non-root user:

```text
fimuser
UID: 10001
```

The monitored directory can be mounted read-only so the monitoring process does not need permission to modify the files it watches.

### Create a baseline with Docker

```bash
docker run --rm \
  -v "$PWD/docker-test:/data:ro" \
  -v "$PWD/docker-baseline:/baseline" \
  file-integrity-monitor \
  --baseline \
  --directory /data \
  --baseline-file /baseline/baseline.json \
  --log-file /baseline/integrity.log
```

### Check integrity

```bash
docker run --rm \
  -v "$PWD/docker-test:/data:ro" \
  -v "$PWD/docker-baseline:/baseline" \
  file-integrity-monitor \
  --check \
  --directory /data \
  --baseline-file /baseline/baseline.json \
  --log-file /baseline/integrity.log
```

If a monitored file changes, the container reports the event:

```text
[MODIFIED] /data/test.txt
```

The integrity log remains available on the host even after the container is removed.

### Docker Security Design

The container follows several basic security practices:

- Runs as an unprivileged user instead of root
- Uses a read-only mount for monitored data
- Stores baseline data outside the container
- Stores security logs outside the container
- Uses `.dockerignore` to reduce the build context
### NameError

A stray character was accidentally left inside `monitor.py`, resulting in:

```text
NameError: name 's' is not defined
```

The source was inspected and the invalid statement was removed.

### argparse and unittest conflict

Importing `monitor.py` from the test suite initially caused the command-line argument parser to execute.

As a result, arguments belonging to `unittest`, such as:

```text
discover -s tests -v
```

were incorrectly processed by the monitor.

The executable CLI code was moved under:

```python
if __name__ == "__main__":
```

This allowed the program's functions to be imported without executing the CLI.

### Python indentation errors

Several `IndentationError` and `SyntaxError` problems occurred while refactoring the program.

Numbered source output and whitespace inspection were used to locate inconsistent indentation.

For example:

```bash
nl -ba monitor.py
```

Invisible whitespace was also inspected programmatically, which revealed inconsistent indentation levels.

The affected blocks were normalized to consistent four-space Python indentation.

### Validation occurred after scanning

When testing an incorrect directory such as `/tmp`, the program originally scanned the directory before checking whether it matched the directory stored in the baseline.

This resulted in unnecessary errors from sockets, temporary application files, and inaccessible filesystem entries.

The execution order was changed to:

```text
Load baseline
     |
Validate requested directory
     |
Scan directory
     |
Compare hashes
```

Now an incorrect directory is rejected before scanning begins.

### Tests modifying real project data

Early CLI tests used the project's actual `monitored_files` directory and `baseline.json`.

The tests were redesigned to use temporary directories and configurable baseline paths, preventing automated tests from modifying real project data.

## Limitations

This project is intended primarily as a learning and portfolio project.

Current limitations include:

- The baseline is stored locally as JSON.
- A malicious user with sufficient permissions could potentially modify both monitored files and the baseline.
- The tool performs scans when executed rather than continuously monitoring filesystem events.
- Logging is local and does not currently integrate with a SIEM or remote logging system.
- Baseline authenticity is not cryptographically protected.

## Future Improvements

Potential future development includes:

- Docker containerization
- Continuous filesystem monitoring
- Baseline integrity protection
- Configurable logging
- SIEM integration
- JSON security event output
- GitHub Actions testing
- Improved CLI reporting
- Packaging as an installable Python command

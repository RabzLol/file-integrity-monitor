import hashlib
import os
import tempfile
import unittest
import subprocess
import sys

from monitor import calculate_hash, scan_directory, compare_states


class TestFileIntegrityMonitor(unittest.TestCase):

    def test_wrong_directory_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            monitored_dir = os.path.join(temp_dir, "monitored")
            wrong_dir = os.path.join(temp_dir, "wrong")
            os.mkdir(monitored_dir)
            os.mkdir(wrong_dir)

            test_file = os.path.join(monitored_dir, "test.txt")
            baseline_file = os.path.join(temp_dir, "baseline.json")

            with open(test_file, "w") as file:
                file.write("original content")

            subprocess.run(
                [
                    sys.executable,
                    "monitor.py",
                    "--baseline",
                    "--directory",
                    monitored_dir,
                    "--baseline-file",
                    baseline_file
                ],
                capture_output=True,
                text=True
            )

            result = subprocess.run(
                [
                    sys.executable,
                    "monitor.py",
                    "--check",
                    "--directory",
                    wrong_dir,
                    "--baseline-file",
                    baseline_file
                ],
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "does not match the baseline",
                result.stdout
            )


    def test_missing_baseline_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_baseline = os.path.join(temp_dir, "missing.json")

            result = subprocess.run(
                [
                    sys.executable,
                    "monitor.py",
                    "--check",
                    "--directory",
                    temp_dir,
                    "--baseline-file",
                    missing_baseline
                ],
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 1)
            self.assertIn(
                "No baseline found",
                result.stdout
            )


    def test_multiple_changes(self):
        baseline = {
            "config.txt": "old_hash",
            "notes.txt": "notes_hash"
        }

        current_state = {
            "config.txt": "new_hash",
            "new.txt": "new_file_hash"
        }

        changes = compare_states(baseline, current_state)

        self.assertIn(("MODIFIED", "config.txt"), changes)
        self.assertIn(("NEW", "new.txt"), changes)
        self.assertIn(("DELETED", "notes.txt"), changes)
        self.assertEqual(len(changes), 3)

    def test_cli_clean_check_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
           test_file = os.path.join(temp_dir, "test.txt")
           baseline_file = os.path.join(temp_dir, "baseline.json")

           with open(test_file, "w") as file:
               file.write("original content")

           baseline_result = subprocess.run(
               [
                   sys.executable,
                   "monitor.py",
                   "--baseline",
                   "--directory",
                   temp_dir
               ],
               capture_output=True,
               text=True
           )

           self.assertEqual(baseline_result.returncode, 0)

           check_result = subprocess.run(
               [
                   sys.executable,
                   "monitor.py",
                   "--check",
                   "--directory",
                   temp_dir
               ],
               capture_output=True,
               text=True
           )

           self.assertEqual(check_result.returncode, 0)


    def test_cli_detected_change_exit_code(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            test_file = os.path.join(temp_dir, "test.txt")
            baseline_file = os.path.join(temp_dir, "baseline.json")
          
            with open(test_file, "w") as file:
                file.write("original content")


            subprocess.run(
                [
                    sys.executable,
                    "monitor.py",
                    "--baseline",
                    "--directory",
                    temp_dir
                ],
                capture_output=True,
                text=True
            )

            with open(test_file, "w") as file:
                file.write("modified content")

            result = subprocess.run(
                [
                    sys.executable,
                    "monitor.py",
                    "--check",
                    "--directory",
                    temp_dir
                ],
                capture_output=True,
                text=True
            )

            self.assertEqual(result.returncode, 2)        


    def test_scan_directory_handles_hash_error(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            good_file = os.path.join(temp_dir, "good.txt")
            bad_file = os.path.join(temp_dir, "bad.txt")

            with open(good_file, "w") as file:
                file.write("safe file")

            with open(bad_file, "w") as file:
                file.write("unreadable file")

            original_calculate_hash = calculate_hash

            def fake_calculate_hash(file_path):
                if file_path == bad_file:
                    raise PermissionError("Permission denied")

                return original_calculate_hash(file_path)

            import monitor
            monitor.calculate_hash = fake_calculate_hash

            try:
                result = scan_directory(temp_dir)
            finally:
                monitor.calculate_hash = original_calculate_hash

            self.assertIn(good_file, result)
            self.assertNotIn(bad_file, result)

    def test_calculate_hash(self):
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"hello security")
            temp_path = temp_file.name

        expected_hash = hashlib.sha256(b"hello security").hexdigest()
        actual_hash = calculate_hash(temp_path)

        os.remove(temp_path)

        self.assertEqual(actual_hash, expected_hash)

    def test_scan_directory(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            file_path = os.path.join(temp_dir, "test.txt")

            with open(file_path, "w") as file:
                file.write("security test")

            result = scan_directory(temp_dir)

        self.assertEqual(
            result[file_path],
            hashlib.sha256(b"security test").hexdigest()
        )

    def test_detect_new_file(self):
        baseline = {
            "config.txt": "abc123"
        }

        current_state = {
            "config.txt": "abc123",
            "new.txt": "def456"
        }

        changes = compare_states(baseline, current_state)

        self.assertIn(("NEW", "new.txt"), changes)


    def test_detect_modified_file(self):
        baseline = {
            "config.txt": "old_hash"
        }

        current_state = {
            "config.txt": "new_hash"
        }

        changes = compare_states(baseline, current_state)

        self.assertIn(("MODIFIED", "config.txt"), changes)


    def test_detect_deleted_file(self):
        baseline = {
            "config.txt": "abc123",
            "notes.txt": "def456"
        }

        current_state = {
            "config.txt": "abc123"
        }

        changes = compare_states(baseline, current_state)

        self.assertIn(("DELETED", "notes.txt"), changes)
            


if __name__ == "__main__":
    unittest.main()

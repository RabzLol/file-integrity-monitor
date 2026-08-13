import hashlib
import os
import tempfile
import unittest

from monitor import calculate_hash, scan_directory, compare_states


class TestFileIntegrityMonitor(unittest.TestCase):

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

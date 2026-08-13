import hashlib
import os
import tempfile
import unittest

from monitor import calculate_hash, scan_directory, compare_states


class TestFileIntegrityMonitor(unittest.TestCase):

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

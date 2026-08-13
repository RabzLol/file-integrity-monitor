import hashlib
import os
import tempfile
import unittest

from monitor import calculate_hash, scan_directory


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

            self.assertIn(file_path, result)
            self.assertEqual(
                result[file_path],
                hashlib.sha256(b"security test").hexdigest()
            )


if __name__ == "__main__":
    unittest.main()

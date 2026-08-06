import unittest

from pydantic import ValidationError

from app.schemas.check import CreateCheckTaskRequest


class CreateCheckTaskRequestTest(unittest.TestCase):
    def test_rejects_unknown_mode(self):
        with self.assertRaises(ValidationError):
            CreateCheckTaskRequest(
                name="test",
                experimentId=1,
                mode="UNKNOWN",
                reportIds=[1],
            )

    def test_accepts_supported_modes(self):
        for mode in ("IN_CLASS", "HISTORY_ONLY", "BOTH"):
            request = CreateCheckTaskRequest(
                name="test",
                experimentId=1,
                mode=mode,
                reportIds=[1],
            )
            self.assertEqual(request.mode, mode)


if __name__ == "__main__":
    unittest.main()

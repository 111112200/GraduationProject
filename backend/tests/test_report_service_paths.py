import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.models import Report
from app.services.report_service import (
    _resolve_report_file_path,
    _resolve_user_upload_path,
    _safe_upload_filename,
)


class ReportServicePathTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.user_dir = Path(self.temp_dir.name) / "uploads" / "1"
        self.user_dir.mkdir(parents=True)
        self.upload_dir_patch = patch(
            "app.services.report_service._get_user_upload_dir",
            return_value=self.user_dir,
        )
        self.upload_dir_patch.start()

    def tearDown(self):
        self.upload_dir_patch.stop()
        self.temp_dir.cleanup()

    def test_filename_normalization_discards_both_path_separator_styles(self):
        self.assertEqual(
            _safe_upload_filename(r"x\..\..\2\victim.docx"),
            "victim.docx",
        )
        self.assertEqual(
            _safe_upload_filename("../../nested/报告.docx"),
            "报告.docx",
        )

    def test_resolved_upload_path_stays_in_current_user_directory(self):
        path = _resolve_user_upload_path(1, "20260808_000000_报告.docx")

        self.assertEqual(path.parent, self.user_dir.resolve())

    def test_upload_path_rejects_directory_escape(self):
        with self.assertRaises(ValueError):
            _resolve_user_upload_path(1, r"x\..\..\2\victim.docx")

    def test_legacy_report_path_outside_owner_directory_is_rejected(self):
        report = Report(
            user_id=1,
            class_id=1,
            file_path=str(self.user_dir.parent / "2" / "victim.docx"),
        )

        with self.assertRaises(ValueError):
            _resolve_report_file_path(report)


if __name__ == "__main__":
    unittest.main()

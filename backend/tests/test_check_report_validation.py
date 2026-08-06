import unittest
from types import SimpleNamespace

from app.services.check_validation import validate_check_reports


def report(status="PARSED", experiment_id=None, class_id=1):
    return SimpleNamespace(
        status=status,
        experiment_id=experiment_id,
        class_id=class_id,
    )


class CheckReportValidationTest(unittest.TestCase):
    def assert_bad(self, reports, experiment_id=10, mode="BOTH"):
        with self.assertRaises(ValueError):
            validate_check_reports(reports, experiment_id, mode)

    def test_rejects_unparsed_report(self):
        self.assert_bad([report(status="FAILED")])

    def test_rejects_report_from_another_experiment(self):
        self.assert_bad([report(experiment_id=11)])

    def test_rejects_cross_class_internal_check(self):
        self.assert_bad(
            [report(class_id=1), report(class_id=2)],
            mode="IN_CLASS",
        )

    def test_allows_unassigned_reports_for_selected_experiment(self):
        validate_check_reports(
            [report(experiment_id=None), report(experiment_id=10)],
            experiment_id=10,
            mode="BOTH",
        )

    def test_history_mode_can_span_classes(self):
        validate_check_reports(
            [report(class_id=1), report(class_id=2)],
            experiment_id=10,
            mode="HISTORY_ONLY",
        )


if __name__ == "__main__":
    unittest.main()

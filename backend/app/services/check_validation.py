def validate_check_reports(reports: list, experiment_id: int, mode: str):
    """Validate that selected reports are eligible for this check mode."""
    if any(report.status != "PARSED" for report in reports):
        raise ValueError("只能选择解析成功的报告进行查重")

    if any(
        report.experiment_id is not None
        and report.experiment_id != experiment_id
        for report in reports
    ):
        raise ValueError("所选报告包含其他实验的报告")

    if mode in ("IN_CLASS", "BOTH") and len({report.class_id for report in reports}) != 1:
        raise ValueError("班内互查只能选择同一个班级的报告")

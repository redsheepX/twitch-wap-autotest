from pathlib import Path

from twitch_wap.infrastructure.run_artifacts import EvidenceBatch


def test_evidence_batch_groups_device_artifacts_under_one_run_directory(tmp_path: Path) -> None:
    batch = EvidenceBatch(root=tmp_path, run_id="20260818T160000000000Z-test")

    iphone_dir = batch.device_directory("iphone")
    samsung_dir = batch.device_directory("samsung")

    assert iphone_dir == tmp_path / batch.run_id / "iphone"
    assert samsung_dir == tmp_path / batch.run_id / "samsung"
    assert iphone_dir.exists()
    assert samsung_dir.exists()

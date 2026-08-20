from pathlib import Path

import pytest

from twitch_wap.application.journey import SearchJourney
from twitch_wap.infrastructure import (
    MOBILE_DEVICE_PROFILES,
    ChromeDriverFactory,
    RuntimeSettings,
    SeleniumEvidenceWriter,
    TwitchWapUi,
)
from twitch_wap.infrastructure.run_artifacts import EvidenceBatch


def pytest_configure(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers", "e2e: requires Chrome, network access, and the live Twitch WAP site"
    )
    if hasattr(config, "workerinput"):
        run_id = config.workerinput["evidence_run_id"]
        config._evidence_batch = EvidenceBatch(root=Path("artifacts"), run_id=run_id)
    else:
        config._evidence_batch = EvidenceBatch.create(Path("artifacts"))


@pytest.hookimpl(optionalhook=True)
def pytest_configure_node(node) -> None:
    node.workerinput["evidence_run_id"] = node.config._evidence_batch.run_id


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f"rep_{report.when}", report)


@pytest.fixture(scope="session")
def evidence_batch(request: pytest.FixtureRequest) -> EvidenceBatch:
    return request.config._evidence_batch


@pytest.fixture
def settings(request: pytest.FixtureRequest, evidence_batch: EvidenceBatch) -> RuntimeSettings:
    device_identifier = request.getfixturevalue("device_identifier")
    profile = next(
        profile for profile in MOBILE_DEVICE_PROFILES if profile.identifier == device_identifier
    )
    return RuntimeSettings(
        device_profile=profile,
        artifacts_dir=evidence_batch.device_directory(profile.identifier),
        headless=False,
    )


@pytest.fixture
def driver(settings: RuntimeSettings, request: pytest.FixtureRequest):
    web_driver = ChromeDriverFactory(settings).create()
    yield web_driver
    report = getattr(request.node, "rep_call", None)
    if report is not None and report.failed:
        SeleniumEvidenceWriter(web_driver, settings.artifacts_dir).capture_failure(
            request.node.name, str(report.longrepr)
        )
    web_driver.quit()


@pytest.fixture
def journey(driver, settings: RuntimeSettings) -> SearchJourney:
    twitch_ui = TwitchWapUi(driver, settings)
    evidence = SeleniumEvidenceWriter(driver, settings.artifacts_dir)
    return SearchJourney(twitch_ui, twitch_ui, evidence)

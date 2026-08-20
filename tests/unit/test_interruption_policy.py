from twitch_wap.domain import Interruption, InterruptionDecision, InterruptionPolicy


def test_known_cookie_consent_is_dismissible() -> None:
    decision = InterruptionPolicy().decide(Interruption("cookie-consent"))

    assert decision is InterruptionDecision.DISMISS


def test_unknown_blocking_interruption_is_escalated() -> None:
    decision = InterruptionPolicy().decide(Interruption("age-gate"))

    assert decision is InterruptionDecision.ESCALATE


def test_app_redirect_is_dismissible() -> None:
    decision = InterruptionPolicy().decide(Interruption("app-redirect"))

    assert decision is InterruptionDecision.DISMISS

from .models import Interruption, InterruptionDecision


class InterruptionPolicy:
    """Decides whether an interruption may be closed automatically."""

    _DISMISSIBLE = frozenset({"cookie-consent", "generic-modal", "app-redirect"})

    def decide(self, interruption: Interruption) -> InterruptionDecision:
        if interruption.name in self._DISMISSIBLE:
            return InterruptionDecision.DISMISS
        return InterruptionDecision.ESCALATE

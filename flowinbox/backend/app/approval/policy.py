from typing import Dict, Any, Tuple


class ActionRiskLevel:
    READ = "READ"
    LOW_RISK = "LOW_RISK"
    CONSEQUENTIAL = "CONSEQUENTIAL"
    DANGEROUS = "DANGEROUS"


class ActionPolicyEngine:
    """Classifies tool actions and enforces human approval policies."""

    _POLICY_MAP = {
        "search_emails": ActionRiskLevel.READ,
        "get_email": ActionRiskLevel.READ,
        "get_thread": ActionRiskLevel.READ,
        "search_threads": ActionRiskLevel.READ,
        "get_events": ActionRiskLevel.READ,
        "find_available_slots": ActionRiskLevel.READ,
        "get_user_profile": ActionRiskLevel.READ,
        "get_writing_style": ActionRiskLevel.READ,
        "create_draft": ActionRiskLevel.LOW_RISK,
        "update_draft": ActionRiskLevel.LOW_RISK,
        "classify_email": ActionRiskLevel.LOW_RISK,
        "suggest_followup": ActionRiskLevel.LOW_RISK,
        "send_email": ActionRiskLevel.CONSEQUENTIAL,
        "create_event": ActionRiskLevel.CONSEQUENTIAL,
        "update_event": ActionRiskLevel.CONSEQUENTIAL,
        "bulk_send": ActionRiskLevel.CONSEQUENTIAL,
        "permanent_delete": ActionRiskLevel.DANGEROUS,
        "mass_send_all": ActionRiskLevel.DANGEROUS,
    }

    @classmethod
    def evaluate_action(cls, action_name: str, payload: Dict[str, Any]) -> Tuple[str, bool, bool, str]:
        """
        Returns:
        - risk_level: str
        - is_allowed: bool
        - requires_approval: bool
        - reason: str
        """
        risk_level = cls._POLICY_MAP.get(action_name, ActionRiskLevel.CONSEQUENTIAL)

        if risk_level == ActionRiskLevel.DANGEROUS:
            return risk_level, False, False, f"Action '{action_name}' is classified as DANGEROUS and disabled in v1."

        if risk_level == ActionRiskLevel.CONSEQUENTIAL:
            return risk_level, True, True, f"Action '{action_name}' is CONSEQUENTIAL and requires explicit human approval."

        # READ or LOW_RISK
        return risk_level, True, False, f"Action '{action_name}' auto-approved under {risk_level} policy."

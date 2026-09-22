import pytest
from app.approval.policy import ActionPolicyEngine, ActionRiskLevel


def test_action_policy_classification():
    # READ action
    risk, allowed, req_appr, _ = ActionPolicyEngine.evaluate_action("search_emails", {})
    assert risk == ActionRiskLevel.READ
    assert allowed is True
    assert req_appr is False

    # CONSEQUENTIAL action
    risk, allowed, req_appr, _ = ActionPolicyEngine.evaluate_action("send_email", {"draft_id": "123"})
    assert risk == ActionRiskLevel.CONSEQUENTIAL
    assert allowed is True
    assert req_appr is True

    # DANGEROUS action
    risk, allowed, req_appr, _ = ActionPolicyEngine.evaluate_action("permanent_delete", {})
    assert risk == ActionRiskLevel.DANGEROUS
    assert allowed is False

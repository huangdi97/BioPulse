"""Tests: unified exclusion gate module."""

from cloud.app.compliance.exclusion_gate import evaluate, evaluate_rule


class TestExclusionGate:
    def test_exclude_l1_rule_by_exclude_when(self):
        """PHR-L1-003 (利益输送拦截) 在 call_type=学术会议 时应排除。"""
        rule = {
            "code": "PHR-L1-003",
            "name": "利益输送拦截",
            "detection": {
                "exclude_when": {"field": "call_type", "operator": "eq", "value": "学术会议"},
            },
        }
        data = {"call_type": "学术会议", "expenses": 1000}
        excluded, reason = evaluate_rule(rule, data)
        assert excluded is True
        assert "PHR-L1-003" in reason

    def test_not_excluded_when_condition_not_met(self):
        """PHR-L1-003 在 call_type=普通拜访 时不应排除。"""
        rule = {
            "code": "PHR-L1-003",
            "name": "利益输送拦截",
            "detection": {
                "exclude_when": {"field": "call_type", "operator": "eq", "value": "学术会议"},
            },
        }
        data = {"call_type": "普通拜访", "expenses": 1000}
        excluded, reason = evaluate_rule(rule, data)
        assert excluded is False
        assert reason == ""

    def test_exclude_by_sponsorship_approved(self):
        """PHR-L1-006 在 sponsorship_approved=true 时应排除。"""
        rule = {
            "code": "PHR-L1-006",
            "name": "学术会议赞助合规",
            "detection": {
                "exclude_when": {"field": "sponsorship_approved", "operator": "eq", "value": True},
            },
        }
        data = {"sponsorship_approved": True, "sponsorship_amount": 100000}
        excluded, reason = evaluate_rule(rule, data)
        assert excluded is True
        assert "PHR-L1-006" in reason

    def test_evaluate_multiple_rules(self):
        """evaluate() 应返回所有被排除的规则。"""
        context = {
            "data": {
                "call_type": "学术会议",
                "sponsorship_approved": True,
                "non_compete_waived": True,
            }
        }
        excluded, reason = evaluate(context)
        assert len(excluded) >= 2
        assert "PHR-L1-003" in excluded
        assert "PHR-L1-006" in excluded

    def test_no_exclusion_when_data_does_not_match(self):
        """当数据不匹配任何排除条件时，应返回空。"""
        context = {
            "data": {
                "call_type": "普通拜访",
                "sponsorship_approved": False,
            }
        }
        excluded, reason = evaluate(context)
        assert excluded == {}
        assert reason == ""

    def test_exclude_by_non_compete_waived(self):
        """PHR-L1-034 在 non_compete_waived=true 时应排除。"""
        rule = {
            "code": "PHR-L1-034",
            "name": "离职后竞业限制",
            "detection": {
                "exclude_when": {"field": "non_compete_waived", "operator": "eq", "value": True},
            },
        }
        data = {"non_compete_waived": True, "days_since_resignation": 30}
        excluded, reason = evaluate_rule(rule, data)
        assert excluded is True
        assert "PHR-L1-034" in reason

    def test_evaluate_rule_returns_false_for_no_exclude_when(self):
        rule = {"code": "PHR-L1-001", "name": "备案身份核验", "detection": {}}
        data = {"rep_verified": False}
        excluded, reason = evaluate_rule(rule, data)
        assert excluded is False

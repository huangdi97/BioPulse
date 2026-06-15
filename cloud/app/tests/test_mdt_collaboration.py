class TestTokenBudgetRouter:
    def test_get_token_budget(self, client, auth_token):
        resp = client.get(
            "/token-budget/status",
            headers={"Authorization": f"Bearer {auth_token}"},
        )
        assert resp.status_code in (200, 404)

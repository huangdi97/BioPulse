class TestContactRouter:
    def test_get_contact_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/contacts/99999", headers=headers)
        assert resp.status_code == 404

    def test_list_all_contacts(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/contacts", headers=headers)
        assert resp.status_code == 200
        assert isinstance(resp.json()["data"], list)

    def test_list_contacts_opportunity_not_found(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/opportunities/99999/contacts", headers=headers)
        assert resp.status_code == 404

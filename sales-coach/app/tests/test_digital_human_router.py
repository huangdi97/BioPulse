class TestDigitalHumanRouter:
    def test_list_sessions_empty(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.get("/coach/digital-human/sessions", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert "sessions" in data
        assert isinstance(data["sessions"], list)

    def test_voice_input_not_implemented(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/coach/digital-human/sessions/1/voice-input", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "not_implemented"

    def test_video_input_not_implemented(self, client, auth_token):
        headers = {"Authorization": f"Bearer {auth_token}"}
        resp = client.post("/coach/digital-human/sessions/1/video-input", headers=headers)
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["status"] == "not_implemented"

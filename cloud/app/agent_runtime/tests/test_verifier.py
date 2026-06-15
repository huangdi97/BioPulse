from cloud.app.agent_runtime.verifier import Verifier


def test_verify_passes():
    v = Verifier()
    result = v.verify({"success": True, "result": "ok"})
    assert result in (True,)

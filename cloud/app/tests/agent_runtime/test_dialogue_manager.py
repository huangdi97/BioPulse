from unittest.mock import MagicMock, patch

from cloud.app.agent_runtime.comm.dialogue_manager import DialogueTranslator


def test_create_session():
    dt = DialogueTranslator()
    session_id = dt.create_session("agent_1", "user_1")
    assert session_id
    assert len(session_id) == 8


def test_classify_intent_misreport():
    dt = DialogueTranslator()
    assert dt._classify_intent("这是误报") == "misreport"


def test_classify_intent_question():
    dt = DialogueTranslator()
    assert dt._classify_intent("为什么") == "question"


@patch("cloud.app.agent_runtime.comm.dialogue_manager.get_shared_state")
def test_handle_question_no_context(mock_get_ss):
    mock_ss = MagicMock()
    mock_ss.read.return_value = []
    mock_get_ss.return_value = mock_ss

    dt = DialogueTranslator()
    session_id = dt.create_session("agent_1", "user_1")
    session = dt._session_store[session_id]
    session["context"] = {}
    session["agent_key"] = ""

    result = dt._handle_question(session, "为什么")
    assert "没有详细的判断依据" in result

import pytest

from contentauto.llm.claude import ClaudeClient
from contentauto.models.verdicts import LaneDContextVerdict


class _FakeMessages:
    def __init__(self, payload):
        self._payload = payload

    def create(self, **kwargs):
        # mimic anthropic tool-use structured output
        class _Block:
            type = "tool_use"
            input = self._payload

        class _Resp:
            content = [_Block()]

        return _Resp()


class _FakeText:
    def create(self, **kwargs):
        class _Block:
            type = "text"
            text = "generated script body"

        class _Resp:
            content = [_Block()]

        return _Resp()


def test_generate_returns_text():
    client = ClaudeClient(api_key="x", model="m")
    client._client.messages = _FakeText()
    assert client.generate("write a hook") == "generated script body"


def test_judge_returns_validated_model():
    payload = {"checks": [{"type": "consistency", "hard": False,
                           "severity": "low", "action": "pass"}],
               "reputational_risk": 0.1}
    client = ClaudeClient(api_key="x", model="m")
    client._client.messages = _FakeMessages(payload)
    result = client.judge("judge this", LaneDContextVerdict)
    assert isinstance(result, LaneDContextVerdict)
    assert result.reputational_risk == pytest.approx(0.1)

from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from bench.judges.base import Judgment

# ── ClaudeJudge ─────────────────────────────────────────────────────────────


def _claude_response(score: float, reasoning: str = "ok") -> MagicMock:
    msg = MagicMock()
    msg.content = [SimpleNamespace(text=json.dumps({"score": score, "reasoning": reasoning}))]
    return msg


@pytest.fixture()
def claude_judge(monkeypatch):
    mock_anthropic = MagicMock()
    mock_client = MagicMock()
    mock_anthropic.Anthropic.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "anthropic", mock_anthropic)
    from bench.judges.claude import ClaudeJudge

    judge = ClaudeJudge.__new__(ClaudeJudge)
    judge._client = mock_client
    judge._model = "claude-haiku-4-5-20251001"
    return judge, mock_client


def test_claude_score_returns_judgment(claude_judge):
    judge, client = claude_judge
    client.messages.create.return_value = _claude_response(0.85)
    result = judge.score("What is RAG?", "RAG stands for Retrieval-Augmented Generation.")
    assert isinstance(result, Judgment)
    assert result.score == pytest.approx(0.85)
    assert result.reasoning == "ok"


def test_claude_score_batch(claude_judge):
    judge, client = claude_judge
    client.messages.create.side_effect = [_claude_response(0.9), _claude_response(0.1)]
    results = judge.score_batch("query", ["relevant chunk", "irrelevant chunk"])
    assert len(results) == 2
    assert results[0].score > results[1].score


def test_claude_score_batch_empty(claude_judge):
    judge, _ = claude_judge
    assert judge.score_batch("query", []) == []


def test_claude_parse_error_fallback(claude_judge):
    judge, client = claude_judge
    bad = MagicMock()
    bad.content = [SimpleNamespace(text="not json at all")]
    client.messages.create.return_value = bad
    result = judge.score("q", "chunk")
    assert result.score == 0.0
    assert result.reasoning is not None
    assert "parse_error" in result.reasoning


def test_claude_import_error(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "anthropic", None)
    import importlib

    import bench.judges.claude as m

    importlib.reload(m)
    with pytest.raises(ImportError, match="rag4you-cli\\[claude\\]"):
        m.ClaudeJudge()


def test_claude_close(claude_judge):
    judge, client = claude_judge
    judge.close()
    client.close.assert_called_once()


# ── OpenAIJudge ──────────────────────────────────────────────────────────────


def _openai_response(score: float, reasoning: str = "ok") -> MagicMock:
    choice = MagicMock()
    choice.message.content = json.dumps({"score": score, "reasoning": reasoning})
    resp = MagicMock()
    resp.choices = [choice]
    return resp


@pytest.fixture()
def openai_judge(monkeypatch):
    mock_openai = MagicMock()
    mock_client = MagicMock()
    mock_openai.OpenAI.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "openai", mock_openai)
    from bench.judges.openai import OpenAIJudge

    judge = OpenAIJudge.__new__(OpenAIJudge)
    judge._client = mock_client
    judge._model = "gpt-4o-mini"
    return judge, mock_client


def test_openai_score_returns_judgment(openai_judge):
    judge, client = openai_judge
    client.chat.completions.create.return_value = _openai_response(0.75)
    result = judge.score("What is RAG?", "RAG combines retrieval and generation.")
    assert isinstance(result, Judgment)
    assert result.score == pytest.approx(0.75)


def test_openai_score_batch(openai_judge):
    judge, client = openai_judge
    client.chat.completions.create.side_effect = [_openai_response(0.9), _openai_response(0.2)]
    results = judge.score_batch("query", ["relevant", "noise"])
    assert results[0].score > results[1].score


def test_openai_score_batch_empty(openai_judge):
    judge, _ = openai_judge
    assert judge.score_batch("query", []) == []


def test_openai_parse_error_fallback(openai_judge):
    judge, client = openai_judge
    choice = MagicMock()
    choice.message.content = "garbage"
    resp = MagicMock()
    resp.choices = [choice]
    client.chat.completions.create.return_value = resp
    result = judge.score("q", "chunk")
    assert result.score == 0.0
    assert "parse_error" in result.reasoning


def test_openai_import_error(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "openai", None)
    import importlib

    import bench.judges.openai as m

    importlib.reload(m)
    with pytest.raises(ImportError, match="rag4you-cli\\[openai\\]"):
        m.OpenAIJudge()


def test_openai_close(openai_judge):
    judge, client = openai_judge
    judge.close()
    client.close.assert_called_once()


# ── OllamaJudge ──────────────────────────────────────────────────────────────


def _ollama_response(score: float, reasoning: str = "ok") -> MagicMock:
    resp = MagicMock()
    resp.json.return_value = {
        "message": {"content": json.dumps({"score": score, "reasoning": reasoning})}
    }
    return resp


@pytest.fixture()
def ollama_judge(monkeypatch):
    mock_httpx = MagicMock()
    mock_client = MagicMock()
    mock_httpx.Client.return_value = mock_client
    monkeypatch.setitem(__import__("sys").modules, "httpx", mock_httpx)
    from bench.judges.ollama import OllamaJudge

    judge = OllamaJudge.__new__(OllamaJudge)
    judge._client = mock_client
    judge._model = "llama3.2"
    return judge, mock_client


def test_ollama_score_returns_judgment(ollama_judge):
    judge, client = ollama_judge
    client.post.return_value = _ollama_response(0.6)
    result = judge.score("What is RAG?", "RAG is a retrieval method.")
    assert isinstance(result, Judgment)
    assert result.score == pytest.approx(0.6)


def test_ollama_score_batch(ollama_judge):
    judge, client = ollama_judge
    client.post.side_effect = [_ollama_response(0.8), _ollama_response(0.1)]
    results = judge.score_batch("query", ["relevant", "noise"])
    assert results[0].score > results[1].score


def test_ollama_score_batch_empty(ollama_judge):
    judge, _ = ollama_judge
    assert judge.score_batch("query", []) == []


def test_ollama_parse_error_fallback(ollama_judge):
    judge, client = ollama_judge
    resp = MagicMock()
    resp.json.return_value = {"message": {"content": "not json"}}
    client.post.return_value = resp
    result = judge.score("q", "chunk")
    assert result.score == 0.0
    assert "parse_error" in result.reasoning


def test_ollama_import_error(monkeypatch):
    monkeypatch.setitem(__import__("sys").modules, "httpx", None)
    import importlib

    import bench.judges.ollama as m

    importlib.reload(m)
    with pytest.raises(ImportError, match="rag4you-cli\\[ollama\\]"):
        m.OllamaJudge()


def test_ollama_close(ollama_judge):
    judge, client = ollama_judge
    judge.close()
    client.close.assert_called_once()

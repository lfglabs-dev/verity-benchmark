#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from typing import Any
from urllib import error, request

USER_AGENT = "verity-benchmark/0.1"


def require_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return value


def join_messages(messages: list[dict[str, str]]) -> str:
    parts: list[str] = []
    for item in messages:
        role = item["role"].strip().upper()
        content = item["content"].strip()
        if not content:
            continue
        parts.append(f"{role}:\n{content}")
    return "\n\n".join(parts)


def send_completion(agent: dict[str, Any], prompt: str) -> dict[str, Any]:
    base_url = str(agent.get("base_url") or "").rstrip("/")
    payload = {
        "model": agent.get("model"),
        "prompt": prompt,
        "n_predict": agent.get("max_completion_tokens"),
    }
    extra_body = agent.get("extra_body")
    if isinstance(extra_body, dict):
        payload.update(extra_body)
    headers = {
        "Content-Type": "application/json",
        "User-Agent": USER_AGENT,
        **dict(agent.get("headers", {})),
    }
    req = request.Request(
        f"{base_url}/completion",
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    timeout = int(agent.get("request_timeout_seconds") or 120)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"completion request failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"completion request failed: {exc}") from exc
    return require_object(json.loads(body), "completion response")


def list_models(agent: dict[str, Any]) -> dict[str, Any]:
    base_url = str(agent.get("base_url") or "").rstrip("/")
    req = request.Request(
        f"{base_url}/models",
        headers={
            "User-Agent": USER_AGENT,
            **dict(agent.get("headers", {})),
        },
        method="GET",
    )
    timeout = int(agent.get("request_timeout_seconds") or 120)
    try:
        with request.urlopen(req, timeout=timeout) as response:
            body = response.read().decode("utf-8")
    except error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"model probe failed with HTTP {exc.code}: {detail}") from exc
    except error.URLError as exc:
        raise SystemExit(f"model probe failed: {exc}") from exc
    return require_object(json.loads(body), "model probe response")


def extract_model_ids(payload: dict[str, Any]) -> list[str]:
    model_ids: list[str] = []
    data = payload.get("data")
    if isinstance(data, list):
        for item in data:
            if isinstance(item, dict):
                model_id = item.get("id")
                if isinstance(model_id, str):
                    model_ids.append(model_id)
    return model_ids


def extract_text(response: dict[str, Any]) -> str:
    content = response.get("content")
    if isinstance(content, str):
        return content.strip()
    return ""


def extract_reasoning(response: dict[str, Any]) -> str:
    reasoning = response.get("reasoning")
    if isinstance(reasoning, str):
        return reasoning.strip()
    return ""


def extract_candidate_file(response_text: str) -> str:
    text = response_text.strip()
    fenced = re.findall(r"```(?:lean)?\s*\n(.*?)```", text, flags=re.DOTALL)
    if len(fenced) == 1:
        return fenced[0].strip() + "\n"
    return text + ("\n" if text and not text.endswith("\n") else "")


def run_request(payload: dict[str, Any]) -> dict[str, Any]:
    agent = require_object(payload.get("agent"), "agent")
    input_payload = require_object(payload.get("input"), "input")
    messages = input_payload.get("messages")
    if not isinstance(messages, list):
        raise SystemExit("input.messages must be an array")
    typed_messages: list[dict[str, str]] = []
    for item in messages:
        if not isinstance(item, dict):
            raise SystemExit("each input.messages item must be an object")
        role = item.get("role")
        content = item.get("content")
        if not isinstance(role, str) or not isinstance(content, str):
            raise SystemExit("each input.messages item must contain string role/content")
        typed_messages.append({"role": role, "content": content})
    response = send_completion(agent, join_messages(typed_messages))
    response_text = extract_text(response)
    return {
        "protocol_version": 1,
        "response": response,
        "response_text": response_text,
        "response_text_raw": response_text,
        "provider_reasoning_text": extract_reasoning(response),
        "candidate_file_contents": extract_candidate_file(response_text),
    }


def probe_request(payload: dict[str, Any]) -> dict[str, Any]:
    agent = require_object(payload.get("agent"), "agent")
    models_payload = list_models(agent)
    model_ids = extract_model_ids(models_payload)
    configured_model = agent.get("model")
    return {
        "protocol_version": 1,
        "adapter": "command",
        "mode": payload.get("mode"),
        "base_url": agent.get("base_url"),
        "models_path": "/models",
        "configured_model": configured_model,
        "model_count": len(model_ids),
        "models": model_ids,
        "configured_model_available": configured_model in model_ids,
    }


def main() -> int:
    payload = require_object(json.load(sys.stdin), "request")
    if payload.get("protocol_version") != 1:
        raise SystemExit(f"unsupported protocol_version {payload.get('protocol_version')!r}")
    kind = payload.get("kind")
    if kind == "run":
        response = run_request(payload)
    elif kind == "probe":
        response = probe_request(payload)
    else:
        raise SystemExit(f"unsupported request kind {kind!r}")
    print(json.dumps(response))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

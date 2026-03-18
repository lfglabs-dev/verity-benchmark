from __future__ import annotations

from pathlib import Path


def parse_scalar(raw: str) -> object:
    if raw == "null":
        return None
    if raw in {"[]", ""}:
        return []
    if raw.isdigit():
        return int(raw)
    return raw


def load_manifest_data(path: Path) -> dict[str, object]:
    data: dict[str, object] = {}
    lines = path.read_text(encoding="utf-8").splitlines()
    index = 0

    while index < len(lines):
        line = lines[index]
        index += 1

        if not line.strip():
            continue
        if line.startswith((" ", "\t")):
            raise ValueError(f"{path}: unexpected indentation: {line!r}")
        if ":" not in line:
            raise ValueError(f"{path}: expected key/value pair: {line!r}")

        key, raw_value = line.split(":", 1)
        key = key.strip()
        value = raw_value.strip()

        if value == ">":
            block: list[str] = []
            while index < len(lines):
                next_line = lines[index]
                if next_line.startswith("  "):
                    block.append(next_line[2:].rstrip())
                    index += 1
                    continue
                if not next_line.strip():
                    block.append("")
                    index += 1
                    continue
                break
            data[key] = " ".join(part for part in block if part).strip()
            continue

        if value == "":
            items: list[str] = []
            while index < len(lines) and lines[index].startswith("  - "):
                items.append(lines[index][4:].strip())
                index += 1
            data[key] = items if items else None
            continue

        data[key] = parse_scalar(value)

    return data

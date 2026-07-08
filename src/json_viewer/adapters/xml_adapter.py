from __future__ import annotations

import copy
import re
from typing import Any
from xml.etree import ElementTree as ET

import defusedxml.ElementTree as DefusedET

from json_viewer.adapters.types import ParseError, ParseResult

ATTR_PREFIX = "$"
ARRAY_ITEM_TAG = "item"
WRAPPER_TAG = "json-viewer-root"


def _sanitize_tag(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]", "_", str(name))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"_{cleaned}"
    return cleaned or "element"


def _coerce_value(text: str) -> Any:
    stripped = text.strip()
    if stripped.lower() == "true":
        return True
    if stripped.lower() == "false":
        return False
    if stripped.lower() in ("null", "none"):
        return None
    if re.fullmatch(r"-?\d+", stripped):
        return int(stripped)
    if re.fullmatch(r"-?\d+\.\d+", stripped):
        return float(stripped)
    return stripped


def _scalar_to_text(value: Any) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _element_to_value(element: ET.Element) -> Any:
    if element.attrib:
        result: dict[str, Any] = {}
        for attr_name, attr_value in element.attrib.items():
            result[f"{ATTR_PREFIX}{attr_name}"] = _coerce_value(attr_value)
    else:
        result = {}

    children = list(element)
    text = (element.text or "").strip()

    if not children:
        if text:
            coerced = _coerce_value(text)
            if result:
                result["#text"] = coerced
                return result
            return coerced
        return result if result else {}

    if len(children) > 1 and all(child.tag == ARRAY_ITEM_TAG for child in children):
        return [_element_to_value(child) for child in children]

    tag_counts: dict[str, int] = {}
    for child in children:
        tag_counts[child.tag] = tag_counts.get(child.tag, 0) + 1

    for child in children:
        child_value = _element_to_value(child)
        tag = child.tag
        if tag_counts[tag] > 1:
            if tag not in result:
                result[tag] = []
            result[tag].append(child_value)
        else:
            result[tag] = child_value

    if text:
        result["#text"] = _coerce_value(text)

    return result


def parse_xml(text: str) -> ParseResult:
    errors: list[ParseError] = []
    try:
        root = DefusedET.fromstring(text)
        data = {root.tag: _element_to_value(root)}
        return ParseResult(data=data, errors=errors)
    except ET.ParseError as exc:
        line = None
        column = None
        if hasattr(exc, "position") and exc.position is not None:
            line = exc.position[0]
            column = exc.position[1]
        errors.append(ParseError(message=str(exc), line=line, column=column))
        return ParseResult(data={}, errors=errors)
    except Exception as exc:
        errors.append(ParseError(message=str(exc)))
        return ParseResult(data={}, errors=errors)


def _populate_element(tag: str, value: Any) -> ET.Element:
    element = ET.Element(_sanitize_tag(tag))

    if isinstance(value, dict):
        for key, child_value in value.items():
            if key.startswith(ATTR_PREFIX):
                element.set(key[len(ATTR_PREFIX) :], _scalar_to_text(child_value))
            elif key == "#text":
                element.text = _scalar_to_text(child_value)
            elif isinstance(child_value, list):
                for item in child_value:
                    element.append(_populate_element(ARRAY_ITEM_TAG, item))
            else:
                element.append(_populate_element(key, child_value))
    elif isinstance(value, list):
        for item in value:
            element.append(_populate_element(ARRAY_ITEM_TAG, item))
    else:
        element.text = _scalar_to_text(value)

    return element


def _document_root(data: Any) -> ET.Element:
    if isinstance(data, dict):
        if len(data) == 1:
            root_tag, root_value = next(iter(data.items()))
            return _populate_element(str(root_tag), root_value)
        wrapper = ET.Element(_sanitize_tag(WRAPPER_TAG))
        for key, value in data.items():
            if isinstance(value, list):
                for item in value:
                    wrapper.append(_populate_element(str(key), item))
            else:
                wrapper.append(_populate_element(str(key), value))
        return wrapper

    if isinstance(data, list):
        wrapper = ET.Element(_sanitize_tag(WRAPPER_TAG))
        for item in data:
            wrapper.append(_populate_element(ARRAY_ITEM_TAG, item))
        return wrapper

    return _populate_element(WRAPPER_TAG, data)


def format_xml(data: Any) -> str:
    working = copy.deepcopy(data)
    root = _document_root(working)
    ET.indent(root, space="  ")
    xml_body = ET.tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_body}\n'


def unwrap_xml_document(data: Any) -> Any:
    """Normalize parsed XML back to the JSON-like shape users expect."""
    if not isinstance(data, dict) or len(data) != 1:
        return data

    root_tag, root_value = next(iter(data.items()))
    if root_tag == WRAPPER_TAG and isinstance(root_value, dict):
        return root_value
    return data

"""Safe ingestion and test-focused filtering for code knowledge graphs.

The initial supported producer is Understand Anything's
``.ua/knowledge-graph.json``.  Graph summaries are semantic hints only; they
never override the deterministic Project AST or robot capability contract.
"""

from __future__ import annotations

import json
import re
from collections import defaultdict
from typing import Any, Dict, Iterable, List, Optional, Set


MAX_GRAPH_BYTES = 25 * 1024 * 1024
MAX_GRAPH_NODES = 100_000
MAX_GRAPH_EDGES = 300_000
DEFAULT_CONTEXT_NODES = 30
DEFAULT_CONTEXT_CHARS = 16_000

KNOWLEDGE_GRAPH_TYPES = {
    "code knowledge graph",
    "knowledge graph",
    "understand anything",
}

_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]{2,}")
_STOP_WORDS = {
    "and", "are", "for", "from", "into", "that", "the", "then", "this",
    "test", "tests", "using", "with", "should", "when", "where", "given",
}


class KnowledgeGraphError(ValueError):
    """Raised when an uploaded graph is malformed or unsafe to process."""


def is_knowledge_graph_file(name: str = "", file_type: str = "") -> bool:
    normalized_type = (file_type or "").strip().lower()
    normalized_name = (name or "").replace("\\", "/").lower()
    basename = normalized_name.rsplit("/", 1)[-1]
    return (
        normalized_type in KNOWLEDGE_GRAPH_TYPES
        or normalized_name.endswith("/.ua/knowledge-graph.json")
        or normalized_name.endswith("/.understand-anything/knowledge-graph.json")
        or normalized_name in {".ua/knowledge-graph.json", ".understand-anything/knowledge-graph.json"}
        or basename in {"knowledge-graph.json", "understand-anything.json"}
        or basename.endswith(".knowledge-graph.json")
    )


def _decode(raw: Any, filename: str) -> str:
    if isinstance(raw, bytes):
        if len(raw) > MAX_GRAPH_BYTES:
            raise KnowledgeGraphError(
                f"{filename} exceeds the {MAX_GRAPH_BYTES // (1024 * 1024)} MB knowledge graph limit"
            )
        return raw.decode("utf-8-sig", errors="strict")
    text = str(raw or "")
    if len(text.encode("utf-8")) > MAX_GRAPH_BYTES:
        raise KnowledgeGraphError(
            f"{filename} exceeds the {MAX_GRAPH_BYTES // (1024 * 1024)} MB knowledge graph limit"
        )
    return text


def _edge_endpoint(edge: Dict[str, Any], primary: str, fallback: str) -> str:
    value = edge.get(primary, edge.get(fallback, ""))
    if isinstance(value, dict):
        value = value.get("id", "")
    return str(value or "").strip()


def _text(value: Any, limit: int) -> str:
    return str(value or "")[:limit]


def parse_knowledge_graph(raw: Any, filename: str = "knowledge-graph.json") -> Dict[str, Any]:
    """Parse and normalize a generated graph without executing its content."""
    try:
        payload = json.loads(_decode(raw, filename))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise KnowledgeGraphError(f"Invalid JSON in {filename}: {exc}") from exc

    if not isinstance(payload, dict):
        raise KnowledgeGraphError(f"{filename} must contain a JSON object")
    nodes = payload.get("nodes")
    edges = payload.get("edges", [])
    if not isinstance(nodes, list) or not isinstance(edges, list):
        raise KnowledgeGraphError(f"{filename} must contain nodes and edges arrays")
    if len(nodes) > MAX_GRAPH_NODES or len(edges) > MAX_GRAPH_EDGES:
        raise KnowledgeGraphError(
            f"{filename} exceeds graph limits ({MAX_GRAPH_NODES} nodes, {MAX_GRAPH_EDGES} edges)"
        )

    normalized_nodes: List[Dict[str, Any]] = []
    seen: Set[str] = set()
    for index, node in enumerate(nodes):
        if not isinstance(node, dict):
            continue
        node_id = str(node.get("id") or "").strip()
        if not node_id:
            raise KnowledgeGraphError(f"Node {index} in {filename} has no id")
        if node_id in seen:
            raise KnowledgeGraphError(f"Duplicate node id in {filename}: {node_id}")
        seen.add(node_id)
        tags = node.get("tags", [])
        normalized_nodes.append({
            "id": node_id,
            "type": _text(node.get("type") or "unknown", 100),
            "name": _text(node.get("name") or node_id, 500),
            "filePath": _text(node.get("filePath") or node.get("file_path") or "", 1000),
            "lineRange": node.get("lineRange") or node.get("line_range"),
            "summary": _text(node.get("summary"), 4000),
            "tags": [_text(tag, 200) for tag in tags[:30]] if isinstance(tags, list) else [],
            "layer": node.get("layer"),
            "complexity": node.get("complexity"),
        })

    normalized_edges: List[Dict[str, Any]] = []
    for edge in edges:
        if not isinstance(edge, dict):
            continue
        source = _edge_endpoint(edge, "source", "from")
        target = _edge_endpoint(edge, "target", "to")
        # Dangling or malformed edges are safely ignored; graph generators can
        # retain historical references across incremental analyses.
        if not source or not target or source not in seen or target not in seen:
            continue
        normalized_edges.append({
            "source": source,
            "target": target,
            "type": _text(edge.get("type") or edge.get("relationship") or "related", 100),
            "label": _text(edge.get("label"), 500),
        })

    project = payload.get("project", {})
    if not isinstance(project, dict):
        project = {}
    return {
        "schema_version": "stlc-code-knowledge-graph/v1",
        "producer": "understand-anything",
        "source_filename": filename,
        "source_version": str(payload.get("version") or "unknown"),
        "project": {
            "name": _text(project.get("name"), 500),
            "description": _text(project.get("description"), 4000),
            "languages": [_text(item, 200) for item in project.get("languages", [])[:50]] if isinstance(project.get("languages"), list) else [],
            "frameworks": [_text(item, 200) for item in project.get("frameworks", [])[:50]] if isinstance(project.get("frameworks"), list) else [],
            "analyzedAt": _text(project.get("analyzedAt"), 100),
            "gitCommitHash": _text(project.get("gitCommitHash"), 200),
        },
        "nodes": normalized_nodes,
        "edges": normalized_edges,
    }


def _terms(values: Iterable[Any]) -> Set[str]:
    result: Set[str] = set()
    for value in values:
        if isinstance(value, (list, tuple)):
            result.update(_terms(value))
            continue
        if isinstance(value, dict):
            result.update(_terms(value.values()))
            continue
        for token in _TOKEN_RE.findall(str(value or "")):
            lowered = token.lower()
            if lowered not in _STOP_WORDS:
                result.add(lowered)
    return result


def _project_symbols(project_structure: Optional[Dict[str, Any]]) -> Set[str]:
    if not project_structure:
        return set()
    symbols = _terms(project_structure.get("symbol_index", []))
    for file_info in project_structure.get("files", []):
        for function in file_info.get("functions", []):
            if isinstance(function, dict) and function.get("name"):
                symbols.add(str(function["name"]).lower())
        for class_info in file_info.get("classes", []):
            if not isinstance(class_info, dict):
                continue
            if class_info.get("name"):
                symbols.add(str(class_info["name"]).lower())
            for method in class_info.get("methods", []):
                if isinstance(method, dict) and method.get("name"):
                    symbols.add(str(method["name"]).lower())
    return symbols


def select_knowledge_context(
    graph: Optional[Dict[str, Any]],
    test_case: Dict[str, Any],
    project_structure: Optional[Dict[str, Any]] = None,
    max_nodes: int = DEFAULT_CONTEXT_NODES,
) -> Optional[Dict[str, Any]]:
    """Return a compact relevant subgraph for one test case."""
    if not graph or not graph.get("nodes"):
        return None
    max_nodes = max(1, min(int(max_nodes), 100))
    query_terms = _terms(test_case.values())
    authoritative_symbols = _project_symbols(project_structure)

    scored = []
    for node in graph["nodes"]:
        name_terms = _terms([node.get("name"), node.get("id")])
        path_terms = _terms([node.get("filePath")])
        detail_terms = _terms([node.get("summary"), node.get("tags")])
        score = (
            8 * len(query_terms & name_terms)
            + 4 * len(query_terms & path_terms)
            + 2 * len(query_terms & detail_terms)
        )
        if name_terms & authoritative_symbols:
            score += 3
        if node.get("type", "").lower() in {"function", "method", "class", "module", "file"}:
            score += 1
        scored.append((score, node.get("id", ""), node))
    scored.sort(key=lambda item: (-item[0], item[1]))

    # Start with strongly relevant matches. If the test vocabulary is generic,
    # still provide a small deterministic project overview.
    seed_limit = min(12, max_nodes)
    positive = [item for item in scored if item[0] > 1]
    seeds = (positive or scored)[:seed_limit]
    selected_ids = {item[1] for item in seeds}

    adjacency: Dict[str, List[str]] = defaultdict(list)
    for edge in graph.get("edges", []):
        adjacency[edge["source"]].append(edge["target"])
        adjacency[edge["target"]].append(edge["source"])
    score_by_id = {item[1]: item[0] for item in scored}
    neighbors = sorted(
        {neighbor for seed in list(selected_ids) for neighbor in adjacency.get(seed, [])},
        key=lambda node_id: (-score_by_id.get(node_id, 0), node_id),
    )
    for node_id in neighbors:
        if len(selected_ids) >= max_nodes:
            break
        selected_ids.add(node_id)

    nodes_by_id = {node["id"]: node for node in graph["nodes"]}
    selected_nodes = [nodes_by_id[node_id] for node_id in selected_ids if node_id in nodes_by_id]
    selected_nodes.sort(key=lambda node: (-score_by_id.get(node["id"], 0), node["id"]))
    selected_edges = [
        edge for edge in graph.get("edges", [])
        if edge["source"] in selected_ids and edge["target"] in selected_ids
    ]
    return {
        "schema_version": "stlc-test-knowledge-context/v1",
        "project": graph.get("project", {}),
        "query_terms": sorted(query_terms)[:40],
        "nodes": selected_nodes,
        "edges": selected_edges[:100],
        "stats": {
            "total_nodes": len(graph.get("nodes", [])),
            "total_edges": len(graph.get("edges", [])),
            "selected_nodes": len(selected_nodes),
            "selected_edges": min(len(selected_edges), 100),
        },
    }


def knowledge_graph_prompt_context(
    context: Optional[Dict[str, Any]],
    max_chars: int = DEFAULT_CONTEXT_CHARS,
) -> str:
    if not context:
        return "Not provided"
    max_chars = max(1000, int(max_chars))
    compact = json.dumps(context, ensure_ascii=False, separators=(",", ":"))
    if len(compact) <= max_chars:
        return compact

    bounded = dict(context)
    bounded["nodes"] = []
    for node in context.get("nodes", []):
        candidate = dict(bounded)
        candidate["nodes"] = bounded["nodes"] + [node]
        encoded = json.dumps(candidate, ensure_ascii=False, separators=(",", ":"))
        if len(encoded) > max_chars:
            break
        bounded["nodes"].append(node)
    selected = {node["id"] for node in bounded["nodes"]}
    bounded["edges"] = [
        edge for edge in context.get("edges", [])
        if edge["source"] in selected and edge["target"] in selected
    ]
    bounded["truncated"] = True
    return json.dumps(bounded, ensure_ascii=False, separators=(",", ":"))[:max_chars]


def knowledge_graph_summary(graph: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not graph:
        return None
    return {
        "producer": graph.get("producer"),
        "source_filename": graph.get("source_filename"),
        "source_version": graph.get("source_version"),
        "project": graph.get("project", {}),
        "node_count": len(graph.get("nodes", [])),
        "edge_count": len(graph.get("edges", [])),
    }

"""Language adapters. Generation is pure: it never imports or executes input code."""

import ast
import copy
import difflib
import hashlib
import random
from dataclasses import asdict, dataclass
from typing import Dict, Iterable, List, Optional, Tuple


def _sha(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class Candidate:
    ordinal: int
    family: str
    operator: str
    replacement: str
    line: int
    column: int
    end_line: int
    function: Optional[str]


class _Collector(ast.NodeVisitor):
    ARITHMETIC = {ast.Add: ast.Sub, ast.Sub: ast.Add, ast.Mult: ast.Div,
                  ast.Div: ast.Mult, ast.FloorDiv: ast.Mod, ast.Mod: ast.FloorDiv}
    RELATIONAL = {ast.Gt: ast.GtE, ast.GtE: ast.Gt, ast.Lt: ast.LtE,
                  ast.LtE: ast.Lt, ast.Eq: ast.NotEq, ast.NotEq: ast.Eq}
    LOGICAL = {ast.And: ast.Or, ast.Or: ast.And}

    def __init__(self):
        self.raw = []
        self.functions = []
        self.sequence = 0

    @property
    def function(self):
        return ".".join(self.functions) or None

    def visit_FunctionDef(self, node):
        self.functions.append(node.name)
        self.generic_visit(node)
        self.functions.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def _add(self, node, family, operator, replacement):
        self.raw.append((self.sequence, family, operator, replacement, node.lineno,
                         getattr(node, "col_offset", 0), getattr(node, "end_lineno", node.lineno), self.function))
        self.sequence += 1

    def visit_BinOp(self, node):
        replacement = self.ARITHMETIC.get(type(node.op))
        if replacement:
            self._add(node, "AOR", type(node.op).__name__, replacement.__name__)
        self.generic_visit(node)

    def visit_Compare(self, node):
        for op in node.ops:
            replacement = self.RELATIONAL.get(type(op))
            if replacement:
                self._add(node, "ROR", type(op).__name__, replacement.__name__)
        self.generic_visit(node)

    def visit_BoolOp(self, node):
        replacement = self.LOGICAL.get(type(node.op))
        if replacement:
            self._add(node, "LOR", type(node.op).__name__, replacement.__name__)
        self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, bool):
            self._add(node, "CON", str(node.value), str(not node.value))

    def visit_If(self, node):
        self._add(node, "CON", "condition", "not condition")
        self.generic_visit(node)

    def visit_While(self, node):
        self._add(node, "CON", "condition", "not condition")
        self.generic_visit(node)

    def visit_IfExp(self, node):
        self._add(node, "CON", "condition", "not condition")
        self.generic_visit(node)


class _ApplyOne(ast.NodeTransformer):
    def __init__(self, target: Candidate):
        self.target = target
        self.current = -1

    def _hit(self, node, family):
        self.current += 1
        return self.current == self.target.ordinal and family == self.target.family

    def visit_BinOp(self, node):
        if type(node.op) in _Collector.ARITHMETIC and self._hit(node, "AOR"):
            node.op = _Collector.ARITHMETIC[type(node.op)]()
        return self.generic_visit(node)

    def visit_Compare(self, node):
        for index, op in enumerate(node.ops):
            if type(op) in _Collector.RELATIONAL and self._hit(node, "ROR"):
                node.ops[index] = _Collector.RELATIONAL[type(op)]()
        return self.generic_visit(node)

    def visit_BoolOp(self, node):
        if type(node.op) in _Collector.LOGICAL and self._hit(node, "LOR"):
            node.op = _Collector.LOGICAL[type(node.op)]()
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if isinstance(node.value, bool) and self._hit(node, "CON"):
            return ast.copy_location(ast.Constant(not node.value), node)
        return node

    def _conditional(self, node):
        if self._hit(node, "CON"):
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
        return self.generic_visit(node)

    visit_If = _conditional
    visit_While = _conditional
    visit_IfExp = _conditional


class PythonAstMutationAdapter:
    language = "python"

    def metadata(self):
        return {"language": self.language, "available": True, "generation": True,
                "execution": False, "operators": ["AOR", "ROR", "LOR", "CON"],
                "execution_reason": "No verified isolated execution adapter is configured."}

    def generate(self, source: str, source_path="module.py", operator_families=None,
                 max_mutants=None, seed=None, function_scope=None):
        tree = ast.parse(source, filename=source_path)
        collector = _Collector()
        collector.visit(tree)
        raw = sorted(collector.raw, key=lambda item: (item[4], item[5], item[1], item[2], item[3]))
        candidates = [Candidate(item[0], *item[1:]) for item in raw]
        families = set(operator_families or ["AOR", "ROR", "LOR", "CON"])
        candidates = [c for c in candidates if c.family in families and (not function_scope or c.function == function_scope)]
        if max_mutants is not None and len(candidates) > max_mutants:
            if seed is None:
                candidates = candidates[:max_mutants]
            else:
                indexes = sorted(random.Random(seed).sample(range(len(candidates)), max_mutants))
                candidates = [candidates[i] for i in indexes]
        source_hash = _sha(source)
        results, seen_hashes = [], set()
        for candidate in candidates:
            mutated_tree = _ApplyOne(candidate).visit(copy.deepcopy(tree))
            ast.fix_missing_locations(mutated_tree)
            mutated_source = ast.unparse(mutated_tree) + "\n"
            compile(mutated_source, source_path, "exec")  # syntax validation only; never executed
            mutant_hash = _sha(mutated_source)
            if mutant_hash in seen_hashes:
                continue
            seen_hashes.add(mutant_hash)
            identity = f"{source_hash}:{source_path}:{candidate.family}:{candidate.line}:{candidate.column}:{candidate.operator}:{candidate.replacement}"
            results.append({
                "mutant_id": "mut_" + _sha(identity)[:24], "source_hash": source_hash,
                "mutant_hash": mutant_hash, "source_path": source_path, **asdict(candidate),
                "original_ast_expression": f"ast.{candidate.operator}()",
                "replacement_ast_expression": f"ast.{candidate.replacement}()",
                "mutated_source": mutated_source,
                "diff": "".join(difflib.unified_diff(source.splitlines(True), mutated_source.splitlines(True),
                                                       fromfile=source_path, tofile=f"{source_path}::{candidate.family}")),
            })
        return results


class UnsupportedCppRos2Adapter:
    language = "cpp_ros2"

    def metadata(self):
        return {"language": self.language, "available": False, "generation": False,
                "execution": False, "operators": [],
                "reason": "C++/ROS2 adapter contract reserved; implementation is not available."}

    def generate(self, *args, **kwargs):
        raise NotImplementedError(self.metadata()["reason"])


adapter_registry: Dict[str, object] = {
    "python": PythonAstMutationAdapter(),
    "cpp_ros2": UnsupportedCppRos2Adapter(),
}

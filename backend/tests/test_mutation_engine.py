import ast

from mutation.adapters import PythonAstMutationAdapter, adapter_registry


SOURCE = """def decide(a, b, enabled=True):
    total = a + b
    ratio = a * b
    if enabled and total > ratio:
        return total
    return False
"""


def test_generates_all_required_families_with_valid_single_mutants():
    adapter = PythonAstMutationAdapter()
    mutants = adapter.generate(SOURCE, "sample.py")
    assert {item["family"] for item in mutants} == {"AOR", "ROR", "LOR", "CON"}
    assert len({item["mutant_id"] for item in mutants}) == len(mutants)
    assert len({item["mutant_hash"] for item in mutants}) == len(mutants)
    for mutant in mutants:
        ast.parse(mutant["mutated_source"])
        assert mutant["source_hash"]
        assert mutant["line"] >= 1
        assert mutant["function"] == "decide"
        assert mutant["diff"].startswith("--- sample.py")
    assert "+" in SOURCE  # original input remains untouched


def test_generation_is_deterministic_and_seeded_selection_is_repeatable():
    adapter = PythonAstMutationAdapter()
    first = adapter.generate(SOURCE, max_mutants=3, seed=42)
    second = adapter.generate(SOURCE, max_mutants=3, seed=42)
    assert [item["mutant_id"] for item in first] == [item["mutant_id"] for item in second]
    assert [item["mutant_id"] for item in first] != [item["mutant_id"] for item in adapter.generate(SOURCE, max_mutants=3, seed=7)]


def test_filter_and_future_adapter_contract():
    mutants = adapter_registry["python"].generate(SOURCE, operator_families=["ROR"], function_scope="decide")
    assert mutants and {item["family"] for item in mutants} == {"ROR"}
    metadata = adapter_registry["cpp_ros2"].metadata()
    assert metadata["available"] is False
    assert metadata["generation"] is False


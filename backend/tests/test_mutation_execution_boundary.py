import inspect

from mutation.execution import UnavailableExecutionAdapter


def test_unavailable_adapter_records_states_without_running_source():
    adapter = UnavailableExecutionAdapter()
    assert adapter.metadata()["available"] is False
    assert inspect.iscoroutinefunction(adapter.run_baseline)
    assert inspect.iscoroutinefunction(adapter.run_mutants)
    implementation = inspect.getsource(UnavailableExecutionAdapter)
    assert "subprocess" not in implementation
    assert "exec(" not in implementation
    assert "not_executed" in implementation

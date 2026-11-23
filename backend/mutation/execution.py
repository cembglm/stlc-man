"""Execution adapter boundary. The default adapter intentionally executes nothing."""


class UnavailableExecutionAdapter:
    def metadata(self):
        return {"available": False, "mode": "execution_unavailable",
                "reason": "No executor with verified no-network, no-secrets, restricted mounts and resource limits is configured."}

    async def run_baseline(self, *args, **kwargs):
        return {"status": "execution_unavailable", "tests": [], **self.metadata()}

    async def run_mutants(self, mutants, *args, **kwargs):
        return [{"mutant_id": item["mutant_id"], "status": "not_executed", "tests": [],
                 "reason": self.metadata()["reason"]} for item in mutants]


execution_adapter = UnavailableExecutionAdapter()

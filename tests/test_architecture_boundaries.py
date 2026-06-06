from pathlib import Path


def test_core_modules_stay_below_entropy_budget():
    root = Path(__file__).resolve().parents[1]
    budgets = {
        "miniCAH/core/runtime.py": 950,
        "miniCAH/core/runtime_events.py": 90,
        "miniCAH/core/runtime_consumers.py": 90,
        "miniCAH/core/artifacts.py": 130,
        "miniCAH/core/task_state.py": 140,
        "miniCAH/core/todo_ledger.py": 120,
        "miniCAH/core/worker_manager.py": 220,
        "miniCAH/core/context_manager.py": 420,
        "miniCAH/core/context_usage.py": 120,
        "miniCAH/core/compact.py": 180,
        "miniCAH/core/engine.py": 470,
        "miniCAH/core/model_errors.py": 100,
        "miniCAH/core/permissions.py": 140,
        "miniCAH/core/tool_policy.py": 90,
        "miniCAH/core/plan_mode.py": 140,
        "miniCAH/core/tool_executor.py": 181,
        "miniCAH/core/tool_profiles.py": 80,
        "miniCAH/core/turn_history.py": 250,
        "miniCAH/features/skills.py": 220,
        "miniCAH/features/skills_bundled.py": 120,
        "miniCAH/features/skills_runtime.py": 140,
        "miniCAH/tools/registry.py": 360,
        "miniCAH/tools/todos.py": 80,
        "miniCAH/tools/agents.py": 90,
    }

    for relative_path, max_lines in budgets.items():
        line_count = len((root / relative_path).read_text(encoding="utf-8").splitlines())
        assert line_count <= max_lines, f"{relative_path} has {line_count} lines, budget is {max_lines}"

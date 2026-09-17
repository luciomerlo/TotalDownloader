from totaldownloader.concurrency import run_concurrent


def test_empty_tasks_returns_empty():
    assert run_concurrent([]) == []


def test_runs_all_tasks_and_preserves_order():
    tasks = [(lambda n=n: n * 2) for n in range(5)]
    assert run_concurrent(tasks, max_workers=3) == [0, 2, 4, 6, 8]


def test_captures_exceptions_per_task_without_aborting_others():
    def boom():
        raise ValueError("fail")

    tasks = [lambda: 1, boom, lambda: 3]
    results = run_concurrent(tasks, max_workers=3)

    assert results[0] == 1
    assert isinstance(results[1], ValueError)
    assert results[2] == 3

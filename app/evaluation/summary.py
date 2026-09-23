from langsmith.evaluation import (
    EvaluationResult,
    EvaluationResults,
)


def experiment_summary(runs, examples):
    # =========================================
    # 1. 初始化统计数据
    # =========================================
    total = len(runs)

    if total == 0:
        return EvaluationResults(results=[])

    delivery_count = 0
    strict_success_count = 0
    reviewer_pass_count = 0
    model_limit_count = 0

    todo_rates = []
    latencies = []

    knowledge_required = 0
    knowledge_success = 0

    # =========================================
    # 2. 遍历 Experiment
    # =========================================
    for run, example in zip(runs, examples):
        outputs = run.outputs or {}
        reference = example.outputs or {}

        report = outputs.get(
            "report",
            "",
        ).strip()

        status = outputs.get("status")
        review_status = outputs.get(
            "review_status"
        )

        # =========================================
        # 3. Delivery Success
        # =========================================
        if (
            report
            and status in {
                "completed",
                "completed_with_warnings",
            }
        ):
            delivery_count += 1

        # =========================================
        # 4. Strict Task Success
        # =========================================
        if (
            report
            and status == "completed"
            and review_status == "passed"
        ):
            strict_success_count += 1

        # =========================================
        # 5. Reviewer Pass
        # =========================================
        if review_status == "passed":
            reviewer_pass_count += 1

        # =========================================
        # 6. Todo Completion
        # =========================================
        todos = outputs.get(
            "todos",
            [],
        )

        if todos:
            completed = sum(
                todo.get("status") == "completed"
                for todo in todos
            )

            todo_rates.append(
                completed / len(todos)
            )

        # =========================================
        # 7. Model Limit Failure
        # =========================================
        errors = outputs.get(
            "errors",
            [],
        )

        if any(
            "ModelCallLimitExceededError" in error
            for error in errors
        ):
            model_limit_count += 1

        # =========================================
        # 8. Latency
        # =========================================
        latency = outputs.get(
            "latency_seconds"
        )

        if latency is not None:
            latencies.append(
                float(latency)
            )

        # =========================================
        # 9. Required Knowledge Usage
        # =========================================
        if reference.get(
            "requires_knowledge",
            False,
        ):
            knowledge_required += 1

            available = set(
                outputs.get(
                    "knowledge_ids",
                    [],
                )
            )

            cited = set(
                outputs.get(
                    "cited_knowledge_ids",
                    [],
                )
            )

            if (
                cited
                and cited.issubset(available)
            ):
                knowledge_success += 1

    # =========================================
    # 10. 计算 Dataset 级指标
    # =========================================
    avg_todo = (
        sum(todo_rates) / len(todo_rates)
        if todo_rates
        else 0.0
    )

    avg_latency = (
        sum(latencies) / len(latencies)
        if latencies
        else 0.0
    )

    knowledge_rate = (
        knowledge_success / knowledge_required
        if knowledge_required
        else 1.0
    )

    # =========================================
    # 11. 返回 Summary Metrics
    # =========================================
    return EvaluationResults(
        results=[
            EvaluationResult(
                key="summary_delivery_rate",
                score=delivery_count / total,
            ),
            EvaluationResult(
                key="summary_task_success_rate",
                score=strict_success_count / total,
            ),
            EvaluationResult(
                key="summary_reviewer_pass_rate",
                score=reviewer_pass_count / total,
            ),
            EvaluationResult(
                key="summary_todo_completion_rate",
                score=avg_todo,
            ),
            EvaluationResult(
                key="summary_required_knowledge_usage",
                score=knowledge_rate,
            ),
            EvaluationResult(
                key="summary_model_limit_failure_rate",
                score=model_limit_count / total,
            ),
            EvaluationResult(
                key="summary_avg_latency_seconds",
                value=round(avg_latency, 2),
            ),
        ]
    )
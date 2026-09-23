def delivery_success(outputs: dict) -> bool:
    # =========================================
    # 1. 判断是否成功产出可交付报告
    # =========================================
    report = outputs.get("report", "").strip()

    return (
        bool(report)
        and outputs["status"] in {
            "completed",
            "completed_with_warnings",
        }
    )

def strict_task_success(outputs: dict) -> bool:
    # =========================================
    # 1. 获取最终报告
    # =========================================
    report = outputs.get("report", "").strip()

    # =========================================
    # 2. 判断严格任务成功
    # =========================================
    return (
        bool(report)
        and outputs.get("status") == "completed"
        and outputs.get("review_status") == "passed"
    )


def task_success(outputs: dict) -> bool:
    # =========================================
    # 1. 判断任务是否真正通过质量验收
    # =========================================
    report = outputs.get("report", "").strip()

    return (
        bool(report)
        and outputs["status"] == "completed"
        and outputs["review_status"] == "passed"
    )


def reviewer_passed(
    outputs: dict,
) -> bool:
    # =========================================
    # 1. 判断 Reviewer 是否最终通过
    # =========================================
    return outputs["review_status"] == "passed"


def todo_completion_rate(
    outputs: dict,
) -> float:
    # =========================================
    # 1. 获取 Todos
    # =========================================
    todos = outputs.get("todos", [])

    if not todos:
        return 0.0

    # =========================================
    # 2. 计算完成比例
    # =========================================
    completed = sum(
        todo["status"] == "completed"
        for todo in todos
    )

    return completed / len(todos)


def agent_routing_recall(
    outputs: dict,
    reference_outputs: dict,
) -> float:
    # =========================================
    # 1. 获取期望和实际 Agent
    # =========================================
    expected = set(
        reference_outputs.get(
            "expected_agents",
            [],
        )
    )

    actual = set(
        outputs.get(
            "agents_used",
            [],
        )
    )

    # =========================================
    # 2. 无期望 Agent 时直接通过
    # =========================================
    if not expected:
        return 1.0

    # =========================================
    # 3. 计算 Agent Routing Recall
    # =========================================
    return len(
        expected & actual
    ) / len(expected)


def citation_validity(
    outputs: dict,
    reference_outputs: dict,
) -> float:
    # =========================================
    # 1. 不要求来源则直接通过
    # =========================================
    if not reference_outputs.get(
        "requires_sources",
        False,
    ):
        return 1.0

    # =========================================
    # 2. 获取真实与引用 Source IDs
    # =========================================
    available = set(
        outputs.get("source_ids", [])
    )

    cited = set(
        outputs.get("cited_source_ids", [])
    )

    if not cited:
        return 0.0

    # =========================================
    # 3. 计算有效引用比例
    # =========================================
    valid = cited & available

    return len(valid) / len(cited)


def knowledge_evidence_usage(
    outputs: dict,
    reference_outputs: dict,
) -> float:
    # =========================================
    # 1. 不需要内部知识则不参与扣分
    # =========================================
    if not reference_outputs.get(
        "requires_knowledge",
        False,
    ):
        return 1.0

    # =========================================
    # 2. 获取 Knowledge Evidence
    # =========================================
    available = set(
        outputs.get("knowledge_ids", [])
    )

    cited = set(
        outputs.get(
            "cited_knowledge_ids",
            [],
        )
    )

    if not cited:
        return 0.0

    # =========================================
    # 3. 验证 Evidence ID
    # =========================================
    valid = cited & available

    return len(valid) / len(cited)

def agent_routing_precision(
    outputs: dict,
    reference_outputs: dict,
) -> float:
    # =========================================
    # 1. 获取期望和实际 Agent
    # =========================================
    expected = set(
        reference_outputs.get(
            "expected_agents",
            [],
        )
    )

    actual = set(
        outputs.get(
            "agents_used",
            [],
        )
    )

    # =========================================
    # 2. 无实际路由
    # =========================================
    if not actual:
        return 0.0

    # =========================================
    # 3. 计算 Routing Precision
    # =========================================
    return len(
        expected & actual
    ) / len(actual)

def agent_routing_f1(
    outputs: dict,
    reference_outputs: dict,
) -> float:
    # =========================================
    # 1. 计算 Recall 和 Precision
    # =========================================
    recall = agent_routing_recall(
        outputs,
        reference_outputs,
    )

    precision = agent_routing_precision(
        outputs,
        reference_outputs,
    )

    # =========================================
    # 2. 计算 Routing F1
    # =========================================
    if precision + recall == 0:
        return 0.0

    return (
        2 * precision * recall
        / (precision + recall)
    )
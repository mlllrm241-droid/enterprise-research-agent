from langchain.agents.middleware import (
    ClearToolUsesEdit,
    ContextEditingMiddleware,
    ModelCallLimitMiddleware,
    ModelRetryMiddleware,
    SummarizationMiddleware,
    ToolCallLimitMiddleware,
    ToolRetryMiddleware,
)

from app.schemas.subagent_route import AgentType

####        V1
# HARNESS_LIMITS = {
#     "company": {"tool_calls": 8, "model_calls": 10},
#     "market": {"tool_calls": 8, "model_calls": 10},
#     "finance": {"tool_calls": 6, "model_calls": 8},
#     "risk": {"tool_calls": 10, "model_calls": 12},
#     "general": {"tool_calls": 8, "model_calls": 10},
# }

####        V2
HARNESS_LIMITS = {
    "company": {"tool_calls": 8, "model_calls": 16},
    "market": {"tool_calls": 8, "model_calls": 16},
    "finance": {"tool_calls": 6, "model_calls": 14},
    "risk": {"tool_calls": 10, "model_calls": 20},
    "general": {"tool_calls": 8, "model_calls": 16},
}


def build_research_harness(agent_type: AgentType, model):
    # =========================================
    # 1. 获取当前 Agent 的调用预算
    # =========================================
    limits = HARNESS_LIMITS[agent_type]

    # =========================================
    # 2. 配置 Model Retry
    # =========================================
    model_retry = ModelRetryMiddleware(
        # 首次调用失败后最多再重试 2 次，因此最多会发起 3 次模型请求。
        max_retries=2,
        # 第一次重试前的基础等待时间（秒）。
        initial_delay=1.0,
        # 指数退避倍数：后续等待时间按 initial_delay * 2^n 增长。
        backoff_factor=2.0,
        # 单次重试的最长等待时间（秒），防止退避时间无限增长。
        max_delay=8.0,
        # 重试耗尽后重新抛出原异常，立即终止当前 Agent 执行。
        on_failure="error",
    )

    # =========================================
    # 3. 配置 Tool Retry
    # =========================================
    tool_retry = ToolRetryMiddleware(
        # 首次调用失败后最多再重试 2 次，即单次工具调用最多尝试 3 次。
        max_retries=2,
        # 第一次重试前的基础等待时间（秒）。
        initial_delay=1.0,
        # 指数退避倍数：后续等待时间按 initial_delay * 2^n 增长。
        backoff_factor=2.0,
        # 单次重试的最长等待时间（秒）。
        max_delay=8.0,
        # 重试耗尽后将错误封装成 ToolMessage 返回，让模型决定降级、改用其他工具或继续作答。
        on_failure="continue",
    )

    # =========================================
    # 4. 限制 Tool 调用次数
    # =========================================
    tool_limit = ToolCallLimitMiddleware(
        # 当前单次 Agent 运行允许的工具调用总数；不同 Agent 类型使用各自的预算。
        run_limit=limits["tool_calls"],
        # 超出预算时阻止多余的工具调用并返回错误消息，但不强制结束 Agent；
        # 模型仍可利用已经获得的上下文生成结论或自行结束。
        exit_behavior="continue",
    )

    # =========================================
    # 5. 限制 Model 调用次数
    # =========================================
    model_limit = ModelCallLimitMiddleware(
        # 当前单次 Agent 运行允许的模型调用总数，用于控制 token 成本并防止无限循环。
        run_limit=limits["model_calls"],
        # 超出预算时直接跳到 Agent 运行末尾，并注入一条说明超限原因的 AIMessage。
        exit_behavior="error",
    )

    # =========================================
    # 6. 清理过老的大型 Tool Result
    # =========================================
    context_editing = ContextEditingMiddleware(
        # 按顺序执行的上下文编辑策略；此处只配置“清理旧工具结果”策略。
        edits=[
            ClearToolUsesEdit(
                # 当消息上下文超过约 12,000 tokens 时触发清理。
                # ContextEditingMiddleware 默认使用近似 token 计数，因此不是精确的计费 token 数。
                trigger=12000,
                # 一次清理至少尝试回收 4,000 tokens；达到目标后停止继续清理旧结果。
                clear_at_least=4000,
                # 始终保留最近 3 条 ToolMessage 的完整内容，只从更旧的工具结果开始清理。
                keep=3,
            )
        ]
    )

    # =========================================
    # 7. 长上下文自动总结
    # =========================================
    summarization = SummarizationMiddleware(
        # 复用当前 Agent 的聊天模型生成历史摘要；该过程会额外发起一次模型调用。
        model=model,
        # 当会话历史达到约 18,000 tokens 时触发总结，避免超出模型上下文窗口。
        trigger=("tokens", 18000),
        # 总结时保留最近约 6,000 tokens 的原始消息，更旧部分被压缩成一条摘要消息。
        keep=("tokens", 6000),
    )

    # =========================================
    # 8. 返回完整 Harness
    # =========================================
    return [
        model_retry,
        tool_retry,
        tool_limit,
        model_limit,
        context_editing,
        summarization,
    ]

from dotenv import load_dotenv
from langsmith import Client
from langsmith.evaluation import evaluate_existing

from app.evaluation.evaluators import (
    agent_routing_f1,
    agent_routing_precision,
    delivery_success,
    strict_task_success,
)
from app.evaluation.llm_judge import report_quality_judge
from app.evaluation.summary import experiment_summary


EXPERIMENT_NAME = "enterprise-research-stage12-831f14ca"


def main():
    # =========================================
    # 1. 加载环境变量
    # =========================================
    load_dotenv()
    client = Client()

    # =========================================
    # 2. 对已有 Experiment 补充 Evaluation
    # =========================================
    results = evaluate_existing(
        EXPERIMENT_NAME,
        evaluators=[
            delivery_success,
            strict_task_success,
            agent_routing_precision,
            agent_routing_f1,
            report_quality_judge,
        ],
        summary_evaluators=[
            experiment_summary,
        ],
        max_concurrency=1,
        client=client,
    )

    # =========================================
    # 3. 输出结果
    # =========================================
    print(results)


if __name__ == "__main__":
    main()
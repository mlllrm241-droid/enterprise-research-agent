from dotenv import load_dotenv
from langsmith import Client

from app.evaluation.evaluators import (
    agent_routing_recall,
    citation_validity,
    knowledge_evidence_usage,
    reviewer_passed,
    task_success,
    todo_completion_rate,
)
from app.evaluation.target import run_research_target


DATASET_NAME = "enterprise-research-agent-stage12-v1"


def main():
    # =========================================
    # 1. 加载环境变量
    # =========================================
    load_dotenv()

    # =========================================
    # 2. 创建 LangSmith Client
    # =========================================
    client = Client()

    # =========================================
    # 3. 运行 Evaluation Experiment
    # =========================================
    results = client.evaluate(
        run_research_target,
        data=DATASET_NAME,
        evaluators=[
            task_success,
            reviewer_passed,
            todo_completion_rate,
            agent_routing_recall,
            citation_validity,
            knowledge_evidence_usage,
        ],
        experiment_prefix="enterprise-research-stage12",
        max_concurrency=1,
    )

    # =========================================
    # 4. 输出结果
    # =========================================
    print(results)


if __name__ == "__main__":
    main()
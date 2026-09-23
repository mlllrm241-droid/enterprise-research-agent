from dotenv import load_dotenv
from langsmith import Client


DATASET_NAME = "enterprise-research-agent-stage12-v1"


def main():
    # =========================================
    # 1. 加载环境变量
    # =========================================
    load_dotenv()

    client = Client()

    # =========================================
    # 2. 避免重复创建 Dataset
    # =========================================
    if client.has_dataset(dataset_name=DATASET_NAME):
        print(f"Dataset 已存在：{DATASET_NAME}")
        return

    # =========================================
    # 3. 创建 Dataset
    # =========================================
    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description="Enterprise Research Agent Stage 12 evaluation dataset.",
    )

    # =========================================
    # 4. 定义测试样本
    # =========================================
    examples = [
        {
            "inputs": {
                "query": (
                    "请梳理 NVIDIA 当前主要企业 AI 产品，"
                    "包括 GPU、DGX、NVIDIA AI Enterprise 和 NIM，"
                    "重要事实保留 Source ID。"
                )
            },
            "outputs": {
                "expected_agents": ["company"],
                "requires_sources": True,
                "requires_knowledge": False,
            },
        },
        {
            "inputs": {
                "query": (
                    "请比较 NVIDIA、AMD、Google 和 AWS "
                    "在企业 AI 基础设施市场中的主要竞争方向，"
                    "重要结论保留 Source ID。"
                )
            },
            "outputs": {
                "expected_agents": ["market"],
                "requires_sources": True,
                "requires_knowledge": False,
            },
        },
        {
            "inputs": {
                "query": (
                    "请分析 NVIDIA 最近财年的营收、净利润和"
                    "数据中心收入，并计算关键同比增长率，"
                    "重要数据保留 Source ID。"
                )
            },
            "outputs": {
                "expected_agents": ["finance"],
                "requires_sources": True,
                "requires_knowledge": False,
            },
        },
        {
            "inputs": {
                "query": (
                    "请根据企业内部 AI Supplier Assessment Standard，"
                    "评估 NVIDIA 的供应链风险和技术依赖风险，"
                    "外部事实保留 Source ID，内部标准保留 "
                    "Knowledge Evidence ID。"
                )
            },
            "outputs": {
                "expected_agents": ["risk"],
                "requires_sources": True,
                "requires_knowledge": True,
            },
        },
    ]

    # =========================================
    # 5. 上传测试样本
    # =========================================
    client.create_examples(
        dataset_id=dataset.id,
        examples=examples,
    )

    print(f"Dataset 创建完成：{DATASET_NAME}")
    print(f"Examples：{len(examples)}")


if __name__ == "__main__":
    main()
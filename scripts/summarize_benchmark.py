import argparse
import csv

from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean


AVERAGE_METRICS = [
    "delivery_success",
    "strict_task_success",
    "todo_completion_rate",
    "reviewer_passed",
    "citation_validity",
    "knowledge_evidence_usage",
    "routing_precision",
    "routing_recall",
    "routing_f1",
    "llm_judge_quality",
]


def parse_number(value):
    if value is None:
        return None

    text = str(value).strip()

    if not text:
        return None

    try:
        return float(text)
    except ValueError:
        return None


def parse_bool(value) -> bool:
    return str(value).strip().lower() in {
        "true",
        "1",
        "yes",
    }


def average_metric(
    rows: list[dict],
    field_name: str,
):
    values = [
        value
        for row in rows
        if (
            value := parse_number(
                row.get(field_name)
            )
        )
        is not None
    ]

    if not values:
        return ""

    return round(
        mean(values),
        4,
    )


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "inputs",
        nargs="+",
    )

    parser.add_argument(
        "--output",
        default=None,
    )

    args = parser.parse_args()

    # =========================================
    # 1. 读取所有 CSV
    # =========================================
    rows = []

    for input_path in args.inputs:
        with Path(input_path).open(
            "r",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            rows.extend(
                csv.DictReader(file)
            )

    # =========================================
    # 2. 按 System 分组
    # =========================================
    grouped = defaultdict(list)

    for row in rows:
        grouped[row["system"]].append(
            row
        )

    # =========================================
    # 3. 生成汇总结果
    # =========================================
    summaries = []

    for system, system_rows in grouped.items():
        summary = {
            "system": system,
            "case_count": len(system_rows),
        }

        for metric in AVERAGE_METRICS:
            summary[metric] = (
                average_metric(
                    system_rows,
                    metric,
                )
            )

        
        summary["timeout_rate"] = round(
            sum(
                parse_bool(
                    row.get("benchmark_timeout")
                )
                for row in system_rows
            )
            / len(system_rows),
            4,
        )
        

        # =========================================
        # 4. Model Limit Failure Rate
        # =========================================
        limit_values = [
            value
            for row in system_rows
            if (
                value := parse_number(
                    row.get(
                        "model_limit_failures"
                    )
                )
            )
            is not None
        ]

        if limit_values:
            summary[
                "model_limit_failure_rate"
            ] = round(
                sum(
                    value > 0
                    for value in limit_values
                )
                / len(limit_values),
                4,
            )
        else:
            summary[
                "model_limit_failure_rate"
            ] = ""

        # =========================================
        # 5. 平均耗时
        # =========================================
        summary[
            "avg_latency_seconds"
        ] = average_metric(
            system_rows,
            "latency_seconds",
        )

        # =========================================
        # 6. 总错误数
        # =========================================
        summary["total_errors"] = int(
            sum(
                parse_number(
                    row.get("total_errors")
                )
                or 0
                for row in system_rows
            )
        )

        summaries.append(summary)

    # =========================================
    # 7. 输出路径
    # =========================================
    if args.output:
        output_path = Path(
            args.output
        )
    else:
        timestamp = datetime.now().strftime(
            "%Y%m%d_%H%M%S"
        )

        output_path = (
            Path("results/benchmarks")
            / f"stage15_summary_{timestamp}.csv"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    # =========================================
    # 8. 保存汇总 CSV
    # =========================================
    if summaries:
        with output_path.open(
            "w",
            encoding="utf-8-sig",
            newline="",
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=summaries[0].keys(),
            )

            writer.writeheader()
            writer.writerows(summaries)

    # =========================================
    # 9. 控制台输出
    # =========================================
    for summary in summaries:
        print(
            f"{summary['system']}: "
            f"cases={summary['case_count']}, "
            "delivery="
            f"{summary['delivery_success']}, "
            "strict="
            f"{summary['strict_task_success']}, "
            "latency="
            f"{summary['avg_latency_seconds']}s"
        )

    print(
        "\n汇总完成："
        f"{output_path.resolve()}"
    )


if __name__ == "__main__":
    main()
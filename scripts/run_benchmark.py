import argparse
import csv
import time

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv


load_dotenv()


from app.benchmark.executor import (
    BENCHMARK_TIMEOUT_SECONDS,
    run_system_with_timeout,
)
from app.benchmark.runner import (
    build_benchmark_result,
    load_benchmark_cases,
)
from app.benchmark.schemas import (
    BenchmarkResult,
)


SYSTEMS = [
    "baseline",
    "full_no_harness",
    "full_harness",
]


CSV_FIELDS = [
    field_name
    for field_name
    in BenchmarkResult.model_fields
    if field_name != "report"
]


def build_failed_raw(
    system: str,
    error: Exception,
    latency_seconds: float,
) -> dict:
    use_harness = {
        "baseline": None,
        "full_no_harness": False,
        "full_harness": True,
    }[system]

    return {
        "status": "failed",
        "review_status": None,
        "report": "",
        "todos": [],
        "agents_used": [],
        "errors": [
            f"{type(error).__name__}: {error}"
        ],
        "warnings": [],
        "source_ids": [],
        "knowledge_ids": [],
        "cited_source_ids": [],
        "cited_knowledge_ids": [],
        "latency_seconds": round(
            latency_seconds,
            2,
        ),
        "use_harness": use_harness,
    }


def main():
    # =========================================
    # 1. 解析命令行参数
    # =========================================
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--system",
        choices=SYSTEMS + ["all"],
        default="all",
    )

    parser.add_argument(
        "--dataset",
        default="benchmarks/stage15_v1.json",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
    )

    parser.add_argument(
        "--with-judge",
        action="store_true",
    )

    parser.add_argument(
        "--output",
        default=None,
    )
    parser.add_argument(
        "--timeout-seconds",
        type=int,
        default=BENCHMARK_TIMEOUT_SECONDS,
    )

    args = parser.parse_args()

    # =========================================
    # 2. 读取 Benchmark Cases
    # =========================================
    cases = load_benchmark_cases(
        args.dataset
    )

    if args.limit is not None:
        cases = cases[:args.limit]

    systems = (
        SYSTEMS
        if args.system == "all"
        else [args.system]
    )

    # =========================================
    # 3. 准备输出文件
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
            / f"stage15_{timestamp}.csv"
        )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    total_runs = (
        len(cases)
        * len(systems)
    )

    run_number = 0

    # =========================================
    # 4. 打开 CSV
    # =========================================
    with output_path.open(
        "w",
        encoding="utf-8-sig",
        newline="",
    ) as file:
        writer = csv.DictWriter(
            file,
            fieldnames=CSV_FIELDS,
        )

        writer.writeheader()
        file.flush()

        # =========================================
        # 5. 依次执行每套系统
        # =========================================
        for system in systems:
            for case in cases:
                run_number += 1

                print(
                    f"\n[{run_number}/{total_runs}] "
                    f"{system} / {case.case_id}"
                )

                started_at = (
                    time.perf_counter()
                )

                try:
                    raw = run_system_with_timeout(
                        system=system,
                        case=case,
                        timeout_seconds=args.timeout_seconds,
                    )

                except Exception as exc:
                    latency = (
                        time.perf_counter()
                        - started_at
                    )

                    raw = build_failed_raw(
                        system=system,
                        error=exc,
                        latency_seconds=latency,
                    )

                result = build_benchmark_result(
                    system=system,
                    case=case,
                    raw=raw,
                    with_judge=args.with_judge,
                )

                row = result.model_dump(
                    exclude={"report"}
                )

                writer.writerow(row)

                # 每个 Case 立即写入磁盘
                file.flush()

                print(
                    "status="
                    f"{result.status}, "
                    "delivery="
                    f"{result.delivery_success}, "
                    "latency="
                    f"{result.latency_seconds}s"
                )

    print(
        "\nBenchmark 完成："
        f"{output_path.resolve()}"
    )


if __name__ == "__main__":
    main()
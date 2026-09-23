import multiprocessing as mp
from queue import Empty

from app.benchmark.runner import run_system
from app.benchmark.schemas import BenchmarkCase


BENCHMARK_TIMEOUT_SECONDS = 900


def _benchmark_worker(
    system: str,
    case_data: dict,
    result_queue,
):
    try:
        # =========================================
        # 1. 恢复 Benchmark Case
        # =========================================
        case = BenchmarkCase.model_validate(
            case_data
        )

        # =========================================
        # 2. 执行被测系统
        # =========================================
        result = run_system(
            system,
            case,
        )

        # =========================================
        # 3. 返回正常结果
        # =========================================
        result_queue.put({
            "type": "success",
            "result": result,
        })

    except Exception as e:
        # =========================================
        # 4. 返回异常结果
        # =========================================
        result_queue.put({
            "type": "error",
            "error": (
                f"{type(e).__name__}: {e}"
            ),
        })


def run_system_with_timeout(
    system: str,
    case: BenchmarkCase,
    timeout_seconds: int = BENCHMARK_TIMEOUT_SECONDS,
) -> dict:
    # =========================================
    # 1. 使用 Windows Spawn Context
    # =========================================
    context = mp.get_context("spawn")

    result_queue = context.Queue()

    # =========================================
    # 2. 创建独立 Benchmark Process
    # =========================================
    process = context.Process(
        target=_benchmark_worker,
        args=(
            system,
            case.model_dump(),
            result_queue,
        ),
    )

    process.start()

    # =========================================
    # 3. 等待 Case 完成
    # =========================================
    process.join(
        timeout_seconds
    )

    # =========================================
    # 4. 超时则强制结束
    # =========================================
    if process.is_alive():
        process.terminate()
        process.join()

        return {
            "status": "timeout",
            "review_status": None,
            "report": "",
            "todos": [],
            "agents_used": [],
            "errors": [
                (
                    "BenchmarkTimeoutError: "
                    f"超过 {timeout_seconds} 秒"
                )
            ],
            "source_ids": [],
            "knowledge_ids": [],
            "cited_source_ids": [],
            "cited_knowledge_ids": [],
            "latency_seconds": float(
                timeout_seconds
            ),
            "benchmark_timeout": True,
        }

    # =========================================
    # 5. 获取 Worker Result
    # =========================================
    try:
        message = result_queue.get_nowait()

    except Empty:
        return {
            "status": "failed",
            "review_status": None,
            "report": "",
            "todos": [],
            "agents_used": [],
            "errors": [
                "BenchmarkWorkerError: 子进程未返回结果"
            ],
            "source_ids": [],
            "knowledge_ids": [],
            "cited_source_ids": [],
            "cited_knowledge_ids": [],
            "latency_seconds": 0.0,
            "benchmark_timeout": False,
        }

    # =========================================
    # 6. Worker 执行异常
    # =========================================
    if message["type"] == "error":
        return {
            "status": "failed",
            "review_status": None,
            "report": "",
            "todos": [],
            "agents_used": [],
            "errors": [
                message["error"]
            ],
            "source_ids": [],
            "knowledge_ids": [],
            "cited_source_ids": [],
            "cited_knowledge_ids": [],
            "latency_seconds": 0.0,
            "benchmark_timeout": False,
        }

    # =========================================
    # 7. 返回正常结果
    # =========================================
    result = message["result"]
    result["benchmark_timeout"] = False

    return result
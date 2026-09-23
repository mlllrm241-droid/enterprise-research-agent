import json
import re
from typing import TypeVar

from pydantic import BaseModel


T = TypeVar("T", bound=BaseModel)


def parse_structured_output(content, schema: type[T]) -> T:
    # =========================================
    # 1. 统一转换成文本
    # =========================================
    if isinstance(content, str):
        text = content.strip()
    else:
        text = str(content).strip()

    # =========================================
    # 2. 清理 Markdown JSON 代码块
    # =========================================
    text = re.sub(r"^```(?:json)?\s*", "", text, flags=re.I)
    text = re.sub(r"\s*```$", "", text)

    # =========================================
    # 3. 解析 JSON
    # =========================================
    data = json.loads(text)

    # =========================================
    # 4. 兼容模型错误返回单元素数组
    # =========================================
    if isinstance(data, list):
        if len(data) != 1:
            raise ValueError(
                f"期望单个 JSON 对象，实际返回 {len(data)} 个对象"
            )

        data = data[0]

    # =========================================
    # 5. Pydantic 最终校验
    # =========================================
    return schema.model_validate(data)
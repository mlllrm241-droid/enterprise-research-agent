from datetime import datetime

from langchain.tools import tool


@tool
def get_current_date() -> str:
    """
    获取当前日期。

    当任务涉及“最近”“过去一年”“今年”
    等时间敏感信息时，可以调用此工具确认当前日期。
    """

    return datetime.now().strftime("%Y-%m-%d")
import ast
import operator

from langchain.tools import tool


OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _calculate(node):
    if isinstance(node, ast.Expression):
        return _calculate(node.body)

    if isinstance(node, ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("只允许数字")

    if isinstance(node, ast.BinOp):
        left = _calculate(node.left)
        right = _calculate(node.right)

        op = OPERATORS.get(type(node.op))

        if op is None:
            raise ValueError("不支持该运算")

        return op(left, right)

    if isinstance(node, ast.UnaryOp):
        value = _calculate(node.operand)

        op = OPERATORS.get(type(node.op))

        if op is None:
            raise ValueError("不支持该运算")

        return op(value)

    raise ValueError("表达式中包含非法内容")


@tool
def calculator(expression: str) -> str:
    """
    计算数学表达式。

    当需要进行收入增长率、利润率、百分比、
    加减乘除等精确计算时使用该工具。

    参数:
        expression: 数学表达式，例如 "(135 - 100) / 100 * 100"

    返回:
        计算结果
    """

    try:
        tree = ast.parse(expression, mode="eval")
        result = _calculate(tree)

        return str(result)

    except Exception as e:
        return f"计算失败: {e}"
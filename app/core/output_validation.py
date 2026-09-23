def is_model_rejection(text: str) -> bool:
    # =========================================
    # 1. 标准化模型输出
    # =========================================
    content = text.strip().lower()

    # =========================================
    # 2. 定义常见拒绝响应
    # =========================================
    rejection_markers = [
        "the request was rejected",
        "considered high risk",
        "request has been rejected",
    ]

    # =========================================
    # 3. 判断是否为拒绝响应
    # =========================================
    return any(marker in content for marker in rejection_markers)
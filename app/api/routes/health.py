from fastapi import APIRouter


router = APIRouter(
    tags=["Health"]
)


@router.get("/health")
async def health():
    # =========================================
    # 1. 返回服务状态
    # =========================================
    return {
        "status": "ok",
        "service": (
            "enterprise-research-agent"
        ),
    }
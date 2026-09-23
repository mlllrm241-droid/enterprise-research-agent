const API_BASE = "/api/v1/research"


export async function createResearchTask(query) {
  // =========================================
  // 1. 创建研究任务
  // =========================================
  const response = await fetch(`${API_BASE}/tasks`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      query,
      user_id: "local_user",
    }),
  })

  // =========================================
  // 2. 检查请求结果
  // =========================================
  if (!response.ok) {
    throw new Error("创建研究任务失败")
  }

  // =========================================
  // 3. 返回任务信息
  // =========================================
  return response.json()
}


export async function getResearchTask(taskId) {
  // =========================================
  // 1. 查询任务状态
  // =========================================
  const response = await fetch(
    `${API_BASE}/tasks/${taskId}`
  )

  // =========================================
  // 2. 检查请求结果
  // =========================================
  if (!response.ok) {
    throw new Error("获取任务状态失败")
  }

  // =========================================
  // 3. 返回任务状态
  // =========================================
  return response.json()
}


export async function submitHumanReview(
  taskId,
  action,
  feedback = ""
) {
  // =========================================
  // 1. 提交 Human Review
  // =========================================
  const response = await fetch(
    `${API_BASE}/tasks/${taskId}/review`,
    {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        action,
        feedback,
      }),
    }
  )

  // =========================================
  // 2. 读取响应
  // =========================================
  const data = await response.json()

  if (!response.ok) {
    throw new Error(
      data.detail || "人工审核失败"
    )
  }

  // =========================================
  // 3. 返回 Resume 结果
  // =========================================
  return data
}


export async function getResearchReport(taskId) {
  // =========================================
  // 1. 请求最终报告
  // =========================================
  const response = await fetch(
    `${API_BASE}/tasks/${taskId}/report`
  )

  // =========================================
  // 2. 检查报告状态
  // =========================================
  if (!response.ok) {
    throw new Error("当前尚未生成最终报告")
  }

  // =========================================
  // 3. 返回 Markdown 文本
  // =========================================
  return response.text()
}


export function createResearchEventSource(taskId) {
  // =========================================
  // 1. 创建 SSE 连接
  // =========================================
  return new EventSource(
    `${API_BASE}/tasks/${taskId}/events`
  )
}
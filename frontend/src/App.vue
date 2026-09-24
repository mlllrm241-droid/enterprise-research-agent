<script setup>
import {
  computed,
  onMounted,
  onUnmounted,
  ref,
} from "vue"

import {
  createResearchEventSource,
  createResearchTask,
  getResearchReport,
  getResearchTask,
  submitHumanReview,
} from "./api/research"

import heroImage from "./assets/hero.png"


const TASK_ID_STORAGE_KEY = (
  "enterprise-research-agent.task-id"
)
const QUERY_STORAGE_KEY = (
  "enterprise-research-agent.query"
)

const query = ref(
  localStorage.getItem(QUERY_STORAGE_KEY) || ""
)
const taskId = ref(
  localStorage.getItem(TASK_ID_STORAGE_KEY) || ""
)
const task = ref(null)
const report = ref("")
const feedback = ref("")

const loading = ref(false)
const errorMessage = ref("")
const connected = ref(false)

let eventSource = null


const isWaitingHuman = computed(() => {
  return task.value?.status === "waiting_human"
})


const isFinished = computed(() => {
  return [
    "completed",
    "completed_with_warnings",
    "failed",
    "rejected",
  ].includes(task.value?.status)
})


const completedTodos = computed(() => {
  if (!task.value?.todos) {
    return 0
  }

  return task.value.todos.filter(
    (todo) => todo.status === "completed"
  ).length
})


const progressPercent = computed(() => {
  const todos = task.value?.todos || []

  if (!todos.length) {
    return 0
  }

  return Math.round(
    (completedTodos.value / todos.length) * 100
  )
})


async function startResearch() {
  // =========================================
  // 1. 校验研究任务
  // =========================================
  if (!query.value.trim()) {
    errorMessage.value = "请输入研究任务"
    return
  }

  // =========================================
  // 2. 重置页面状态
  // =========================================
  loading.value = true
  errorMessage.value = ""
  report.value = ""
  feedback.value = ""

  closeEventSource()

  try {
    // =========================================
    // 3. 创建研究任务
    // =========================================
    const result = await createResearchTask(
      query.value.trim()
    )

    taskId.value = result.task_id

    localStorage.setItem(
      TASK_ID_STORAGE_KEY,
      taskId.value
    )
    localStorage.setItem(
      QUERY_STORAGE_KEY,
      query.value.trim()
    )

    // =========================================
    // 4. 获取初始状态
    // =========================================
    await refreshTask()

    // =========================================
    // 5. 建立 SSE 连接
    // =========================================
    connectEvents()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}


async function refreshTask() {
  // =========================================
  // 1. 检查 Task ID
  // =========================================
  if (!taskId.value) {
    return
  }

  // =========================================
  // 2. 获取最新 Graph State
  // =========================================
  task.value = await getResearchTask(
    taskId.value
  )
}


function connectEvents() {
  // =========================================
  // 1. 关闭旧连接
  // =========================================
  closeEventSource()

  if (!taskId.value) {
    return
  }

  // =========================================
  // 2. 创建 SSE
  // =========================================
  eventSource = createResearchEventSource(
    taskId.value
  )

  connected.value = true

  // =========================================
  // 3. 监听 Progress Event
  // =========================================
  eventSource.addEventListener(
    "progress",
    async (event) => {
      try {
        const data = JSON.parse(event.data)

        task.value = {
          ...(task.value || {}),
          ...data,
        }

        // =========================================
        // 4. Terminal 后读取最终报告
        // =========================================
        if (
          [
            "completed",
            "completed_with_warnings",
          ].includes(data.status)
        ) {
          await loadReport()
          closeEventSource()
        }

        // =========================================
        // 5. Human Review 后停止当前连接
        // =========================================
        if (data.status === "waiting_human") {
          await refreshTask()
          closeEventSource()
        }
      } catch (error) {
        errorMessage.value = (
          "解析 SSE 数据失败"
        )
      }
    }
  )

  // =========================================
  // 6. 监听运行异常
  // =========================================
  eventSource.addEventListener(
    "error",
    () => {
      connected.value = false
    }
  )
}


function closeEventSource() {
  // =========================================
  // 1. 关闭 SSE
  // =========================================
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  connected.value = false
}


async function handleReview(action) {
  // =========================================
  // 1. 校验 Revise Feedback
  // =========================================
  if (
    action === "revise"
    && !feedback.value.trim()
  ) {
    errorMessage.value = (
      "revise 时请输入修改意见"
    )
    return
  }

  // =========================================
  // 2. 提交人工审核
  // =========================================
  loading.value = true
  errorMessage.value = ""

  try {
    await submitHumanReview(
      taskId.value,
      action,
      feedback.value.trim()
    )

    // =========================================
    // 3. 重新获取任务状态
    // =========================================
    await new Promise(
      (resolve) => setTimeout(resolve, 300)
    )

    await refreshTask()

    // =========================================
    // 4. Resume 后重新监听 SSE
    // =========================================
    connectEvents()
  } catch (error) {
    errorMessage.value = error.message
  } finally {
    loading.value = false
  }
}


async function loadReport() {
  // =========================================
  // 1. 获取最终报告
  // =========================================
  if (!taskId.value) {
    return
  }

  try {
    report.value = await getResearchReport(
      taskId.value
    )
  } catch {
    report.value = ""
  }
}


onMounted(async () => {
  if (!taskId.value) {
    return
  }

  loading.value = true

  try {
    await refreshTask()

    if (
      [
        "completed",
        "completed_with_warnings",
      ].includes(task.value?.status)
    ) {
      await loadReport()
    } else if (
      !isFinished.value
      && !isWaitingHuman.value
    ) {
      connectEvents()
    }
  } catch (error) {
    errorMessage.value = (
      `恢复上次任务失败：${error.message}`
    )
  } finally {
    loading.value = false
  }
})


onUnmounted(() => {
  closeEventSource()
})
</script>


<template>
  <main class="app-shell">
    <header class="header">
      <div>
        <div class="brand">
          Enterprise Research
          <span>Agent</span>
          <i>✦</i>
        </div>
        <p class="subtitle">
          AI-powered enterprise research workspace
        </p>
      </div>

      <img
        class="header-mascot"
        :src="heroImage"
        alt="AI research assistant"
      />

      <div
        class="connection"
        :class="{ online: connected }"
      >
        <span class="dot"></span>
        {{ connected ? "Agent Running" : "Idle" }}
      </div>
    </header>

    <section class="hero card">
      <div class="label label-with-icon">
        <span class="label-icon">▣</span>
        Research Task
      </div>

      <div class="query-wrap">
        <textarea
          v-model="query"
          class="query-input"
          maxlength="1000"
          placeholder="例如：请分析 NVIDIA 与 AMD 在企业 AI 推理市场中的竞争格局，并保留重要事实的 Source ID。"
          :disabled="loading"
        />
        <span class="character-count">
          {{ query.length }}/1000
        </span>
      </div>

      <div class="actions">
        <button
          class="primary-button"
          :disabled="loading"
          @click="startResearch"
        >
          <span class="play-icon">▶</span>
          {{ loading ? "Processing..." : "Start Research" }}
        </button>

        <span v-if="taskId" class="task-id">
          Task {{ taskId }}
        </span>
      </div>

      <div v-if="errorMessage" class="error-box">
        {{ errorMessage }}
      </div>
    </section>

    <section v-if="task" class="dashboard">
      <div class="main-column">
        <section class="card status-card">
          <div class="section-header">
            <div class="section-title">
              <span class="section-icon status-icon">⌁</span>
              <div>
                <div class="label">Current Status</div>
                <h2>{{ task.current_step || task.status }}</h2>
              </div>
            </div>

            <span class="status-badge" :class="task.status">
              <span class="badge-spinner"></span>
              {{ task.status }}
            </span>
          </div>

          <div class="progress-line">
            <div class="progress-track">
              <div
                class="progress-value"
                :style="{ width: `${progressPercent}%` }"
              />
            </div>
            <strong>{{ progressPercent }}%</strong>
          </div>

          <div class="metrics">
            <div class="metric-card">
              <span class="metric-icon blue">▥</span>
              <div>
                <span>Progress</span>
                <strong>{{ progressPercent }}%</strong>
              </div>
            </div>

            <div class="metric-card">
              <span class="metric-icon teal">●</span>
              <div>
                <span>Current Agent</span>
                <strong>{{ task.current_agent || "-" }}</strong>
              </div>
            </div>

            <div class="metric-card">
              <span class="metric-icon purple">♟</span>
              <div>
                <span>Reviewer</span>
                <strong>{{ task.review_status || "-" }}</strong>
              </div>
            </div>
          </div>
        </section>

        <section class="card plan-card">
          <div class="section-header">
            <div class="section-title">
              <span class="section-icon plan-icon">✓</span>
              <div>
                <div class="label">Research Plan</div>
                <h2>Todos</h2>
              </div>
            </div>
            <span class="todo-count">
              {{ completedTodos }} / {{ task.todos?.length || 0 }}
            </span>
          </div>

          <div class="todo-list">
            <div
              v-for="(todo, index) in task.todos"
              :key="todo.id"
              class="todo-item"
              :class="todo.status"
            >
              <span class="timeline-dot"></span>
              <div class="todo-symbol">
                {{
                  todo.status === "completed"
                    ? "✓"
                    : index + 1
                }}
              </div>

              <div class="todo-content">
                <strong>{{ todo.id }} · {{ todo.title }}</strong>
                <span>
                  {{
                    todo.assigned_agent
                      ? `Agent: ${todo.assigned_agent}`
                      : "Waiting for routing"
                  }}
                </span>
              </div>

              <span class="todo-action">
                {{ todo.status === "running" ? "◎" : "◇" }}
              </span>
            </div>
          </div>
        </section>

        <section v-if="report" class="card report-card">
          <div class="section-title">
            <span class="section-icon report-icon">▤</span>
            <div>
              <div class="label">Final Artifact</div>
              <h2>Research Report</h2>
            </div>
          </div>
          <pre class="report">{{ report }}</pre>
        </section>
      </div>

      <aside class="side-column">
        <section class="card details-card">
          <div class="section-title compact">
            <span class="section-icon runtime-icon">⚙</span>
            <div class="label">Runtime</div>
          </div>

          <div class="detail-row">
            <span><i>◇</i>Status</span>
            <strong class="detail-status">
              <b></b>{{ task.status }}
            </strong>
          </div>
          <div class="detail-row">
            <span><i>▱</i>Step</span>
            <strong>{{ task.current_step || "-" }}</strong>
          </div>
          <div class="detail-row">
            <span><i>▤</i>Todo</span>
            <strong>{{ task.current_todo_id || "-" }}</strong>
          </div>
          <div class="detail-row">
            <span><i>♟</i>Human Review</span>
            <strong>{{ task.human_review_status || "-" }}</strong>
          </div>

          <button
            v-if="isFinished && !report"
            class="secondary-button"
            @click="loadReport"
          >
            Load Report
          </button>
        </section>

        <section v-if="isWaitingHuman" class="card review-card">
          <div class="label">Human In The Loop</div>
          <h2>Review Required</h2>
          <p>自动审查已完成，请决定是否接受当前报告。</p>

          <textarea
            v-model="feedback"
            class="feedback-input"
            placeholder="需要修改时，在这里填写反馈..."
          />

          <button
            class="approve-button"
            :disabled="loading"
            @click="handleReview('approve')"
          >Approve</button>
          <button
            class="revise-button"
            :disabled="loading"
            @click="handleReview('revise')"
          >Revise</button>
          <button
            class="reject-button"
            :disabled="loading"
            @click="handleReview('reject')"
          >Reject</button>
        </section>

        <div class="mascot-stage" aria-hidden="true">
          <span class="sparkle one">✦</span>
          <span class="sparkle two">✧</span>
          <img :src="heroImage" alt="" />
        </div>

        <section v-if="task.errors?.length" class="card error-card">
          <div class="label">Errors</div>
          <div
            v-for="item in task.errors"
            :key="item"
            class="runtime-message"
          >{{ item }}</div>
        </section>

        <section v-if="task.warnings?.length" class="card warning-card">
          <div class="label">Warnings</div>
          <div
            v-for="item in task.warnings"
            :key="item"
            class="runtime-message"
          >{{ item }}</div>
        </section>
      </aside>
    </section>
  </main>
</template>

<template>
  <div class="page">
    <div class="top-bar">
      <router-link to="/checks" class="back-link">← 返回任务列表</router-link>
      <h2 class="g-page-title">{{ task?.name || '查重结果' }}</h2>
      <span :class="['g-badge', badgeClass(task?.status)]">
        {{ statusIcon(task?.status) }} {{ statusLabel(task?.status) }}
      </span>
      <button
        v-if="task?.status === 'COMPLETED' && task?.results?.length"
        @click="exportExcel"
        :disabled="exporting"
        class="g-btn g-btn-primary export-btn"
      >
        {{ exporting ? '⏳ 导出中...' : '📥 导出 Excel' }}
      </button>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="task?.status === 'RUNNING' || task?.status === 'PENDING'" class="g-card g-card-body pending-card">
      <div class="pending-icon">⏳</div>
      <div class="pending-text">查重任务正在执行中，请稍后刷新页面查看结果</div>
      <button @click="load" class="g-btn g-btn-primary" style="margin-top: 12px;">🔄 刷新</button>
    </div>

    <div v-else class="g-card">
      <table class="g-table" v-if="task?.results?.length">
        <thead>
          <tr>
            <th>学生</th>
            <th>文件名</th>
            <th>重复率</th>
            <th>风险等级</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in task.results" :key="r.reportId">
            <td class="student-col">{{ r.studentName || '-' }}</td>
            <td class="file-col">{{ r.fileName }}</td>
            <td>
              <div class="score-cell">
                <span class="score-num">{{ (r.overallScore * 100).toFixed(1) }}%</span>
                <div class="g-progress" style="width: 80px;">
                  <div
                    class="g-progress-bar"
                    :class="r.riskLevel.toLowerCase()"
                    :style="{ width: (r.overallScore * 100) + '%' }"
                  ></div>
                </div>
              </div>
            </td>
            <td>
              <span :class="['g-badge', riskBadge(r.riskLevel)]">
                {{ riskIcon(r.riskLevel) }} {{ riskLabel(r.riskLevel) }}
              </span>
            </td>
            <td>
              <router-link :to="`/reports/${r.reportId}/result`" class="g-btn g-btn-primary" style="padding: 5px 14px; font-size: 12px;">
                查看详情 →
              </router-link>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="g-empty">
        <div class="g-empty-icon">📊</div>
        <div class="g-empty-text">暂无查重结果</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getCheckTask, exportCheckExcel } from '../api/checks'

const route = useRoute()
const task = ref(null)
const loading = ref(true)
const exporting = ref(false)

function badgeClass(s) {
  return { COMPLETED: 'g-badge-success', RUNNING: 'g-badge-info', PENDING: 'g-badge-warning', FAILED: 'g-badge-danger' }[s] || 'g-badge-neutral'
}
function statusIcon(s) {
  return { COMPLETED: '✅', RUNNING: '⏳', PENDING: '🕐', FAILED: '❌' }[s] || ''
}
function statusLabel(s) {
  return { COMPLETED: '已完成', RUNNING: '执行中', PENDING: '待执行', FAILED: '失败' }[s] || s
}
function riskBadge(r) {
  return { HIGH: 'g-badge-danger', MEDIUM: 'g-badge-warning', LOW: 'g-badge-success' }[r] || 'g-badge-neutral'
}
function riskIcon(r) {
  return { HIGH: '🔴', MEDIUM: '🟡', LOW: '🟢' }[r] || ''
}
function riskLabel(r) {
  return { HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[r] || r
}

async function load() {
  loading.value = true
  try {
    task.value = await getCheckTask(route.params.id)
  } finally {
    loading.value = false
  }
}

async function exportExcel() {
  exporting.value = true
  try {
    const blob = await exportCheckExcel(route.params.id)
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `${task.value?.name || '查重结果'}_查重结果报告.xlsx`
    a.click()
    window.URL.revokeObjectURL(url)
  } catch (err) {
    alert(err.message || '导出失败，请稍后重试')
  } finally {
    exporting.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.top-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  margin-bottom: 20px;
}
.back-link {
  color: var(--primary);
  font-size: 14px;
  font-weight: 500;
}
.back-link:hover { color: var(--primary-dark); }

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 32px;
  color: var(--gray-400);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2.5px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.pending-card {
  text-align: center;
  padding: 48px 24px;
}
.pending-icon { font-size: 48px; margin-bottom: 12px; }
.pending-text { color: var(--gray-500); font-size: 15px; }

.student-col { font-weight: 500; }
.file-col { max-width: 220px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; color: var(--gray-600); font-size: 13px; }

.score-cell {
  display: flex;
  align-items: center;
  gap: 10px;
}
.score-num { font-weight: 600; font-size: 14px; min-width: 48px; }

.export-btn {
  margin-left: auto;
  white-space: nowrap;
}
.export-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

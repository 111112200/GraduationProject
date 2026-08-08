<template>
  <div class="dashboard">
    <!-- 欢迎横幅 -->
    <div class="welcome-banner g-card">
      <div class="welcome-left">
        <p class="welcome-kicker">检测概览</p>
        <h1 class="welcome-title">实验报告语义查重系统</h1>
        <p class="welcome-desc">集中查看报告、检测任务与历史底库的当前状态。</p>
      </div>
      <div class="welcome-right">
        <span class="welcome-version">系统版本 v1.2.5</span>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-grid">
      <div class="stat-card g-card" v-for="stat in stats" :key="stat.label">
        <span :class="['stat-indicator', stat.tone]" aria-hidden="true"></span>
        <div class="stat-info">
          <span class="stat-value">{{ stat.loading ? '...' : stat.value }}</span>
          <span class="stat-label">{{ stat.label }}</span>
        </div>
      </div>
    </div>

    <!-- 图表 / 列表区 -->
    <div class="dashboard-grid">
      <!-- 最近查重任务 -->
      <div class="g-card dash-panel">
        <div class="dash-panel-header">
          <h3 class="dash-panel-title">最近查重任务</h3>
          <router-link to="/checks" class="dash-panel-more">查看全部 →</router-link>
        </div>
        <div class="dash-panel-body">
          <div v-if="recentChecksLoading" class="g-empty">
            <div class="g-empty-text">加载中…</div>
          </div>
          <div v-else-if="recentChecks.length === 0" class="g-empty">
            <div class="g-empty-icon">📭</div>
            <div class="g-empty-text">暂无查重任务</div>
          </div>
          <div v-else class="recent-list">
            <div class="recent-item" v-for="item in recentChecks" :key="item.taskId">
              <div class="recent-item-left">
                <span class="recent-item-name">{{ item.name || item.taskId }}</span>
                <span class="recent-item-time">{{ formatTime(item.createdAt) }}</span>
              </div>
              <span class="g-badge" :class="statusClass(item.status)">{{ statusLabel(item.status) }}</span>
            </div>
          </div>
        </div>
      </div>

      <!-- 报告状态分布 -->
      <div class="g-card dash-panel">
        <div class="dash-panel-header">
          <h3 class="dash-panel-title">任务状态分布</h3>
        </div>
        <div class="dash-panel-body chart-body">
          <div v-if="checksLoading" class="g-empty">
            <div class="g-empty-text">加载中…</div>
          </div>
          <div v-else class="pie-chart-wrap">
            <div class="pie-chart" :style="pieStyle"></div>
            <div class="pie-legend">
              <div class="legend-item" v-for="seg in pieSegments" :key="seg.label">
                <span class="legend-dot" :style="{ background: seg.color }"></span>
                <span class="legend-label">{{ seg.label }}</span>
                <span class="legend-count">{{ seg.count }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { getReports } from '../api/reports'
import { listChecks } from '../api/checks'
import { getLibraryReports } from '../api/library'

const reportCount = ref(0)
const checkCount = ref(0)
const libraryCount = ref(0)
const completedCount = ref(0)
const checks = ref([])

const reportsLoading = ref(true)
const checksLoading = ref(true)
const libraryLoading = ref(true)
const recentChecksLoading = ref(true)

const stats = computed(() => [
  {
    label: '报告总数', value: reportCount.value, tone: 'blue', loading: reportsLoading.value,
  },
  {
    label: '查重任务数', value: checkCount.value, tone: 'amber', loading: checksLoading.value,
  },
  {
    label: '底库报告数', value: libraryCount.value, tone: 'green', loading: libraryLoading.value,
  },
  {
    label: '已完成任务', value: completedCount.value, tone: 'navy', loading: checksLoading.value,
  },
])

const recentChecks = computed(() => {
  const sorted = [...checks.value].sort((a, b) => {
    return new Date(b.createdAt || 0) - new Date(a.createdAt || 0)
  })
  return sorted.slice(0, 5)
})

const pieSegments = computed(() => {
  const statusMap = {}
  const colorMap = {
    COMPLETED: '#67c23a',
    RUNNING: '#409eff',
    PENDING: '#e6a23c',
    FAILED: '#f56c6c',
  }
  checks.value.forEach(c => {
    const s = c.status || 'PENDING'
    statusMap[s] = (statusMap[s] || 0) + 1
  })
  return Object.entries(statusMap).map(([status, count]) => ({
    label: statusLabel(status),
    count,
    color: colorMap[status] || '#909399',
  }))
})

const pieStyle = computed(() => {
  const total = checks.value.length
  if (total === 0) return { background: '#f0f2f5' }
  const segments = pieSegments.value
  let cumPercent = 0
  const stops = []
  segments.forEach(seg => {
    const start = cumPercent
    const end = cumPercent + (seg.count / total) * 100
    stops.push(`${seg.color} ${start}% ${end}%`)
    cumPercent = end
  })
  return { background: `conic-gradient(${stops.join(', ')})` }
})

function statusLabel(s) {
  const map = { COMPLETED: '已完成', RUNNING: '运行中', PENDING: '待处理', FAILED: '失败' }
  return map[s] || s
}

function statusClass(s) {
  const map = { COMPLETED: 'g-badge-success', RUNNING: 'g-badge-info', PENDING: 'g-badge-warning', FAILED: 'g-badge-danger' }
  return map[s] || 'g-badge-neutral'
}

function formatTime(t) {
  if (!t) return ''
  const d = new Date(t)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

onMounted(async () => {
  try {
    const res = await getReports()
    // Backend returns { reports: [...] }
    const list = res?.reports || (Array.isArray(res) ? res : [])
    reportCount.value = list.length
  } catch { reportCount.value = 0 }
  reportsLoading.value = false

  try {
    const res = await listChecks()
    // Backend returns { tasks: [...] }
    const list = res?.tasks || (Array.isArray(res) ? res : [])
    checks.value = list
    checkCount.value = list.length
    completedCount.value = list.filter(c => c.status === 'COMPLETED').length
  } catch { checks.value = []; checkCount.value = 0; completedCount.value = 0 }
  checksLoading.value = false
  recentChecksLoading.value = false

  try {
    const res = await getLibraryReports()
    // Backend returns { reports: [...] }
    const list = res?.reports || (Array.isArray(res) ? res : [])
    libraryCount.value = list.length
  } catch { libraryCount.value = 0 }
  libraryLoading.value = false
})
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

/* ===== 欢迎横幅 ===== */
.welcome-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30px 32px;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-left: 4px solid var(--primary);
}

.welcome-kicker { margin: 0 0 4px; color: var(--gray-400); font-size: 12px; font-weight: 650; }

.welcome-title {
  font-size: 20px;
  font-weight: 700;
  color: var(--gray-800);
  margin-bottom: 6px;
}

.welcome-desc {
  font-size: 14px;
  color: var(--gray-500);
  line-height: 1.6;
}

.welcome-version {
  font-size: 13px;
  color: var(--gray-400);
  background: var(--gray-50);
  padding: 4px 12px;
  border-radius: var(--radius-full);
}

/* ===== 统计卡片 ===== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 20px;
}

.stat-indicator { width: 8px; height: 42px; border-radius: 5px; flex: 0 0 8px; background: var(--primary); }
.stat-indicator.amber { background: var(--warning); }
.stat-indicator.green { background: var(--success); }
.stat-indicator.navy { background: var(--gray-800); }

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-value {
  font-size: 26px;
  font-weight: 700;
  color: var(--gray-800);
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: var(--gray-400);
  margin-top: 2px;
}

/* ===== 图表 / 列表区 ===== */
.dashboard-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.dash-panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 18px 24px;
  border-bottom: 1px solid var(--gray-100);
}

.dash-panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.dash-panel-more {
  font-size: 13px;
  color: var(--primary);
  text-decoration: none;
  font-weight: 500;
}

.dash-panel-more:hover {
  color: var(--primary-dark);
}

.dash-panel-body {
  padding: 16px 24px;
}

/* 最近查重列表 */
.recent-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.recent-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  border-radius: var(--radius-sm);
  background: var(--gray-50);
  transition: background var(--transition-fast);
}

.recent-item:hover {
  background: var(--primary-bg);
}

.recent-item-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.recent-item-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
}

.recent-item-time {
  font-size: 12px;
  color: var(--gray-400);
}

/* 饼图 */
.chart-body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}

.pie-chart-wrap {
  display: flex;
  align-items: center;
  gap: 32px;
  width: 100%;
  justify-content: center;
}

.pie-chart {
  width: 140px;
  height: 140px;
  border-radius: 50%;
  flex-shrink: 0;
  position: relative;
}

.pie-chart::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 70px;
  height: 70px;
  background: #fff;
  border-radius: 50%;
  transform: translate(-50%, -50%);
}

.pie-legend {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--gray-600);
}

.legend-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}

.legend-count {
  font-weight: 600;
  color: var(--gray-800);
  margin-left: auto;
}

/* 响应式 */
@media (max-width: 1100px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 640px) {
  .stats-grid {
    grid-template-columns: 1fr;
  }
  .welcome-banner {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
}
</style>

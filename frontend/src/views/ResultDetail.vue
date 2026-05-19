<template>
  <div class="page">
    <div class="top-bar">
      <a href="#" @click.prevent="$router.back()" class="back-link">← 返回上一页</a>
      <h2 class="g-page-title">查重结果详情</h2>
    </div>

    <div v-if="loading" class="loading-state">
      <div class="spinner"></div>
      <span>加载中...</span>
    </div>

    <div v-else-if="report.status === 'FAILED'" class="status-card status-failed g-card g-card-body">
      <div class="status-icon">❌</div>
      <div class="status-content">
        <div class="status-title">报告解析失败</div>
        <div class="status-desc">该报告在上传后解析失败，无法进行查重检测。</div>
        <div v-if="report.parseError" class="status-error-detail">
          <span class="error-label">错误详情：</span>{{ report.parseError }}
        </div>
      </div>
    </div>

    <div v-else-if="report.status === 'UPLOADED'" class="status-card status-pending g-card g-card-body">
      <div class="status-icon">⏳</div>
      <div class="status-content">
        <div class="status-title">报告尚未解析</div>
        <div class="status-desc">该报告还未完成解析，请稍后再来查看结果。</div>
      </div>
    </div>

    <div v-else-if="!result.hasCheckResult" class="status-card status-awaiting g-card g-card-body">
      <div class="status-icon">🔍</div>
      <div class="status-content">
        <div class="status-title">待检测</div>
        <div class="status-desc">该报告已成功解析，但尚未创建查重任务。请前往查重管理创建查重任务后再来查看结果。</div>
      </div>
    </div>

    <div v-else>
      <!-- 概览卡片 -->
      <div class="overview-card g-card g-card-body">
        <div class="overview-score">
          <div class="score-ring" :class="result.riskLevel?.toLowerCase()">
            {{ (result.overallScore * 100).toFixed(1) }}%
          </div>
          <div class="score-label">
            <div class="score-title">整体重复率</div>
            <span :class="['g-badge', riskBadge(result.riskLevel)]">
              {{ riskIcon(result.riskLevel) }} {{ riskLabel(result.riskLevel) }}
            </span>
          </div>
        </div>
        <button v-if="!inLibrary" @click="addToLib" class="g-btn g-btn-success">📚 加入底库</button>
        <span v-else class="g-badge g-badge-success">✅ 已入库</span>
      </div>

      <!-- 分组展示 -->
      <div v-if="result.segments?.length" class="segments-section">

        <!-- 班级内部互查 -->
        <div v-if="inClassSegments.length" class="group fade-in-up">
          <div class="group-header in-class">
            <span class="group-icon">👥</span>
            <span class="group-title">班级内部互查</span>
            <span class="group-count">{{ inClassSegments.length }} 处相似片段</span>
          </div>
          <div v-for="(s, i) in inClassSegments" :key="'ic-' + i" class="segment-card">
            <div class="seg-col source">
              <div class="seg-label">📝 被检报告</div>
              <div class="seg-text">{{ s.sourceText }}</div>
            </div>
            <div class="seg-divider">
              <div class="sim-badge in-class-sim">
                <div class="sim-value">{{ (s.similarity * 100).toFixed(0) }}%</div>
                <div class="sim-tag">班内</div>
              </div>
            </div>
            <div class="seg-col target">
              <div class="seg-label">🔗 班内同学：{{ s.targetStudentName }}</div>
              <div class="seg-text">{{ s.targetText }}</div>
            </div>
          </div>
        </div>

        <!-- 历史底库对比 -->
        <div v-if="historySegments.length" class="group fade-in-up" style="animation-delay: 0.1s;">
          <div class="group-header history">
            <span class="group-icon">📚</span>
            <span class="group-title">历史底库比对</span>
            <span class="group-count">{{ historySegments.length }} 处相似片段</span>
          </div>
          <div v-for="(s, i) in historySegments" :key="'hs-' + i" class="segment-card">
            <div class="seg-col source">
              <div class="seg-label">📝 被检报告</div>
              <div class="seg-text">{{ s.sourceText }}</div>
            </div>
            <div class="seg-divider">
              <div class="sim-badge history-sim">
                <div class="sim-value">{{ (s.similarity * 100).toFixed(0) }}%</div>
                <div class="sim-tag">底库</div>
              </div>
            </div>
            <div class="seg-col target">
              <div class="seg-label">🔗 历史报告：{{ s.targetStudentName || '未知' }}</div>
              <div class="seg-text">{{ s.targetText }}</div>
            </div>
          </div>
        </div>

      </div>

      <div v-else class="g-card g-card-body">
        <div class="g-empty">
          <div class="g-empty-icon">✨</div>
          <div class="g-empty-text">未发现相似片段</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getReport, getReportResult } from '../api/reports'
import { addToLibrary, getLibraryReports } from '../api/library'

const route = useRoute()
const result = ref({ segments: [] })
const report = ref({})
const loading = ref(true)
const inLibrary = ref(false)

const inClassSegments = computed(() =>
  (result.value.segments || []).filter(s => s.mode === 'IN_CLASS')
)
const historySegments = computed(() =>
  (result.value.segments || []).filter(s => s.mode === 'HISTORY')
)

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
    const [reportMeta, res, lib] = await Promise.all([
      getReport(route.params.reportId),
      getReportResult(route.params.reportId),
      getLibraryReports(),
    ])
    report.value = reportMeta
    result.value = res
    inLibrary.value = (lib.reports || []).some(r => r.reportId === parseInt(route.params.reportId))
  } finally {
    loading.value = false
  }
}

async function addToLib() {
  try {
    await addToLibrary(parseInt(route.params.reportId))
    inLibrary.value = true
  } catch (err) {
    alert(err.message || '加入底库失败')
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
.back-link { color: var(--primary); font-size: 14px; font-weight: 500; }
.back-link:hover { color: var(--primary-dark); }

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 32px;
  color: var(--gray-400);
}
.spinner {
  width: 20px; height: 20px;
  border: 2.5px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 概览 */
.overview-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
.overview-score { display: flex; align-items: center; gap: 20px; }
.score-ring {
  width: 72px; height: 72px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 18px;
  font-weight: 700;
  border: 4px solid;
}
.score-ring.low { border-color: var(--success); color: var(--success); background: var(--success-bg); }
.score-ring.medium { border-color: var(--warning); color: #b45309; background: var(--warning-bg); }
.score-ring.high { border-color: var(--danger); color: var(--danger); background: var(--danger-bg); }
.score-title { font-size: 14px; color: var(--gray-500); margin-bottom: 6px; }

/* 分组 */
.segments-section { display: flex; flex-direction: column; gap: 24px; }
.group-header {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 18px;
  border-radius: var(--radius-md) var(--radius-md) 0 0;
  font-weight: 600;
  font-size: 14px;
}
.group-header.in-class { background: #eff6ff; color: #1d4ed8; border-left: 4px solid #3b82f6; }
.group-header.history { background: #fdf4ff; color: #7e22ce; border-left: 4px solid #a855f7; }
.group-icon { font-size: 16px; }
.group-title { flex: 1; }
.group-count { font-size: 12px; font-weight: normal; opacity: 0.7; }

/* 片段卡片 */
.segment-card {
  display: grid;
  grid-template-columns: 1fr auto 1fr;
  gap: 0;
  border: 1px solid var(--gray-200);
  border-top: none;
  background: #fff;
  transition: box-shadow var(--transition-fast);
}
.segment-card:hover { box-shadow: var(--shadow-md); }
.segment-card:last-child { border-radius: 0 0 var(--radius-md) var(--radius-md); }

.seg-col { padding: 16px 18px; }
.seg-label { font-size: 12px; color: var(--gray-500); margin-bottom: 6px; font-weight: 500; }
.seg-text {
  font-size: 14px;
  line-height: 1.65;
  max-height: 140px;
  overflow-y: auto;
  color: var(--gray-700);
}
.source { background: #fefce8; }
.target { background: var(--gray-50); }

.seg-divider {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0 6px;
  background: var(--gray-50);
  border-left: 1px solid var(--gray-100);
  border-right: 1px solid var(--gray-100);
}
.sim-badge {
  text-align: center;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
  min-width: 54px;
}
.sim-value { font-size: 16px; font-weight: 700; }
.sim-tag { font-size: 11px; font-weight: 600; margin-top: 2px; }
.in-class-sim { color: #1d4ed8; background: #dbeafe; }
.history-sim { color: #7e22ce; background: #f3e8ff; }

/* 状态卡片（解析失败 / 未解析）*/
.status-card {
  display: flex;
  align-items: flex-start;
  gap: 20px;
  padding: 28px 28px;
}

.status-icon {
  font-size: 36px;
  flex-shrink: 0;
  line-height: 1;
  margin-top: 2px;
}

.status-content { display: flex; flex-direction: column; gap: 8px; }

.status-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--gray-900);
}

.status-desc {
  font-size: 14px;
  color: var(--gray-500);
}

.status-error-detail {
  margin-top: 4px;
  padding: 12px 14px;
  background: var(--danger-bg);
  border-left: 3px solid var(--danger);
  border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
  font-size: 13px;
  color: var(--gray-700);
  word-break: break-all;
}

.error-label {
  font-weight: 600;
  color: var(--danger);
  margin-right: 4px;
}

.status-failed { border-left: 4px solid var(--danger); }
.status-pending { border-left: 4px solid var(--warning); }
.status-awaiting { border-left: 4px solid var(--primary); }
</style>

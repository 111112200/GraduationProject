<template>
  <div class="page result-page">
    <div class="result-nav">
      <a href="#" class="back-link" @click.prevent="$router.back()">返回上一页</a>
      <span class="result-nav-separator">/</span>
      <span class="result-nav-current">检测结果</span>
    </div>

    <div v-if="loading" class="loading-state" aria-live="polite">
      <div class="spinner"></div>
      <span>正在载入检测结果</span>
    </div>

    <section v-else-if="report.status === 'FAILED'" class="status-card status-failed">
      <div class="status-mark" aria-hidden="true">!</div>
      <div class="status-content">
        <p class="status-kicker">处理状态</p>
        <h2 class="status-title">报告解析失败</h2>
        <p class="status-desc">该报告在上传后解析失败，无法进行查重检测。</p>
        <p v-if="report.parseError" class="status-error-detail">
          <span>错误详情</span>{{ report.parseError }}
        </p>
      </div>
    </section>

    <section v-else-if="report.status === 'UPLOADED'" class="status-card status-pending">
      <div class="status-mark" aria-hidden="true">...</div>
      <div class="status-content">
        <p class="status-kicker">处理状态</p>
        <h2 class="status-title">报告尚未解析</h2>
        <p class="status-desc">该报告还未完成解析，请稍后再来查看结果。</p>
      </div>
    </section>

    <section v-else-if="!result.hasCheckResult" class="status-card status-awaiting">
      <div class="status-mark" aria-hidden="true">?</div>
      <div class="status-content">
        <p class="status-kicker">检测状态</p>
        <h2 class="status-title">等待创建检测任务</h2>
        <p class="status-desc">该报告已经解析完成。创建查重任务后，系统将在这里呈现检测结果。</p>
      </div>
    </section>

    <template v-else>
      <section :class="['result-hero', riskTone]">
        <div class="result-hero-copy">
          <p class="result-eyebrow">实验报告检测</p>
          <h2 class="report-title" :title="reportTitle">{{ reportTitle }}</h2>
          <p class="report-subtitle">{{ reportOwner }}</p>
          <div class="risk-summary">
            <span :class="['risk-dot', riskTone]" aria-hidden="true"></span>
            <span>{{ riskLabel(result.riskLevel) }}</span>
            <span class="risk-summary-divider"></span>
            <span>{{ riskDescription }}</span>
          </div>
        </div>

        <div class="score-panel">
          <div class="score-orbit" :style="{ '--score': scorePercent + '%' }">
            <div class="score-orbit-inner">
              <strong>{{ scorePercent }}%</strong>
              <span>重复率</span>
            </div>
          </div>
          <button v-if="!inLibrary" class="g-btn g-btn-primary library-button" @click="addToLib">
            加入底库
          </button>
          <span v-else class="library-state">已加入底库</span>
        </div>
      </section>

      <section class="metric-grid" aria-label="检测结果概览">
        <article class="metric-card">
          <p class="metric-label">相似片段</p>
          <strong class="metric-value">{{ totalSegments }}</strong>
          <span class="metric-note">共发现的匹配内容</span>
        </article>
        <article class="metric-card">
          <p class="metric-label">班级互查</p>
          <strong class="metric-value">{{ inClassSegments.length }}</strong>
          <span class="metric-note">来自同班报告的匹配</span>
        </article>
        <article class="metric-card">
          <p class="metric-label">历史底库</p>
          <strong class="metric-value">{{ historySegments.length }}</strong>
          <span class="metric-note">来自历史报告的匹配</span>
        </article>
      </section>

      <section v-if="totalSegments" class="matches-section">
        <div class="matches-heading">
          <div>
            <p class="section-kicker">匹配明细</p>
            <h3>相似片段</h3>
          </div>
          <div class="segment-filter" role="tablist" aria-label="匹配来源筛选">
            <button
              v-for="option in filterOptions"
              :key="option.value"
              :class="['filter-button', { active: activeFilter === option.value }]"
              type="button"
              role="tab"
              :aria-selected="activeFilter === option.value"
              @click="activeFilter = option.value"
            >
              {{ option.label }}
              <span>{{ option.count }}</span>
            </button>
          </div>
        </div>

        <div v-if="showInClass" class="match-group">
          <div class="group-heading">
            <div>
              <span class="group-marker in-class"></span>
              <span>班级内部互查</span>
            </div>
            <span>{{ inClassSegments.length }} 处匹配</span>
          </div>
          <article v-for="(segment, index) in inClassSegments" :key="`in-class-${index}`" class="match-card">
            <div class="match-card-header">
              <span class="match-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="match-card-meta">
                <span class="source-tag in-class">班内报告</span>
                <span>与 {{ segment.targetStudentName || '同班学生' }} 的报告匹配</span>
              </div>
              <strong class="similarity-value in-class">{{ similarityPercent(segment.similarity) }}%</strong>
            </div>
            <div class="match-text-grid">
              <div class="text-column source-text">
                <p>当前报告</p>
                <div>{{ segment.sourceText }}</div>
              </div>
              <div class="match-connector" aria-hidden="true"><span></span></div>
              <div class="text-column target-text">
                <p>对比报告</p>
                <div>{{ segment.targetText }}</div>
              </div>
            </div>
          </article>
        </div>

        <div v-if="showHistory" class="match-group">
          <div class="group-heading">
            <div>
              <span class="group-marker history"></span>
              <span>历史底库比对</span>
            </div>
            <span>{{ historySegments.length }} 处匹配</span>
          </div>
          <article v-for="(segment, index) in historySegments" :key="`history-${index}`" class="match-card">
            <div class="match-card-header">
              <span class="match-index">{{ String(index + 1).padStart(2, '0') }}</span>
              <div class="match-card-meta">
                <span class="source-tag history">历史底库</span>
                <span>与 {{ segment.targetStudentName || '历史报告' }} 的内容匹配</span>
              </div>
              <strong class="similarity-value history">{{ similarityPercent(segment.similarity) }}%</strong>
            </div>
            <div class="match-text-grid">
              <div class="text-column source-text">
                <p>当前报告</p>
                <div>{{ segment.sourceText }}</div>
              </div>
              <div class="match-connector" aria-hidden="true"><span></span></div>
              <div class="text-column target-text">
                <p>底库报告</p>
                <div>{{ segment.targetText }}</div>
              </div>
            </div>
          </article>
        </div>
      </section>

      <section v-else class="no-match-card">
        <div class="no-match-mark" aria-hidden="true">0</div>
        <div>
          <p class="section-kicker">检测完成</p>
          <h3>未发现相似片段</h3>
          <p>当前报告未检出达到阈值的相似内容。</p>
        </div>
      </section>
    </template>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import { getReport, getReportResult } from '../api/reports'
import { addToLibrary, getLibraryReports } from '../api/library'

const route = useRoute()
const result = ref({ segments: [] })
const report = ref({})
const loading = ref(true)
const inLibrary = ref(false)
const activeFilter = ref('ALL')

const inClassSegments = computed(() =>
  (result.value.segments || []).filter(segment => segment.mode === 'IN_CLASS')
)
const historySegments = computed(() =>
  (result.value.segments || []).filter(segment => segment.mode === 'HISTORY')
)
const totalSegments = computed(() => inClassSegments.value.length + historySegments.value.length)
const scorePercent = computed(() => (Math.max(0, Math.min(1, Number(result.value.overallScore) || 0)) * 100).toFixed(1))
const reportTitle = computed(() => report.value.fileName || report.value.originalFileName || report.value.name || '实验报告')
const reportOwner = computed(() => report.value.studentName || report.value.className || '检测完成后可查看相似来源')
const riskTone = computed(() => (result.value.riskLevel || 'LOW').toLowerCase())
const riskDescription = computed(() => ({
  HIGH: '建议优先复核',
  MEDIUM: '建议人工核查',
  LOW: '相似度处于可接受范围',
}[result.value.riskLevel] || '检测完成'))
const filterOptions = computed(() => [
  { value: 'ALL', label: '全部', count: totalSegments.value },
  { value: 'IN_CLASS', label: '班级互查', count: inClassSegments.value.length },
  { value: 'HISTORY', label: '历史底库', count: historySegments.value.length },
])
const showInClass = computed(() => activeFilter.value !== 'HISTORY' && inClassSegments.value.length > 0)
const showHistory = computed(() => activeFilter.value !== 'IN_CLASS' && historySegments.value.length > 0)

function riskLabel(riskLevel) {
  return { HIGH: '高风险', MEDIUM: '中风险', LOW: '低风险' }[riskLevel] || '检测完成'
}

function similarityPercent(value) {
  return Math.round((Number(value) || 0) * 100)
}

async function load() {
  loading.value = true
  try {
    const [reportMeta, checkResult, library] = await Promise.all([
      getReport(route.params.reportId),
      getReportResult(route.params.reportId),
      getLibraryReports(),
    ])
    report.value = reportMeta
    result.value = checkResult
    inLibrary.value = (library.reports || []).some(item => item.reportId === Number(route.params.reportId))
  } finally {
    loading.value = false
  }
}

async function addToLib() {
  try {
    await addToLibrary(Number(route.params.reportId))
    inLibrary.value = true
  } catch (error) {
    alert(error.message || '加入底库失败')
  }
}

onMounted(load)
</script>

<style scoped>
.result-page {
  max-width: 1280px;
  margin: 0 auto;
  padding-bottom: 36px;
}

.result-nav {
  display: flex;
  align-items: center;
  gap: 8px;
  min-height: 28px;
  margin-bottom: 18px;
  font-size: 13px;
}

.back-link { color: var(--gray-500); }
.back-link:hover { color: var(--primary-dark); }
.result-nav-separator { color: var(--gray-300); }
.result-nav-current { color: var(--gray-400); }

.loading-state {
  display: flex;
  align-items: center;
  gap: 10px;
  min-height: 180px;
  color: var(--gray-500);
}

.spinner {
  width: 20px;
  height: 20px;
  border: 2px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.status-card,
.no-match-card {
  display: flex;
  align-items: flex-start;
  gap: 18px;
  padding: 32px;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  box-shadow: var(--shadow-sm);
}

.status-mark,
.no-match-mark {
  display: grid;
  place-items: center;
  width: 44px;
  height: 44px;
  flex: 0 0 44px;
  border-radius: 50%;
  font-size: 18px;
  font-weight: 700;
}

.status-failed { border-left: 4px solid var(--danger); }
.status-pending { border-left: 4px solid var(--warning); }
.status-awaiting { border-left: 4px solid var(--primary); }
.status-failed .status-mark { color: #b42318; background: var(--danger-bg); }
.status-pending .status-mark { color: #a15c00; background: var(--warning-bg); }
.status-awaiting .status-mark { color: var(--primary-dark); background: var(--primary-bg); }

.status-content { min-width: 0; }
.status-kicker,
.section-kicker,
.result-eyebrow {
  margin: 0 0 5px;
  color: var(--gray-400);
  font-size: 12px;
  font-weight: 600;
  letter-spacing: 0;
}

.status-title,
.no-match-card h3 {
  margin: 0;
  color: var(--gray-900);
  font-size: 20px;
  line-height: 1.35;
}

.status-desc,
.no-match-card p:last-child {
  margin: 8px 0 0;
  color: var(--gray-500);
  font-size: 14px;
}

.status-error-detail {
  margin: 15px 0 0;
  padding: 10px 12px;
  overflow-wrap: anywhere;
  border-radius: 4px;
  color: var(--gray-600);
  background: var(--danger-bg);
  font-size: 13px;
}

.status-error-detail span {
  margin-right: 9px;
  color: var(--danger);
  font-weight: 600;
}

.result-hero {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 28px;
  padding: 30px 32px;
  overflow: hidden;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: #fff;
  box-shadow: var(--shadow-sm);
}

.result-hero.high { border-top: 4px solid var(--danger); }
.result-hero.medium { border-top: 4px solid var(--warning); }
.result-hero.low { border-top: 4px solid var(--success); }
.result-hero-copy { min-width: 0; }

.report-title {
  max-width: 700px;
  margin: 0;
  overflow: hidden;
  color: var(--gray-900);
  font-size: 26px;
  font-weight: 700;
  line-height: 1.32;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.report-subtitle {
  margin: 7px 0 0;
  color: var(--gray-500);
  font-size: 14px;
}

.risk-summary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  margin-top: 21px;
  color: var(--gray-600);
  font-size: 13px;
}

.risk-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--gray-400);
}
.risk-dot.high { background: var(--danger); }
.risk-dot.medium { background: var(--warning); }
.risk-dot.low { background: var(--success); }
.risk-summary-divider { width: 1px; height: 12px; background: var(--gray-200); }

.score-panel {
  display: grid;
  flex: 0 0 138px;
  justify-items: center;
  gap: 14px;
}

.score-orbit {
  display: grid;
  width: 118px;
  height: 118px;
  place-items: center;
  border-radius: 50%;
  background: conic-gradient(var(--primary) var(--score), var(--gray-100) 0);
}
.result-hero.high .score-orbit { background: conic-gradient(var(--danger) var(--score), var(--gray-100) 0); }
.result-hero.medium .score-orbit { background: conic-gradient(var(--warning) var(--score), var(--gray-100) 0); }
.result-hero.low .score-orbit { background: conic-gradient(var(--success) var(--score), var(--gray-100) 0); }

.score-orbit-inner {
  display: grid;
  width: 102px;
  height: 102px;
  place-content: center;
  border-radius: 50%;
  background: #fff;
  text-align: center;
}
.score-orbit-inner strong { color: var(--gray-900); font-size: 23px; line-height: 1.2; }
.score-orbit-inner span { margin-top: 3px; color: var(--gray-500); font-size: 12px; }

.library-button { width: 118px; min-height: 34px; padding: 7px 12px; font-size: 13px; }
.library-state { color: var(--success); font-size: 13px; font-weight: 600; }

.metric-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin: 16px 0 30px;
}

.metric-card {
  min-height: 132px;
  padding: 20px;
  border: 1px solid var(--gray-200);
  border-radius: 6px;
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.metric-label { margin: 0; color: var(--gray-500); font-size: 13px; }
.metric-value { display: block; margin-top: 7px; color: var(--gray-900); font-size: 30px; line-height: 1.15; }
.metric-note { display: block; margin-top: 8px; color: var(--gray-400); font-size: 12px; }

.matches-section { margin-top: 4px; }
.matches-heading {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 16px;
}
.matches-heading h3 { margin: 0; color: var(--gray-900); font-size: 20px; line-height: 1.35; }

.segment-filter {
  display: inline-flex;
  max-width: 100%;
  overflow-x: auto;
  border: 1px solid var(--gray-200);
  border-radius: 6px;
  background: #fff;
}
.filter-button {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  min-height: 34px;
  padding: 6px 11px;
  border: 0;
  border-right: 1px solid var(--gray-200);
  background: transparent;
  color: var(--gray-500);
  cursor: pointer;
  font-size: 13px;
  white-space: nowrap;
}
.filter-button:last-child { border-right: 0; }
.filter-button:hover { color: var(--primary-dark); background: var(--primary-bg); }
.filter-button.active { color: var(--primary-dark); background: var(--primary-bg); font-weight: 600; }
.filter-button span { color: inherit; font-size: 12px; opacity: 0.75; }

.match-group + .match-group { margin-top: 30px; }
.group-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin: 0 0 10px;
  color: var(--gray-700);
  font-size: 14px;
  font-weight: 600;
}
.group-heading > div { display: inline-flex; align-items: center; gap: 8px; }
.group-heading > span { color: var(--gray-400); font-size: 12px; font-weight: 500; }
.group-marker { width: 8px; height: 8px; border-radius: 50%; background: var(--primary); }
.group-marker.in-class { background: #2f80ed; }
.group-marker.history { background: #18a67a; }

.match-card {
  overflow: hidden;
  border: 1px solid var(--gray-200);
  border-radius: 6px;
  background: #fff;
  box-shadow: var(--shadow-sm);
}
.match-card + .match-card { margin-top: 10px; }

.match-card-header {
  display: flex;
  align-items: center;
  min-height: 48px;
  padding: 9px 18px;
  border-bottom: 1px solid var(--gray-100);
  background: var(--gray-50);
}
.match-index { width: 34px; color: var(--gray-400); font-size: 12px; font-variant-numeric: tabular-nums; }
.match-card-meta { display: flex; flex: 1; align-items: center; min-width: 0; gap: 8px; color: var(--gray-500); font-size: 13px; }
.match-card-meta > span:last-child { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.source-tag { flex: 0 0 auto; padding: 2px 7px; border-radius: 3px; font-size: 11px; font-weight: 600; }
.source-tag.in-class { color: #155db3; background: #eaf3ff; }
.source-tag.history { color: #06785a; background: #e6f7f1; }
.similarity-value { margin-left: 12px; font-size: 15px; font-variant-numeric: tabular-nums; }
.similarity-value.in-class { color: #155db3; }
.similarity-value.history { color: #06785a; }

.match-text-grid { display: grid; grid-template-columns: minmax(0, 1fr) 42px minmax(0, 1fr); }
.text-column { min-width: 0; padding: 18px; }
.text-column p { margin: 0 0 8px; color: var(--gray-400); font-size: 12px; font-weight: 600; }
.text-column div { max-height: 144px; overflow: auto; color: var(--gray-700); font-size: 14px; line-height: 1.75; overflow-wrap: anywhere; }
.source-text { background: #fffdf4; }
.target-text { background: #f8fbff; }
.match-connector { display: grid; place-items: center; background: #fff; }
.match-connector span { width: 18px; height: 1px; position: relative; background: var(--gray-300); }
.match-connector span::after { position: absolute; top: -3px; right: 0; width: 7px; height: 7px; border-top: 1px solid var(--gray-300); border-right: 1px solid var(--gray-300); content: ''; transform: rotate(45deg); }

.no-match-card { border-left: 4px solid var(--success); }
.no-match-mark { color: #16865e; background: #e6f7f1; }

@media (max-width: 760px) {
  .result-hero { align-items: flex-start; flex-direction: column; padding: 24px 20px; }
  .report-title { max-width: 100%; font-size: 22px; white-space: normal; }
  .score-panel { grid-template-columns: auto auto; width: 100%; justify-content: start; align-items: center; }
  .score-orbit { grid-row: span 2; }
  .library-button { width: auto; }
  .metric-grid { grid-template-columns: 1fr; gap: 10px; }
  .metric-card { display: grid; min-height: 0; grid-template-columns: 1fr auto; align-items: center; padding: 16px; }
  .metric-value { grid-row: span 2; grid-column: 2; margin: 0; }
  .metric-note { margin-top: 3px; }
  .matches-heading { align-items: flex-start; flex-direction: column; }
  .segment-filter { width: 100%; }
  .filter-button { flex: 1; justify-content: center; }
  .match-text-grid { grid-template-columns: 1fr; }
  .match-connector { height: 18px; }
  .match-connector span { transform: rotate(90deg); }
  .match-card-header { align-items: flex-start; padding: 10px 14px; }
  .match-card-meta { align-items: flex-start; flex-direction: column; gap: 4px; }
  .match-card-meta > span:last-child { white-space: normal; }
  .text-column { padding: 15px; }
}

@media (max-width: 460px) {
  .result-page { padding-bottom: 20px; }
  .risk-summary { align-items: flex-start; flex-wrap: wrap; }
  .risk-summary-divider { display: none; }
  .status-card,
  .no-match-card { padding: 22px 18px; }
  .similarity-value { font-size: 14px; }
}
</style>

<template>
  <div class="page">
    <h2 class="g-page-title">🆕 创建查重任务</h2>
    <p class="g-page-desc">选择实验、查重模式和待检报告，一键启动语义查重</p>
    <div class="g-card g-card-body">
      <div class="form-row">
        <label>任务名称</label>
        <input v-model="name" placeholder="如：2025春 软工实验1 查重" class="g-input" style="min-width: 360px;" />
      </div>
      <div class="form-grid">
        <div class="form-row">
          <label>查重模式</label>
          <select v-model="mode" class="g-select">
            <option value="IN_CLASS">仅班级内部互查</option>
            <option value="HISTORY_ONLY">仅历史底库比对</option>
            <option value="BOTH">双重模式</option>
          </select>
        </div>
        <div class="form-row">
          <label>选择班级</label>
          <select v-model="selectedClassId" class="g-select" @change="onClassChange">
            <option :value="null">全部班级</option>
            <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.name }}{{ c.grade ? ` (${c.grade})` : '' }}</option>
          </select>
        </div>
      </div>
      <div class="form-row">
        <label>选择报告 <span class="report-count">（已选 {{ reportIds.length }} / {{ filteredReports.length }}）</span></label>
        <div class="select-actions">
          <button type="button" @click="selectAll" class="g-btn g-btn-primary" style="padding: 5px 12px; font-size: 12px;">全选</button>
          <button type="button" @click="selectNone" class="g-btn g-btn-danger" style="padding: 5px 12px; font-size: 12px;">清空</button>
        </div>
        <div v-if="filteredReports.length === 0" class="empty-hint">
          <span>📭 {{ selectedClassId ? '当前班级暂无已解析的报告' : '暂无已解析的报告' }}</span>
        </div>
        <div v-else class="report-grid">
          <label v-for="r in filteredReports" :key="r.id" class="report-item" :class="{ selected: reportIds.includes(r.id) }">
            <input type="checkbox" :value="r.id" v-model="reportIds" />
            <span class="report-name">{{ r.fileName || r.studentName }}</span>
            <span :class="['g-badge', r.hasCheckResult ? 'g-badge-success' : 'g-badge-warning']" style="font-size: 11px;">{{ r.hasCheckResult ? '已检测' : '待检测' }}</span>
          </label>
        </div>
      </div>
      <button @click="create" :disabled="creating" class="g-btn g-btn-primary" style="margin-top: 8px;">
        {{ creating ? '创建中...' : '🚀 创建并开始查重' }}
      </button>
      <p v-if="msg" :class="msgClass" style="margin-top: 12px;">{{ msg }}</p>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getExperiments, getClasses } from '../api/course'
import { getReports } from '../api/reports'
import { createCheck } from '../api/checks'

const router = useRouter()
const experiments = ref([])
const experimentId = ref(null)
const classes = ref([])
const selectedClassId = ref(null)
const allReports = ref([])
const name = ref('')
const mode = ref('BOTH')
const reportIds = ref([])
const creating = ref(false)
const msg = ref('')
const msgClass = ref('')

// 根据选中的班级过滤报告
const filteredReports = computed(() => {
  if (!selectedClassId.value) return allReports.value
  return allReports.value.filter(r => r.classId === selectedClassId.value)
})

function selectAll() { reportIds.value = filteredReports.value.map(r => r.id) }
function selectNone() { reportIds.value = [] }

function onClassChange() {
  // 切换班级时，清空已选报告并自动选择待检测的报告
  const pending = filteredReports.value.filter(r => !r.hasCheckResult).map(r => r.id)
  reportIds.value = pending.length > 0 ? pending : []
}

async function loadClasses() {
  const res = await getClasses()
  classes.value = res.classes || []
}

async function loadExperiments() {
  const res = await getExperiments()
  experiments.value = res.experiments || []
  if (experiments.value.length && !experimentId.value) experimentId.value = experiments.value[0].id
}

async function loadReports() {
  const res = await getReports()
  allReports.value = (res.reports || []).filter(r => r.status === 'PARSED').sort((a, b) => {
    if (a.hasCheckResult === b.hasCheckResult) return b.id - a.id
    return a.hasCheckResult ? 1 : -1
  })
  
  const pendingIds = allReports.value.filter(r => !r.hasCheckResult).map(r => r.id)
  reportIds.value = pendingIds.length > 0 ? pendingIds : []
}

async function create() {
  if (!name.value.trim() || !reportIds.value.length) {
    msg.value = '请填写任务名称并选择至少一份报告'
    msgClass.value = 'g-msg-error'
    return
  }
  creating.value = true
  msg.value = ''
  try {
    const res = await createCheck({
      name: name.value,
      experimentId: experimentId.value,
      mode: mode.value,
      reportIds: reportIds.value,
      highRiskThreshold: 0.8,
      similarThreshold: 0.5,
    })
    msg.value = '任务已创建，正在执行查重...'
    msgClass.value = 'g-msg-success'
    setTimeout(() => router.push(`/checks/${res.taskId}`), 1500)
  } catch (e) {
    msg.value = '创建失败: ' + (e.message || e)
    msgClass.value = 'g-msg-error'
  } finally {
    creating.value = false
  }
}

onMounted(async () => {
  await Promise.all([loadExperiments(), loadClasses()])
  loadReports()
})
</script>

<style scoped>
.form-row { margin-bottom: 20px; }
.form-row label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  font-size: 14px;
  color: var(--gray-700);
}
.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}
.report-count { font-weight: 400; color: var(--gray-400); font-size: 13px; }
.select-actions { display: flex; gap: 8px; margin-bottom: 10px; }

.report-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px;
}
.report-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border: 1.5px solid var(--gray-200);
  border-radius: var(--radius-sm);
  cursor: pointer;
  font-size: 13px;
  font-weight: 400;
  transition: all var(--transition-fast);
  background: #fff;
}
.report-item:hover { border-color: var(--primary-light); background: var(--primary-bg); }
.report-item.selected { border-color: var(--primary); background: var(--primary-bg); }
.report-item input[type="checkbox"] { accent-color: var(--primary); }
.report-name { color: var(--gray-700); }
.empty-hint {
  padding: 24px;
  text-align: center;
  color: var(--gray-400);
  font-size: 14px;
  border: 1.5px dashed var(--gray-200);
  border-radius: var(--radius-sm);
  background: var(--gray-50, #f9fafb);
}
</style>

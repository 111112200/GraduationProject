<template>
  <div class="page">
    <h2 class="g-page-title">📋 报告列表</h2>
    <div class="g-toolbar">
      <select v-model="classId" @change="load" class="g-select">
        <option value="">全部班级</option>
        <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.name }}</option>
      </select>
      <button :class="['g-btn', classId ? 'g-btn-primary' : '']" @click="resetFilters">重置筛选</button>
    </div>
    <div class="g-card">
      <table class="g-table" v-if="reports.length">
        <thead>
          <tr>
            <th>序号</th>
            <th>学生</th>
            <th>学号</th>
            <th>文件名</th>
            <th>状态</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, index) in reports" :key="r.id">
            <td class="id-col">{{ reports.length - index }}</td>
            <td>{{ r.studentName || '-' }}</td>
            <td class="mono">{{ r.studentId || '-' }}</td>
            <td class="file-col">{{ r.fileName }}</td>
            <td>
              <span :class="['g-badge', statusClass(displayStatus(r))]">
                {{ statusLabel(displayStatus(r)) }}
              </span>
            </td>
            <td class="action-col">
              <router-link :to="`/reports/${r.id}/result`" class="action-link">查看结果</router-link>
              <button @click="openChunks(r)" class="action-btn-info">查看分块</button>
              <button @click="handleDelete(r.id)" class="action-btn-danger">删除</button>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="g-empty">
        <div class="g-empty-icon">📄</div>
        <div class="g-empty-text">暂无报告，请先上传实验报告</div>
      </div>
    </div>

  </div>

  <!-- 确认删除弹窗 -->
  <Teleport to="body">
    <div class="g-modal-overlay" v-if="deleteModal.visible">
      <div class="g-modal fade-in-up">
        <div class="g-modal-header">
          <h3 class="g-modal-title">⚠️ 确认删除</h3>
        </div>
        <div class="g-modal-body">
          <p>确定要删除这份报告吗？删除后相关的查重记录也会被一并清除且不可恢复。</p>
        </div>
        <div class="g-modal-footer">
          <button @click="closeDeleteModal" class="g-btn">取消</button>
          <button @click="confirmDelete" class="g-btn g-btn-danger" :disabled="deleteModal.loading">
            {{ deleteModal.loading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- 分块可视化抽屉 -->
  <ReportChunksDrawer
    :visible="chunksDrawer.visible"
    :report-id="chunksDrawer.reportId"
    :report-name="chunksDrawer.reportName"
    @close="closeChunks"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getClasses } from '../api/course'
import { getReports, deleteReport } from '../api/reports'
import ReportChunksDrawer from '../components/ReportChunksDrawer.vue'

const classes = ref([])
const reports = ref([])
const classId = ref('')

const deleteModal = ref({
  visible: false,
  reportId: null,
  loading: false
})

const chunksDrawer = ref({
  visible: false,
  reportId: null,
  reportName: ''
})

function openChunks(report) {
  chunksDrawer.value.reportId = report.id
  chunksDrawer.value.reportName = report.fileName || ('报告 #' + report.id)
  chunksDrawer.value.visible = true
}

function closeChunks() {
  chunksDrawer.value.visible = false
}

function displayStatus(r) {
  // 解析成功但未查重的报告显示为 "待检测"
  if ((r.status === 'PARSED' || r.status === 'PARSED_EMPTY') && !r.hasCheckResult) {
    return 'PENDING_CHECK'
  }
  return r.status
}

function statusClass(s) {
  if (s === 'PARSED') return 'g-badge-success'
  if (s === 'PENDING_CHECK') return 'g-badge-info'
  if (s === 'PARSED_EMPTY') return 'g-badge-warning'
  if (s === 'FAILED') return 'g-badge-danger'
  return 'g-badge-neutral'
}

function statusLabel(s) {
  const map = { PARSED: '已检测', PENDING_CHECK: '待检测', PARSED_EMPTY: '无文本块', FAILED: '解析失败', UPLOADED: '已上传' }
  return map[s] || s
}

async function load() {
  const params = {}
  if (classId.value) params.classId = classId.value
  const res = await getReports(params)
  reports.value = res.reports || []
}

function resetFilters() {
  classId.value = ''
  load()
}

async function loadOptions() {
  const cRes = await getClasses()
  classes.value = cRes.classes || []
  load()
}

function handleDelete(id) {
  deleteModal.value.reportId = id
  deleteModal.value.visible = true
}

function closeDeleteModal() {
  deleteModal.value.visible = false
  deleteModal.value.reportId = null
  deleteModal.value.loading = false
}

async function confirmDelete() {
  if (!deleteModal.value.reportId) return
  
  deleteModal.value.loading = true
  try {
    await deleteReport(deleteModal.value.reportId)
    closeDeleteModal()
    load()
  } catch (err) {
    alert('删除失败: ' + err.message)
    deleteModal.value.loading = false
  }
}

onMounted(loadOptions)
</script>

<style scoped>
.id-col { color: var(--gray-400); font-size: 13px; }
.mono { font-family: 'SF Mono', 'Consolas', monospace; font-size: 13px; color: var(--gray-600); }
.file-col { max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.action-col {
  display: flex;
  align-items: center;
  gap: 8px; /* 间距变小，因为元素有了 padding */
}

.action-link {
  color: var(--primary);
  font-weight: 500;
  font-size: 13px;
  padding: 6px 14px;
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
}

.action-link:hover { 
  color: #fff;
  background: var(--primary); 
}

.action-btn-danger {
  color: var(--danger);
  background: transparent;
  border: none;
  font-size: 13px;
  cursor: pointer;
  padding: 6px 14px;
  font-weight: 500;
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
}

.action-btn-danger:hover { 
  color: #fff;
  background: var(--danger); 
}

.action-btn-info {
  color: var(--primary);
  background: transparent;
  border: none;
  font-size: 13px;
  cursor: pointer;
  padding: 6px 14px;
  font-weight: 500;
  border-radius: var(--radius-full);
  transition: all var(--transition-fast);
}

.action-btn-info:hover {
  color: #fff;
  background: var(--primary);
}
</style>

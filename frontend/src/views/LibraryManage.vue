<template>
  <div class="page">
    <h2 class="g-page-title">指纹底库管理</h2>
    <p class="g-page-desc">已入库的报告将作为历史底库，用于后续查重任务中的「历史库比对」</p>
    <div class="g-card">
      <table class="g-table" v-if="reports.length">
        <thead>
          <tr>
            <th>报告ID</th>
            <th>学生</th>
            <th>学号</th>
            <th>文件名</th>
            <th>操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(r, index) in reports" :key="r.reportId">
            <td class="id-col">{{ index + 1 }}</td>
            <td class="student-col">{{ r.studentName || '-' }}</td>
            <td class="mono">{{ r.studentId || '-' }}</td>
            <td class="file-col">{{ r.fileName }}</td>
            <td>
              <div style="display:flex;gap:8px;align-items:center;">
                <button @click="openChunks(r)" class="g-btn" style="padding:5px 14px;font-size:12px;color:var(--primary);border:1px solid var(--primary-light);">
                  查看分块
                </button>
                <button @click="remove(r.reportId)" class="g-btn g-btn-danger" style="padding: 5px 14px; font-size: 12px;">
                  移出底库
                </button>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
      <div v-else class="g-empty">
        <div class="g-empty-icon">📚</div>
        <div class="g-empty-text">底库暂无报告</div>
        <div style="color: var(--gray-400); font-size: 13px; margin-top: 4px;">
          在查重结果详情页可将报告加入底库
        </div>
      </div>
    </div>
  </div>

  <!-- 分块可视化抽屉 -->
  <ReportChunksDrawer
    :visible="chunksDrawer.visible"
    :report-id="chunksDrawer.reportId"
    :report-name="chunksDrawer.reportName"
    @close="chunksDrawer.visible = false"
  />
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getLibraryReports, removeFromLibrary } from '../api/library'
import ReportChunksDrawer from '../components/ReportChunksDrawer.vue'

const reports = ref([])

const chunksDrawer = ref({
  visible: false,
  reportId: null,
  reportName: ''
})

function openChunks(report) {
  chunksDrawer.value.reportId = report.reportId
  chunksDrawer.value.reportName = report.fileName || ('报告 #' + report.reportId)
  chunksDrawer.value.visible = true
}

async function load() {
  const res = await getLibraryReports()
  reports.value = res.reports || []
}

async function remove(reportId) {
  if (!confirm('确定从底库移除此报告？')) return
  await removeFromLibrary(reportId)
  load()
}

onMounted(load)
</script>

<style scoped>
.id-col { color: var(--gray-400); font-size: 13px; }
.student-col { font-weight: 500; }
.mono { font-family: 'SF Mono', 'Consolas', monospace; font-size: 13px; color: var(--gray-600); }
.file-col { max-width: 280px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
</style>

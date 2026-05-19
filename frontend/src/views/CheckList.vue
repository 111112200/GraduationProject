<template>
  <div class="page">
    <div class="page-header">
      <h2 class="g-page-title">🔍 查重任务</h2>
      <router-link to="/checks/create" class="g-btn g-btn-primary">＋ 新建查重任务</router-link>
    </div>
    <div class="g-card">
      <div v-if="tasks.length" class="task-list">
        <div v-for="t in tasks" :key="t.taskId" class="task-card" @click="go(t.taskId)">
          <div class="task-main">
            <div class="task-name">{{ t.name }}</div>
            <div class="task-meta">
              <span :class="['g-badge', badgeClass(t.status)]">
                {{ statusIcon(t.status) }} {{ statusLabel(t.status) }}
              </span>
              <span class="task-time">{{ formatTime(t.createdAt) }}</span>
            </div>
          </div>
          <button @click.stop="deleteTask(t.taskId)" class="g-btn g-btn-danger btn-del" title="删除任务">🗑 删除</button>
        </div>
      </div>
      <div v-else class="g-empty">
        <div class="g-empty-icon">🔍</div>
        <div class="g-empty-text">暂无查重任务，点击上方按钮创建</div>
      </div>
    </div>

    <!-- 确认删除弹窗 -->
    <div class="g-modal-overlay" v-if="deleteModal.visible" @click.stop="closeDeleteModal">
      <div class="g-modal fade-in-up" @click.stop>
        <div class="g-modal-header">
          <h3 class="g-modal-title">⚠️ 确认删除任务</h3>
        </div>
        <div class="g-modal-body">
          <p>确定要删除这个查重任务吗？删除后相关的所有比对结果也会被彻底清除且不可恢复。</p>
        </div>
        <div class="g-modal-footer">
          <button @click="closeDeleteModal" class="g-btn">取消</button>
          <button @click="confirmDelete" class="g-btn g-btn-danger" :disabled="deleteModal.loading">
            {{ deleteModal.loading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { listChecks, deleteCheckTask } from '../api/checks'

const router = useRouter()
const tasks = ref([])

const deleteModal = ref({
  visible: false,
  taskId: null,
  loading: false
})

function badgeClass(s) {
  return { COMPLETED: 'g-badge-success', RUNNING: 'g-badge-info', PENDING: 'g-badge-warning', FAILED: 'g-badge-danger' }[s] || 'g-badge-neutral'
}
function statusIcon(s) {
  return { COMPLETED: '✅', RUNNING: '⏳', PENDING: '🕐', FAILED: '❌' }[s] || ''
}
function statusLabel(s) {
  return { COMPLETED: '已完成', RUNNING: '执行中', PENDING: '待执行', FAILED: '失败' }[s] || s
}
function formatTime(iso) {
  if (!iso) return ''
  const d = new Date(iso)
  return d.toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function load() {
  const res = await listChecks()
  tasks.value = res.tasks || []
}

function go(id) {
  router.push(`/checks/${id}`)
}

function deleteTask(id) {
  deleteModal.value.taskId = id
  deleteModal.value.visible = true
}

function closeDeleteModal() {
  deleteModal.value.visible = false
  deleteModal.value.taskId = null
  deleteModal.value.loading = false
}

async function confirmDelete() {
  if (!deleteModal.value.taskId) return
  
  deleteModal.value.loading = true
  try {
    await deleteCheckTask(deleteModal.value.taskId)
    closeDeleteModal()
    load()
  } catch (err) {
    alert(err.message || '删除失败')
    deleteModal.value.loading = false
  }
}

onMounted(load)
</script>

<style scoped>
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.task-list { display: flex; flex-direction: column; }
.task-card {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  cursor: pointer;
  transition: all var(--transition-fast);
  border-bottom: 1px solid var(--gray-100);
}
.task-card:last-child { border-bottom: none; }
.task-card:hover { background: var(--primary-bg); }
.task-main { flex: 1; }
.task-name { font-weight: 600; font-size: 15px; color: var(--gray-800); margin-bottom: 6px; }
.task-meta { display: flex; align-items: center; gap: 12px; }
.task-time { font-size: 13px; color: var(--gray-400); }

.btn-del {
  padding: 5px 14px;
  font-size: 12px;
  flex-shrink: 0;
}
</style>

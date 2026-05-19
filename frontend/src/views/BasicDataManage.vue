<template>
  <div class="page">
    <h2 class="g-page-title">🗂️ 基础数据管理</h2>
    <p class="g-page-desc">管理系统中的班级基础数据</p>

    <!-- ===== 班级管理 ===== -->
    <section class="data-section">
      <div class="section-header">
        <h3 class="section-title">📚 班级管理</h3>
        <button class="g-btn g-btn-primary" @click="openClassModal">＋ 新建班级</button>
      </div>
      <div class="g-card">
        <table class="g-table" v-if="classes.length">
          <thead>
            <tr>
              <th>ID</th>
              <th>班级名称</th>
              <th>年级</th>
              <th>报告数量</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in classes" :key="c.id">
              <td class="id-col">{{ c.id }}</td>
              <td>{{ c.name }}</td>
              <td>{{ c.grade || '-' }}</td>
              <td>
                <span class="g-badge" :class="c.reportCount > 0 ? 'g-badge-info' : 'g-badge-neutral'">
                  {{ c.reportCount }} 份
                </span>
              </td>
              <td>
                <button class="action-btn-danger" @click="handleDeleteClass(c)">删除</button>
              </td>
            </tr>
          </tbody>
        </table>
        <div v-else class="g-empty">
          <div class="g-empty-icon">📚</div>
          <div class="g-empty-text">暂无班级数据，请点击右上角新建班级</div>
        </div>
      </div>
    </section>

  </div>

  <!-- ===== 新建班级弹窗 ===== -->
  <Teleport to="body">
    <div class="g-modal-overlay" v-if="classModal.visible">
      <div class="g-modal fade-in-up">
        <div class="g-modal-header">
          <h3 class="g-modal-title">📚 新建班级</h3>
        </div>
        <div class="g-modal-body">
          <div class="form-row">
            <label>班级名称 <span class="required">*</span></label>
            <input v-model="classModal.name" class="g-input full-width" placeholder="例如：计科2301" />
          </div>
          <div class="form-row">
            <label>年级</label>
            <input v-model="classModal.grade" class="g-input full-width" placeholder="例如：2023（选填）" />
          </div>
          <p v-if="classModal.error" class="g-msg-error">{{ classModal.error }}</p>
        </div>
        <div class="g-modal-footer">
          <button class="g-btn" @click="closeClassModal">取消</button>
          <button class="g-btn g-btn-primary" @click="submitClass" :disabled="classModal.loading">
            {{ classModal.loading ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <!-- ===== 删除确认弹窗 ===== -->
  <Teleport to="body">
    <div class="g-modal-overlay" v-if="deleteModal.visible">
      <div class="g-modal fade-in-up">
        <div class="g-modal-header">
          <h3 class="g-modal-title">⚠️ 确认删除</h3>
        </div>
        <div class="g-modal-body">
          <p>确定要删除 <strong>{{ deleteModal.label }}</strong> 吗？此操作不可撤销。</p>
        </div>
        <div class="g-modal-footer">
          <button class="g-btn" @click="closeDeleteModal">取消</button>
          <button class="g-btn g-btn-danger" @click="confirmDelete" :disabled="deleteModal.loading">
            {{ deleteModal.loading ? '删除中...' : '确认删除' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getClasses, createClass, deleteClass } from '../api/course'

const classes = ref([])

// ===== 班级弹窗 =====
const classModal = ref({
  visible: false,
  name: '',
  grade: '',
  loading: false,
  error: ''
})

function openClassModal() {
  classModal.value = { visible: true, name: '', grade: '', loading: false, error: '' }
}
function closeClassModal() {
  classModal.value.visible = false
}
async function submitClass() {
  if (!classModal.value.name.trim()) {
    classModal.value.error = '请输入班级名称'
    return
  }
  classModal.value.loading = true
  classModal.value.error = ''
  try {
    await createClass(classModal.value.name.trim(), classModal.value.grade.trim())
    closeClassModal()
    await loadClasses()
  } catch (e) {
    classModal.value.error = '创建失败: ' + (e.message || e)
  } finally {
    classModal.value.loading = false
  }
}

// ===== 删除 =====
const deleteModal = ref({
  visible: false,
  id: null,
  label: '',
  loading: false
})

function handleDeleteClass(c) {
  deleteModal.value = { visible: true, id: c.id, label: `班级「${c.name}」`, loading: false }
}
function closeDeleteModal() {
  deleteModal.value.visible = false
}
async function confirmDelete() {
  deleteModal.value.loading = true
  try {
    await deleteClass(deleteModal.value.id)
    await loadClasses()
    closeDeleteModal()
  } catch (e) {
    alert('删除失败: ' + (e.message || e))
    deleteModal.value.loading = false
  }
}

// ===== 数据加载 =====
async function loadClasses() {
  const res = await getClasses()
  classes.value = res.classes || []
}

onMounted(loadClasses)
</script>

<style scoped>
.data-section {
  margin-bottom: 32px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 14px;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.id-col {
  color: var(--gray-400);
  font-size: 13px;
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

.form-row {
  margin-bottom: 18px;
}

.form-row label {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
  font-size: 14px;
  color: var(--gray-700);
}

.required {
  color: var(--danger);
}

.full-width {
  width: 100%;
}
</style>

<template>
  <div class="page">
    <h2 class="g-page-title">📤 上传实验报告</h2>
    <p class="g-page-desc">支持 .docx 格式，可一次选择多个文件批量上传</p>
    <div class="g-card g-card-body">
      <div class="form-row">
        <label>班级</label>
        <div class="class-select-row">
          <select v-model="classId" class="g-select">
            <option v-for="c in classes" :key="c.id" :value="c.id">{{ c.name }}</option>
          </select>
          <button class="g-btn g-btn-primary" @click="openClassModal">＋ 添加班级</button>
        </div>
      </div>
      <div class="form-row">
        <label>关联实验 <span class="optional">（选填）</span></label>
        <select v-model="experimentId" class="g-select">
          <option :value="null">不关联实验</option>
          <option v-for="experiment in experiments" :key="experiment.id" :value="experiment.id">
            {{ experiment.title }}
          </option>
        </select>
      </div>
      <div class="form-row">
        <label>选择文件</label>
        <div
          class="drop-zone"
          :class="{ 'drag-over': isDragging }"
          @dragover.prevent="isDragging = true"
          @dragleave="isDragging = false"
          @drop.prevent="onDrop"
          @click="$refs.fileInput.click()"
        >
          <div class="drop-icon">📁</div>
          <div class="drop-text" v-if="!fileList.length">
            点击选择文件 或 拖拽文件到此处
          </div>
          <div class="drop-text" v-else>
            已选择 <strong>{{ fileList.length }}</strong> 个文件
          </div>
          <div class="drop-hint">仅支持 .docx 格式</div>
        </div>
        <input type="file" multiple accept=".docx" @change="onFileChange" ref="fileInput" class="hidden-input" />
      </div>

      <div v-if="fileList.length" class="file-preview">
        <div v-for="(f, i) in fileList" :key="i" class="file-item">
          <span class="file-icon">📄</span>
          <span class="file-name">{{ f.name }}</span>
          <span class="file-size">{{ formatSize(f.size) }}</span>
          <button class="file-remove" @click="removeFile(i)">✕</button>
        </div>
      </div>

      <button @click="upload" :disabled="uploading" class="g-btn g-btn-primary upload-btn">
        {{ uploading ? '上传中...' : '开始上传' }}
      </button>
      <p v-if="msg" :class="msgClass">{{ msg }}</p>
    </div>
  </div>

  <!-- ===== 新建班级弹窗 ===== -->
  <Teleport to="body">
    <div class="g-modal-overlay" v-if="classModal.visible">
      <div class="g-modal fade-in-up">
        <div class="g-modal-header">
          <h3 class="g-modal-title">📚 添加班级</h3>
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
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { getClasses, getExperiments, createClass } from '../api/course'
import { uploadReports } from '../api/reports'

const classes = ref([])
const classId = ref(null)
const experiments = ref([])
const experimentId = ref(null)
const fileList = ref([])
const fileInput = ref(null)
const uploading = ref(false)
const isDragging = ref(false)
const msg = ref('')

const msgClass = ref('')

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
    const res = await createClass(classModal.value.name.trim(), classModal.value.grade.trim())
    closeClassModal()
    await loadOptions()
    classId.value = res.id
  } catch (e) {
    classModal.value.error = '创建失败: ' + (e.message || e)
  } finally {
    classModal.value.loading = false
  }
}

function onFileChange(e) {
  const files = Array.from(e.target.files || [])
  fileList.value = [...fileList.value, ...files]
}

function onDrop(e) {
  isDragging.value = false
  const files = Array.from(e.dataTransfer.files).filter(f => f.name.endsWith('.docx'))
  fileList.value = [...fileList.value, ...files]
}

function removeFile(index) {
  fileList.value.splice(index, 1)
}

function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function loadOptions() {
  const [classResult, experimentResult] = await Promise.all([getClasses(), getExperiments()])
  classes.value = classResult.classes || []
  experiments.value = experimentResult.experiments || []
  if (classes.value.length && !classId.value) classId.value = classes.value[0].id
}

async function upload() {
  if (!fileList.value.length || !classId.value) {
    msg.value = '请选择班级和至少一个文件'
    msgClass.value = 'g-msg-error'
    return
  }
  uploading.value = true
  msg.value = ''
  try {
    const res = await uploadReports(fileList.value, experimentId.value, classId.value)
    const ok = res.uploadedReports?.length || 0
    const err = res.errors?.length || 0
    msg.value = `上传成功 ${ok} 份${err ? `，失败 ${err} 份` : ''}`
    msgClass.value = err ? 'g-msg-warning' : 'g-msg-success'
    fileList.value = []
    if (fileInput.value) fileInput.value.value = ''
  } catch (e) {
    msg.value = '上传失败: ' + (e.message || e)
    msgClass.value = 'g-msg-error'
  } finally {
    uploading.value = false
  }
}

onMounted(loadOptions)
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

.drop-zone {
  border: 2px dashed var(--gray-300);
  border-radius: var(--radius-md);
  padding: 36px 24px;
  text-align: center;
  cursor: pointer;
  transition: all var(--transition-base);
  background: var(--gray-50);
}
.drop-zone:hover, .drop-zone.drag-over {
  border-color: var(--primary);
  background: var(--primary-bg);
}

.class-select-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.flex-1 {
  flex: 1;
}

.full-width {
  width: 100%;
}

.required {
  color: var(--danger);
}
.optional { color: var(--gray-400); font-size: 12px; font-weight: 400; }
.drop-icon { font-size: 36px; margin-bottom: 8px; }
.drop-text { font-size: 15px; color: var(--gray-600); }
.drop-text strong { color: var(--primary); }
.drop-hint { font-size: 12px; color: var(--gray-400); margin-top: 6px; }

.hidden-input { display: none; }

.file-preview {
  margin: 16px 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  background: var(--gray-50);
  border-radius: var(--radius-sm);
  font-size: 13px;
}
.file-icon { font-size: 16px; }
.file-name { flex: 1; color: var(--gray-700); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.file-size { color: var(--gray-400); font-size: 12px; }
.file-remove {
  background: none;
  border: none;
  color: var(--gray-400);
  cursor: pointer;
  font-size: 14px;
  padding: 2px 6px;
  border-radius: 4px;
  transition: all var(--transition-fast);
}
.file-remove:hover { color: var(--danger); background: var(--danger-bg); }

.upload-btn { margin-top: 8px; }
</style>

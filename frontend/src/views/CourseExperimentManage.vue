<template>
  <div class="page">
    <h2 class="g-page-title">📘 课程与实验管理</h2>
    <p class="g-page-desc">先创建课程，再为课程配置实验；查重任务和报告可关联到对应实验。</p>

    <section class="data-section">
      <div class="section-header">
        <h3 class="section-title">📘 课程</h3>
        <button class="g-btn g-btn-primary" @click="openCourseModal">＋ 新建课程</button>
      </div>
      <div class="g-card">
        <table v-if="courses.length" class="g-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>课程名称</th>
              <th>课程代码</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="course in courses" :key="course.id">
              <td class="id-col">{{ course.id }}</td>
              <td>{{ course.name }}</td>
              <td>{{ course.code || '-' }}</td>
              <td><button class="action-btn-danger" @click="removeCourse(course)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="g-empty">
          <div class="g-empty-icon">📘</div>
          <div class="g-empty-text">暂无课程，请先创建课程。</div>
        </div>
      </div>
    </section>

    <section class="data-section">
      <div class="section-header">
        <h3 class="section-title">🧪 实验</h3>
        <button class="g-btn g-btn-primary" :disabled="!courses.length" @click="openExperimentModal">＋ 新建实验</button>
      </div>
      <p v-if="!courses.length" class="section-hint">请先创建至少一门课程，才能新建实验。</p>
      <div class="g-card">
        <table v-if="experiments.length" class="g-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>所属课程</th>
              <th>实验名称</th>
              <th>说明</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="experiment in experiments" :key="experiment.id">
              <td class="id-col">{{ experiment.id }}</td>
              <td>{{ courseName(experiment.courseId) }}</td>
              <td>{{ experiment.title }}</td>
              <td class="description-col">{{ experiment.description || '-' }}</td>
              <td><button class="action-btn-danger" @click="removeExperiment(experiment)">删除</button></td>
            </tr>
          </tbody>
        </table>
        <div v-else class="g-empty">
          <div class="g-empty-icon">🧪</div>
          <div class="g-empty-text">暂无实验，请为课程添加实验。</div>
        </div>
      </div>
    </section>
  </div>

  <Teleport to="body">
    <div v-if="courseModal.visible" class="g-modal-overlay">
      <div class="g-modal fade-in-up">
        <div class="g-modal-header"><h3 class="g-modal-title">新建课程</h3></div>
        <div class="g-modal-body">
          <div class="form-row">
            <label>课程名称 <span class="required">*</span></label>
            <input v-model="courseModal.name" class="g-input full-width" placeholder="例如：软件工程" />
          </div>
          <div class="form-row">
            <label>课程代码</label>
            <input v-model="courseModal.code" class="g-input full-width" placeholder="例如：SE001（选填）" />
          </div>
          <p v-if="courseModal.error" class="g-msg-error">{{ courseModal.error }}</p>
        </div>
        <div class="g-modal-footer">
          <button class="g-btn" @click="courseModal.visible = false">取消</button>
          <button class="g-btn g-btn-primary" :disabled="courseModal.loading" @click="submitCourse">
            {{ courseModal.loading ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>

  <Teleport to="body">
    <div v-if="experimentModal.visible" class="g-modal-overlay">
      <div class="g-modal fade-in-up">
        <div class="g-modal-header"><h3 class="g-modal-title">新建实验</h3></div>
        <div class="g-modal-body">
          <div class="form-row">
            <label>所属课程 <span class="required">*</span></label>
            <select v-model="experimentModal.courseId" class="g-select full-width">
              <option v-for="course in courses" :key="course.id" :value="course.id">{{ course.name }}</option>
            </select>
          </div>
          <div class="form-row">
            <label>实验名称 <span class="required">*</span></label>
            <input v-model="experimentModal.title" class="g-input full-width" placeholder="例如：实验一：需求分析" />
          </div>
          <div class="form-row">
            <label>实验说明</label>
            <textarea v-model="experimentModal.description" class="g-input full-width" rows="3" placeholder="选填"></textarea>
          </div>
          <p v-if="experimentModal.error" class="g-msg-error">{{ experimentModal.error }}</p>
        </div>
        <div class="g-modal-footer">
          <button class="g-btn" @click="experimentModal.visible = false">取消</button>
          <button class="g-btn g-btn-primary" :disabled="experimentModal.loading" @click="submitExperiment">
            {{ experimentModal.loading ? '创建中...' : '确认创建' }}
          </button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import {
  createCourse,
  createExperiment,
  deleteCourse,
  deleteExperiment,
  getCourses,
  getExperiments,
} from '../api/course'

const courses = ref([])
const experiments = ref([])
const courseModal = ref({ visible: false, name: '', code: '', loading: false, error: '' })
const experimentModal = ref({ visible: false, courseId: null, title: '', description: '', loading: false, error: '' })

const courseNames = computed(() => Object.fromEntries(courses.value.map(course => [course.id, course.name])))

function courseName(courseId) {
  return courseNames.value[courseId] || '-'
}

async function loadData() {
  const [courseResult, experimentResult] = await Promise.all([getCourses(), getExperiments()])
  courses.value = courseResult.courses || []
  experiments.value = experimentResult.experiments || []
}

function openCourseModal() {
  courseModal.value = { visible: true, name: '', code: '', loading: false, error: '' }
}

function openExperimentModal() {
  experimentModal.value = {
    visible: true,
    courseId: courses.value[0]?.id || null,
    title: '',
    description: '',
    loading: false,
    error: '',
  }
}

async function submitCourse() {
  if (!courseModal.value.name.trim()) {
    courseModal.value.error = '请输入课程名称'
    return
  }
  courseModal.value.loading = true
  courseModal.value.error = ''
  try {
    await createCourse(courseModal.value.name.trim(), courseModal.value.code.trim())
    courseModal.value.visible = false
    await loadData()
  } catch (error) {
    courseModal.value.error = '创建失败：' + (error.message || error)
  } finally {
    courseModal.value.loading = false
  }
}

async function submitExperiment() {
  if (!experimentModal.value.courseId || !experimentModal.value.title.trim()) {
    experimentModal.value.error = '请选择课程并输入实验名称'
    return
  }
  experimentModal.value.loading = true
  experimentModal.value.error = ''
  try {
    await createExperiment(
      experimentModal.value.courseId,
      experimentModal.value.title.trim(),
      experimentModal.value.description.trim(),
    )
    experimentModal.value.visible = false
    await loadData()
  } catch (error) {
    experimentModal.value.error = '创建失败：' + (error.message || error)
  } finally {
    experimentModal.value.loading = false
  }
}

async function removeCourse(course) {
  if (!confirm(`确定删除课程“${course.name}”吗？没有实验时才允许删除。`)) return
  try {
    await deleteCourse(course.id)
    await loadData()
  } catch (error) {
    alert('删除失败：' + (error.message || error))
  }
}

async function removeExperiment(experiment) {
  if (!confirm(`确定删除实验“${experiment.title}”吗？有关联报告或查重任务时不允许删除。`)) return
  try {
    await deleteExperiment(experiment.id)
    await loadData()
  } catch (error) {
    alert('删除失败：' + (error.message || error))
  }
}

onMounted(loadData)
</script>

<style scoped>
.data-section { margin-bottom: 32px; }
.section-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.section-title { margin: 0; font-size: 17px; font-weight: 600; color: var(--gray-800); }
.section-hint { margin: -6px 0 12px; color: var(--gray-400); font-size: 13px; }
.id-col { color: var(--gray-400); font-size: 13px; }
.description-col { max-width: 420px; white-space: normal; }
.action-btn-danger {
  border: none; border-radius: var(--radius-full); background: transparent; color: var(--danger);
  cursor: pointer; font-size: 13px; font-weight: 500; padding: 6px 14px;
}
.action-btn-danger:hover { background: var(--danger); color: #fff; }
.form-row { margin-bottom: 18px; }
.form-row label { display: block; margin-bottom: 6px; color: var(--gray-700); font-size: 14px; font-weight: 600; }
.required { color: var(--danger); }
.full-width { box-sizing: border-box; width: 100%; }
textarea.g-input { resize: vertical; }
</style>

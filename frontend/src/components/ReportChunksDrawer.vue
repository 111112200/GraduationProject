<template>
  <Teleport to="body">
    <!-- 遮罩层 -->
    <div class="drawer-overlay" v-if="visible" @click.self="close">
      <!-- 抽屉主体 -->
    <div class="drawer fade-in-right">
      <!-- 抽屉头部 -->
      <div class="drawer-header">
        <div class="drawer-title-wrap">
          <span class="drawer-icon">🔬</span>
          <div>
            <h3 class="drawer-title">向量分块详情</h3>
            <p class="drawer-subtitle" v-if="reportName">{{ reportName }}</p>
          </div>
        </div>
        <button class="drawer-close" @click="close" title="关闭">✕</button>
      </div>

      <!-- 可滚动的抽屉主体内容区 -->
      <div class="drawer-body">
        <!-- 加载中 -->
        <div class="drawer-loading" v-if="loading">
          <div class="spinner"></div>
          <p>正在计算分块…</p>
        </div>

      <!-- 错误 -->
      <div class="drawer-error" v-else-if="error">
        <span class="error-icon">⚠️</span>
        <p>{{ error }}</p>
        <button class="g-btn g-btn-primary" style="margin-top:12px" @click="load">重试</button>
      </div>

      <!-- 内容 -->
      <template v-else-if="data">
        <!-- 统计摘要卡片 -->
        <div class="summary-bar">
          <div class="stat-card">
            <div class="stat-value">{{ data.summary.total_chunks }}</div>
            <div class="stat-label">切块总数</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ data.summary.total_text_length }}</div>
            <div class="stat-label">原文总字符</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ data.summary.chunk_size }}</div>
            <div class="stat-label">Chunk Size</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ data.summary.chunk_overlap }}</div>
            <div class="stat-label">Chunk Overlap</div>
          </div>
          <div class="stat-card">
            <div class="stat-value">{{ data.summary.block_count }}</div>
            <div class="stat-label">原始段落数</div>
          </div>
        </div>

        <!-- 图例说明 -->
        <div class="legend-bar">
          <span class="legend-item">
            <span class="legend-dot legend-prev"></span>与前块重叠
          </span>
          <span class="legend-item">
            <span class="legend-dot legend-body"></span>独立内容
          </span>
          <span class="legend-item">
            <span class="legend-dot legend-next"></span>与后块重叠
          </span>
        </div>

        <!-- 空状态 -->
        <div class="drawer-empty" v-if="data.chunks.length === 0">
          <div class="g-empty-icon">📭</div>
          <div class="g-empty-text">该报告暂无可展示的分块内容（文本块为空或内容过短）</div>
        </div>

        <!-- 分块列表 -->
        <div class="chunks-list" v-else>
          <div
            v-for="chunk in data.chunks"
            :key="chunk.index"
            class="chunk-card"
          >
            <!-- 卡片头部 -->
            <div class="chunk-header">
              <div class="chunk-meta-left">
                <span class="chunk-index">#{{ chunk.index }}</span>
                <span class="chunk-section" v-if="chunk.section_type">{{ sectionLabel(chunk.section_type) }}</span>
              </div>
              <div class="chunk-meta-right">
                <span class="chunk-length-badge">{{ chunk.length }} 字符</span>
                <button
                  class="chunk-expand-btn"
                  @click="toggleExpand(chunk.index)"
                  v-if="chunk.content.length > 200"
                >
                  {{ collapsedSet.has(chunk.index) ? '展开全文' : '收起' }}
                </button>
              </div>
            </div>

            <!-- 分块文本（高亮着色） -->
            <div class="chunk-content" v-html="renderChunk(chunk, !collapsedSet.has(chunk.index))"></div>

            <!-- 重叠标注信息 -->
            <div class="chunk-overlap-info" v-if="chunk.overlap_prev || chunk.overlap_next">
              <span v-if="chunk.overlap_prev" class="overlap-tag overlap-tag-prev">
                ↑ 与前块重叠 {{ chunk.overlap_prev.length }} 字符
              </span>
              <span v-if="chunk.overlap_next" class="overlap-tag overlap-tag-next">
                ↓ 与后块重叠 {{ chunk.overlap_next.length }} 字符
              </span>
            </div>
          </div>
        </div>
      </template>
      </div>
    </div>
  </div>
  </Teleport>
</template>

<script setup>
import { ref, watch } from 'vue'
import { getReportChunks } from '../api/reports'

const props = defineProps({
  visible: Boolean,
  reportId: Number,
  reportName: String,
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref('')
const data = ref(null)
const collapsedSet = ref(new Set())

watch(
  () => props.visible,
  (val) => {
    if (val && props.reportId) {
      load()
    } else {
      // 关闭时重置
      data.value = null
      error.value = ''
      collapsedSet.value = new Set()
    }
  }
)

async function load() {
  loading.value = true
  error.value = ''
  data.value = null
  try {
    data.value = await getReportChunks(props.reportId)
  } catch (e) {
    error.value = '加载分块数据失败：' + (e.message || '未知错误')
  } finally {
    loading.value = false
  }
}

function close() {
  emit('close')
}

function toggleExpand(index) {
  const s = new Set(collapsedSet.value)
  if (s.has(index)) s.delete(index)
  else s.add(index)
  collapsedSet.value = s
}

function sectionLabel(type) {
  const map = {
    DESIGN_IDEA: '设计思路',
    REFLECTION: '心得体会',
    CONCLUSION: '实验总结',
    OTHER: '其他',
  }
  return map[type] || type
}

/**
 * 将 chunk 的 content 渲染为带颜色的 HTML：
 *  - 头部 overlap_prev 部分 → 蓝色背景
 *  - 尾部 overlap_next 部分 → 黄色背景
 *  - 中间独立内容 → 普通文本
 * 截断逻辑：非展开状态最多显示 200 字符
 */
function renderChunk(chunk, expanded) {
  const { content, overlap_prev, overlap_next } = chunk
  const escape = (s) =>
    s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/\n/g, '<br/>')

  // 确定展示窗口
  const displayText = expanded || content.length <= 200 ? content : content.slice(0, 200) + '…'

  // 三段拆分
  let head = ''
  let tail = ''
  let body = displayText

  // 头部重叠：displayText 以 overlap_prev 开头才标注
  if (overlap_prev && displayText.startsWith(overlap_prev)) {
    head = displayText.slice(0, overlap_prev.length)
    body = displayText.slice(overlap_prev.length)
  }

  // 尾部重叠：body 以 overlap_next 结尾才标注（仅在全展开时才显示完整尾部重叠）
  if (overlap_next && body.endsWith(overlap_next)) {
    tail = body.slice(body.length - overlap_next.length)
    body = body.slice(0, body.length - overlap_next.length)
  }

  let html = ''
  if (head) html += `<mark class="hl-prev">${escape(head)}</mark>`
  if (body) html += `<span class="hl-body">${escape(body)}</span>`
  if (tail) html += `<mark class="hl-next">${escape(tail)}</mark>`
  return html
}
</script>

<style scoped>
/* ===== 抽屉遮罩 ===== */
.drawer-overlay {
  position: fixed;
  inset: 0;
  background: rgba(15, 23, 42, 0.35);
  backdrop-filter: blur(3px);
  z-index: 9999;
  display: flex;
  justify-content: flex-end;
}

/* ===== 抽屉主体 ===== */
.drawer {
  width: min(680px, 96vw);
  height: 100%;
  max-height: 100%;
  background: #fff;
  display: flex;
  flex-direction: column;
  box-shadow: -8px 0 40px rgba(0, 0, 0, 0.12);
  overflow: hidden;
}

@keyframes slideInRight {
  from { transform: translateX(100%); opacity: 0; }
  to   { transform: translateX(0);    opacity: 1; }
}

.fade-in-right {
  animation: slideInRight 0.28s cubic-bezier(0.22, 1, 0.36, 1) both;
}

/* ===== 头部 ===== */
.drawer-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px 24px;
  border-bottom: 1px solid var(--gray-100);
  flex-shrink: 0;
  background: linear-gradient(135deg, #f0f7ff 0%, #fff 100%);
}

.drawer-title-wrap {
  display: flex;
  align-items: center;
  gap: 12px;
}

.drawer-icon {
  font-size: 28px;
  line-height: 1;
}

.drawer-title {
  font-size: 18px;
  font-weight: 700;
  color: var(--gray-900);
  margin: 0;
}

.drawer-subtitle {
  font-size: 13px;
  color: var(--gray-400);
  margin: 2px 0 0;
  max-width: 380px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.drawer-close {
  width: 32px;
  height: 32px;
  border: none;
  background: var(--gray-100);
  color: var(--gray-500);
  border-radius: 50%;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.15s;
  flex-shrink: 0;
}

.drawer-close:hover {
  background: var(--gray-200);
  color: var(--gray-800);
}

/* ===== 抽屉内容区 (挂载滚动条) ===== */
.drawer-body {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
}

.drawer-body::-webkit-scrollbar {
  width: 8px;
}

.drawer-body::-webkit-scrollbar-track {
  background: transparent;
}

.drawer-body::-webkit-scrollbar-thumb {
  background: var(--gray-300);
  border-radius: 4px;
}

.drawer-body::-webkit-scrollbar-thumb:hover {
  background: var(--gray-400);
}

/* ===== 加载/错误 ===== */
.drawer-loading,
.drawer-error {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  gap: 12px;
  color: var(--gray-400);
  font-size: 15px;
}

.error-icon {
  font-size: 36px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid var(--gray-200);
  border-top-color: var(--primary);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* ===== 统计摘要栏 ===== */
.summary-bar {
  display: flex;
  gap: 0;
  border-bottom: 1px solid var(--gray-100);
  flex-shrink: 0;
  background: var(--gray-50);
}

.stat-card {
  flex: 1;
  padding: 14px 8px;
  text-align: center;
  border-right: 1px solid var(--gray-100);
}

.stat-card:last-child {
  border-right: none;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
  color: var(--primary);
  line-height: 1.2;
}

.stat-label {
  font-size: 11px;
  color: var(--gray-400);
  margin-top: 3px;
  letter-spacing: 0.03em;
}

/* ===== 图例 ===== */
.legend-bar {
  display: flex;
  gap: 20px;
  padding: 10px 20px;
  background: #fff;
  border-bottom: 1px solid var(--gray-100);
  flex-shrink: 0;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: var(--gray-500);
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 3px;
}

.legend-prev { background: #bfdbfe; }
.legend-body { background: var(--gray-100); }
.legend-next { background: #fef08a; }

/* ===== 空状态 ===== */
.drawer-empty {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--gray-400);
}

/* ===== 分块列表 ===== */
.chunks-list {
  padding: 16px 20px;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

/* ===== 单个分块卡片 ===== */
.chunk-card {
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-md);
  overflow: hidden;
  transition: box-shadow 0.2s;
}

.chunk-card:hover {
  box-shadow: var(--shadow-md);
  border-color: var(--primary-light);
}

.chunk-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: var(--gray-50);
  border-bottom: 1px solid var(--gray-100);
}

.chunk-meta-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chunk-meta-right {
  display: flex;
  align-items: center;
  gap: 8px;
}

.chunk-index {
  font-size: 13px;
  font-weight: 700;
  color: var(--primary);
  font-family: 'SF Mono', 'Consolas', monospace;
}

.chunk-section {
  font-size: 11px;
  padding: 2px 8px;
  background: var(--primary-bg);
  color: var(--primary-dark);
  border-radius: var(--radius-full);
  font-weight: 500;
}

.chunk-length-badge {
  font-size: 12px;
  color: var(--gray-400);
  font-family: 'SF Mono', 'Consolas', monospace;
}

.chunk-expand-btn {
  font-size: 12px;
  color: var(--primary);
  background: none;
  border: 1px solid var(--primary-light);
  border-radius: var(--radius-full);
  padding: 2px 10px;
  cursor: pointer;
  transition: all 0.15s;
}

.chunk-expand-btn:hover {
  background: var(--primary);
  color: #fff;
}

/* ===== 分块内容区 ===== */
.chunk-content {
  padding: 12px 14px;
  font-size: 14px;
  line-height: 1.8;
  color: var(--gray-700);
  word-break: break-all;
}

/* ===== 高亮 mark 样式 ===== */
.chunk-content :deep(.hl-prev) {
  background: #bfdbfe;
  color: #1e40af;
  border-radius: 2px;
  padding: 0 1px;
}

.chunk-content :deep(.hl-body) {
  color: var(--gray-700);
}

.chunk-content :deep(.hl-next) {
  background: #fef08a;
  color: #713f12;
  border-radius: 2px;
  padding: 0 1px;
}

/* ===== 重叠信息标签 ===== */
.chunk-overlap-info {
  display: flex;
  gap: 8px;
  padding: 8px 14px;
  background: var(--gray-50);
  border-top: 1px solid var(--gray-100);
  flex-wrap: wrap;
}

.overlap-tag {
  font-size: 11px;
  padding: 2px 10px;
  border-radius: var(--radius-full);
  font-weight: 500;
}

.overlap-tag-prev {
  background: #dbeafe;
  color: #1d4ed8;
}

.overlap-tag-next {
  background: #fef9c3;
  color: #854d0e;
}
</style>

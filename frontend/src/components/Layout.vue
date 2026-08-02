<template>
  <div class="layout">
    <!-- 左侧侧边栏 -->
    <aside class="sidebar">
      <div class="sidebar-brand">
        <span class="sidebar-logo">📄</span>
        <span class="sidebar-title">语义查重系统</span>
      </div>
      <nav class="sidebar-nav">
        <router-link to="/dashboard" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">🏠</span>
          <span class="sidebar-text">首页</span>
        </router-link>
        <router-link to="/reports/upload" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">📤</span>
          <span class="sidebar-text">上传报告</span>
        </router-link>
        <router-link to="/reports" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">📋</span>
          <span class="sidebar-text">报告管理</span>
        </router-link>
        <router-link to="/checks" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">🔍</span>
          <span class="sidebar-text">查重任务</span>
        </router-link>
        <router-link to="/library" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">📚</span>
          <span class="sidebar-text">底库管理</span>
        </router-link>
        <router-link to="/course-experiments" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">📘</span>
          <span class="sidebar-text">课程与实验</span>
        </router-link>
        <router-link to="/basic-data" class="sidebar-link" active-class="active">
          <span class="sidebar-icon">🗂️</span>
          <span class="sidebar-text">班级管理</span>
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <span class="sidebar-version">v1.2.5</span>
      </div>
    </aside>

    <!-- 右侧区域 -->
    <div class="layout-right">
      <!-- 顶部栏 -->
      <header class="topbar">
        <div class="topbar-left">
          <h2 class="topbar-title">{{ pageTitle }}</h2>
        </div>
        <div class="topbar-right">
          <span class="topbar-time">{{ currentTime }}</span>
          <div class="user-profile" @mouseenter="showDropdown = true" @mouseleave="hideDropdown">
            <div class="topbar-avatar">👤</div>
            <span class="username">{{ currentUsername }}</span>
            <!-- 下拉菜单 -->
            <div v-show="showDropdown" class="dropdown-menu" @mouseenter="cancelHideDropdown" @mouseleave="hideDropdown">
              <div class="dropdown-item" @click="onChangePassword">
                <span class="dropdown-icon">🔐</span>
                <span>修改密码</span>
              </div>
              <div class="dropdown-divider"></div>
              <div class="dropdown-item dropdown-item-danger" @click="handleLogout">
                <span class="dropdown-icon">🚪</span>
                <span>退出账户</span>
              </div>
            </div>
          </div>
        </div>
      </header>

      <!-- 主内容区 -->
      <main class="main-content fade-in-up">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup>
import { computed, ref, onMounted, onUnmounted } from 'vue'
import { useRoute } from 'vue-router'
import { logout } from '../api/auth'

const route = useRoute()

const pageTitleMap = {
  'dashboard': '首页',
  'reports': '报告管理',
  'report-upload': '上传报告',
  'report-result': '查重结果',
  'checks': '查重任务',
  'check-create': '新建查重',
  'check-detail': '任务详情',
  'library': '底库管理',
  'course-experiments': '课程与实验管理',
  'basic-data': '班级管理',
}

const pageTitle = computed(() => pageTitleMap[route.name] || '首页')

const currentTime = ref('')
const currentUsername = ref(localStorage.getItem('username') || '用户')
const showDropdown = ref(false)
let timer = null
let dropdownTimer = null

function updateTime() {
  const now = new Date()
  currentTime.value = now.toLocaleString('zh-CN', {
    month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit',
    weekday: 'short',
  })
}

function handleLogout() {
  if (confirm('确定要退出登录吗？')) {
    logout()
  }
}

function onChangePassword() {
  // 预留：修改密码功能
  alert('修改密码功能暂未实现')
}

function hideDropdown() {
  dropdownTimer = setTimeout(() => {
    showDropdown.value = false
  }, 300)
}

function cancelHideDropdown() {
  if (dropdownTimer) {
    clearTimeout(dropdownTimer)
    dropdownTimer = null
  }
}

onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 10000)
})
onUnmounted(() => {
  clearInterval(timer)
  if (dropdownTimer) {
    clearTimeout(dropdownTimer)
  }
})
</script>

<style scoped>
.layout {
  display: flex;
  min-height: 100vh;
  background: var(--gray-100);
}

/* ===== 侧边栏 ===== */
.sidebar {
  width: var(--sidebar-width);
  background: #fff;
  border-right: 1px solid var(--gray-200);
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 200;
  transition: width var(--transition-base);
}

.sidebar-brand {
  height: var(--header-height);
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 20px;
  border-bottom: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.sidebar-logo {
  font-size: 22px;
}

.sidebar-title {
  font-size: 16px;
  font-weight: 700;
  color: var(--gray-800);
  white-space: nowrap;
}

.sidebar-nav {
  flex: 1;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
  overflow-y: auto;
}

.sidebar-link {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 11px 16px;
  border-radius: var(--radius-sm);
  color: var(--gray-500);
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  transition: all var(--transition-fast);
  white-space: nowrap;
}

.sidebar-link:hover {
  color: var(--primary);
  background: var(--primary-bg);
}

.sidebar-link.active {
  color: var(--primary);
  background: var(--primary-bg);
  font-weight: 600;
}

.sidebar-link.active .sidebar-icon {
  transform: scale(1.1);
}

.sidebar-icon {
  font-size: 17px;
  width: 24px;
  text-align: center;
  flex-shrink: 0;
  transition: transform var(--transition-fast);
}

.sidebar-text {
  flex: 1;
}

.sidebar-footer {
  padding: 14px 20px;
  border-top: 1px solid var(--gray-200);
  flex-shrink: 0;
}

.sidebar-version {
  font-size: 12px;
  color: var(--gray-400);
}

/* ===== 右侧区域 ===== */
.layout-right {
  flex: 1;
  margin-left: var(--sidebar-width);
  display: flex;
  flex-direction: column;
  min-height: 100vh;
}

/* ===== 顶部栏 ===== */
.topbar {
  height: var(--header-height);
  background: #fff;
  border-bottom: 1px solid var(--gray-200);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 28px;
  position: sticky;
  top: 0;
  z-index: 100;
  flex-shrink: 0;
}

.topbar-left {
  display: flex;
  align-items: center;
}

.topbar-title {
  font-size: 16px;
  font-weight: 600;
  color: var(--gray-800);
  margin: 0;
}

.topbar-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.topbar-time {
  font-size: 13px;
  color: var(--gray-400);
}

.topbar-avatar {
  width: 34px;
  height: 34px;
  border-radius: 50%;
  background: var(--primary-bg);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 16px;
  cursor: pointer;
  transition: box-shadow var(--transition-fast);
}

.topbar-avatar:hover {
  box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.15);
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 16px;
  border-left: 1px solid var(--gray-200);
  position: relative;
}

.username {
  font-size: 14px;
  font-weight: 500;
  color: var(--gray-700);
}

/* 下拉菜单 */
.dropdown-menu {
  position: absolute;
  top: calc(100% + 2px);
  right: 0;
  background: #fff;
  border: 1px solid var(--gray-200);
  border-radius: var(--radius-sm);
  box-shadow: 0 4px 12px rgba(0,0,0,0.15);
  min-width: 140px;
  z-index: 300;
  padding: 6px 0;
}

.dropdown-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: var(--gray-700);
  transition: background var(--transition-fast);
  white-space: nowrap;
}

.dropdown-item:hover {
  background: var(--gray-100);
}

.dropdown-item-danger {
  color: var(--danger);
}

.dropdown-item-danger:hover {
  background: var(--danger-bg);
}

.dropdown-divider {
  height: 1px;
  background: var(--gray-200);
  margin: 6px 0;
}

.dropdown-icon {
  font-size: 14px;
  width: 20px;
  text-align: center;
}

/* ===== 主内容区 ===== */
.main-content {
  flex: 1;
  padding: 24px 28px;
}
</style>

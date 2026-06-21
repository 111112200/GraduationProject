<template>
  <div class="auth-container">
    <div class="glass-panel">
      <div class="brand">
        <h1>实验报告语义查重系统</h1>
        <p>欢迎回来，请登录您的账号</p>
      </div>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="input-group">
          <label for="username">用户名</label>
          <input 
            id="username"
            v-model="username" 
            type="text" 
            placeholder="请输入用户名" 
            required
            :class="{ 'has-value': username.length > 0 }"
          />
        </div>

        <div class="input-group">
          <label for="password">密码</label>
          <input 
            id="password"
            v-model="password" 
            type="password" 
            placeholder="请输入密码" 
            required
            :class="{ 'has-value': password.length > 0 }"
          />
        </div>

        <div v-if="errorMsg" class="error-msg">
          {{ errorMsg }}
        </div>

        <button type="submit" class="submit-btn" :disabled="isLoading">
          <span v-if="isLoading" class="spinner"></span>
          <span v-else>登 录</span>
        </button>

        <div class="switch-link">
          还没有账号？<router-link to="/register">立即注册</router-link>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login } from '../api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

const handleLogin = async () => {
  if (!username.value || !password.value) return
  
  try {
    isLoading.value = true
    errorMsg.value = ''
    await login(username.value, password.value)
    router.push('/')
  } catch (err) {
    errorMsg.value = err.message || '登录失败，请检查用户名或密码'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
/* 背景使用现代、通透的渐变亮色 */
.auth-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #e0c3fc 0%, #8ec5fc 100%);
  font-family: 'Inter', 'Helvetica Neue', Arial, sans-serif;
  overflow: hidden;
  position: relative;
}

/* 添加一些背景点缀以增加层次感 */
.auth-container::before {
  content: '';
  position: absolute;
  top: -10%;
  left: -10%;
  width: 400px;
  height: 400px;
  background: rgba(255, 255, 255, 0.4);
  filter: blur(80px);
  border-radius: 50%;
  z-index: 1;
}
.auth-container::after {
  content: '';
  position: absolute;
  bottom: -10%;
  right: -10%;
  width: 500px;
  height: 500px;
  background: rgba(142, 197, 252, 0.6);
  filter: blur(100px);
  border-radius: 50%;
  z-index: 1;
}

/* 核心毛玻璃面板 */
.glass-panel {
  position: relative;
  z-index: 10;
  width: 100%;
  max-width: 420px;
  padding: 40px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.6);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.5);
  box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.1);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.glass-panel:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 40px 0 rgba(31, 38, 135, 0.15);
}

.brand {
  text-align: center;
  margin-bottom: 30px;
}

.brand h1 {
  font-size: 24px;
  font-weight: 700;
  color: #333;
  margin: 0 0 10px 0;
  letter-spacing: -0.5px;
}

.brand p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.auth-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.input-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.input-group label {
  font-size: 13px;
  font-weight: 600;
  color: #444;
  margin-left: 4px;
}

.input-group input {
  padding: 14px 16px;
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.4);
  background: rgba(255, 255, 255, 0.7);
  font-size: 15px;
  color: #333;
  outline: none;
  transition: all 0.3s ease;
  box-shadow: inset 0 2px 4px rgba(0, 0, 0, 0.02);
}

.input-group input:focus {
  background: rgba(255, 255, 255, 0.9);
  border-color: #8ec5fc;
  box-shadow: 0 0 0 4px rgba(142, 197, 252, 0.2);
}

.error-msg {
  color: #e74c3c;
  font-size: 13px;
  text-align: center;
  background: rgba(231, 76, 60, 0.1);
  padding: 10px;
  border-radius: 8px;
  animation: fadeIn 0.3s ease;
}

.submit-btn {
  margin-top: 10px;
  padding: 14px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  justify-content: center;
  align-items: center;
  box-shadow: 0 4px 15px rgba(118, 75, 162, 0.3);
}

.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(118, 75, 162, 0.4);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.switch-link {
  text-align: center;
  font-size: 14px;
  color: #666;
  margin-top: 10px;
}

.switch-link a {
  color: #667eea;
  text-decoration: none;
  font-weight: 600;
  transition: color 0.2s ease;
}

.switch-link a:hover {
  color: #764ba2;
  text-decoration: underline;
}

/* 简单的加载动画 */
.spinner {
  width: 20px;
  height: 20px;
  border: 3px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: white;
  animation: spin 1s ease-in-out infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(-5px); }
  to { opacity: 1; transform: translateY(0); }
}

/* 响应式调整 */
@media (max-width: 480px) {
  .glass-panel {
    border-radius: 0;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    background: rgba(255, 255, 255, 0.8);
  }
}
</style>

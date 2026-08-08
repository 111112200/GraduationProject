<template>
  <div class="auth-container">
    <main class="auth-shell">
      <section class="auth-aside">
        <div class="auth-mark" aria-hidden="true">SR</div>
        <p class="auth-eyebrow">Academic workspace</p>
        <h1>创建工作账号</h1>
        <p>建立账号后即可开始管理实验报告与语义检测任务。</p>
      </section>

      <section class="auth-panel" aria-labelledby="register-title">
        <div class="auth-heading">
          <p>开始使用</p>
          <h2 id="register-title">注册账号</h2>
        </div>

        <form class="auth-form" @submit.prevent="handleRegister">
          <div class="input-group">
            <label for="username">用户名</label>
            <input id="username" v-model="username" type="text" placeholder="请输入至少 4 位用户名" required minlength="4" />
          </div>

          <div class="input-group">
            <label for="password">密码</label>
            <input id="password" v-model="password" type="password" placeholder="请输入至少 6 位密码" required minlength="6" />
          </div>

          <div class="input-group">
            <label for="confirmPassword">确认密码</label>
            <input id="confirmPassword" v-model="confirmPassword" type="password" placeholder="请再次输入密码" required />
          </div>

          <p v-if="errorMsg" class="error-msg">{{ errorMsg }}</p>

          <button type="submit" class="submit-btn" :disabled="isLoading">
            <span v-if="isLoading" class="spinner"></span>
            <span v-else>注册</span>
          </button>

          <p class="switch-link">已有账号？<router-link to="/login">返回登录</router-link></p>
        </form>
      </section>
    </main>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '../api/auth'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const isLoading = ref(false)
const errorMsg = ref('')

const handleRegister = async () => {
  if (!username.value || !password.value || !confirmPassword.value) return

  if (password.value !== confirmPassword.value) {
    errorMsg.value = '两次输入的密码不一致'
    return
  }

  try {
    isLoading.value = true
    errorMsg.value = ''
    await register(username.value, password.value)
    router.push('/')
  } catch (err) {
    errorMsg.value = err.message || '注册失败，请更换用户名重试'
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.auth-container {
  display: grid;
  min-height: 100vh;
  padding: 28px;
  place-items: center;
  background: #edf1f5;
}
.auth-shell {
  display: grid;
  grid-template-columns: minmax(280px, 0.85fr) minmax(340px, 1fr);
  width: min(900px, 100%);
  overflow: hidden;
  border: 1px solid var(--gray-200);
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 18px 45px rgba(13, 29, 45, 0.1);
}
.auth-aside { display: flex; flex-direction: column; justify-content: center; min-height: 550px; padding: 52px; background: #13263a; color: #fff; }
.auth-mark { display: grid; width: 42px; height: 42px; margin-bottom: 28px; place-items: center; border-radius: 6px; background: #dce7f4; color: #13263a; font-size: 14px; font-weight: 800; }
.auth-eyebrow { margin: 0 0 9px; color: #9db2c9; font-size: 12px; font-weight: 600; }
.auth-aside h1 { margin: 0; font-size: 28px; line-height: 1.35; }
.auth-aside > p:last-child { margin: 14px 0 0; color: #c0cedc; font-size: 14px; line-height: 1.8; }
.auth-panel { padding: 52px; }
.auth-heading p { margin: 0 0 5px; color: var(--gray-400); font-size: 13px; }
.auth-heading h2 { margin: 0; color: var(--gray-900); font-size: 24px; }
.auth-form { display: flex; flex-direction: column; gap: 18px; margin-top: 30px; }
.input-group { display: flex; flex-direction: column; gap: 7px; }
.input-group label { color: var(--gray-700); font-size: 13px; font-weight: 650; }
.input-group input { width: 100%; min-height: 44px; padding: 10px 12px; border: 1px solid var(--gray-200); border-radius: 6px; background: #fff; color: var(--gray-800); outline: none; }
.input-group input:focus { border-color: var(--primary); box-shadow: 0 0 0 3px rgba(47, 103, 216, 0.12); }
.error-msg { margin: -2px 0 0; padding: 10px 12px; border-left: 3px solid var(--danger); background: var(--danger-bg); color: var(--danger); font-size: 13px; }
.submit-btn { display: inline-flex; min-height: 44px; align-items: center; justify-content: center; border: 0; border-radius: 6px; background: var(--primary); box-shadow: 0 2px 7px rgba(47, 103, 216, 0.2); color: #fff; cursor: pointer; font-size: 14px; font-weight: 650; }
.submit-btn:hover:not(:disabled) { background: var(--primary-dark); }
.submit-btn:disabled { cursor: not-allowed; opacity: 0.6; }
.switch-link { margin: 0; color: var(--gray-500); font-size: 13px; text-align: center; }
.switch-link a { margin-left: 4px; font-weight: 650; }
.spinner { width: 18px; height: 18px; border: 2px solid rgba(255, 255, 255, 0.36); border-top-color: #fff; border-radius: 50%; animation: spin 0.8s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
@media (max-width: 700px) {
  .auth-container { padding: 0; align-items: stretch; }
  .auth-shell { grid-template-columns: 1fr; border: 0; border-radius: 0; box-shadow: none; }
  .auth-aside { min-height: 0; padding: 34px 28px; }
  .auth-aside h1 { font-size: 22px; }
  .auth-panel { padding: 34px 28px; }
}
</style>

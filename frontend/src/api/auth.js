import { post, postUrlEncoded } from './http'

export async function login(username, password) {
  const formData = new URLSearchParams()
  formData.append('username', username)
  formData.append('password', password)
  
  const data = await postUrlEncoded('/auth/login', formData)
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('username', username)
  return data
}

export async function register(username, password) {
  const data = await post('/auth/register', { username, password })
  localStorage.setItem('token', data.access_token)
  localStorage.setItem('username', username)
  return data
}

export function logout() {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
  window.location.href = '#/login'
}

export function isLoggedIn() {
  return !!localStorage.getItem('token')
}

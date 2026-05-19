import { get, post, del } from './http'

export function listChecks() {
  return get('/checks')
}

export function createCheck(body) {
  return post('/checks', body)
}

export function getCheckTask(taskId) {
  return get(`/checks/${taskId}`)
}

export function deleteCheckTask(taskId) {
  return del(`/checks/${taskId}`)
}

export async function exportCheckExcel(taskId) {
  const res = await fetch(`/api/checks/${taskId}/export`)
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || '导出失败')
  }
  return res.blob()
}

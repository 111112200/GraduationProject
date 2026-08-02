import { get, post, del, getBlob } from './http'

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
  return getBlob(`/checks/${taskId}/export`)
}

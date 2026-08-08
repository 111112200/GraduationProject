import { get, postForm, del } from './http'

export function uploadReports(files, experimentId, classId) {
  const fd = new FormData()
  if (experimentId != null) fd.append('experimentId', experimentId)
  fd.append('classId', classId)
  files.forEach(f => fd.append('files', f))
  return postForm('/reports/upload', fd)
}

export function getReports(params = {}) {
  const qs = new URLSearchParams(params).toString()
  return get('/reports' + (qs ? '?' + qs : ''))
}

export function getReport(reportId) {
  return get(`/reports/${reportId}`)
}

export function getReportResult(reportId, taskId) {
  return get(`/reports/${reportId}/result?taskId=${encodeURIComponent(taskId)}`)
}

export function deleteReport(reportId) {
  return del(`/reports/${reportId}`)
}

export function getReportChunks(reportId) {
  return get(`/reports/${reportId}/chunks`)
}

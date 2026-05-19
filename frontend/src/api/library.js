import { get, post, del } from './http'

export function addToLibrary(reportId) {
  return post(`/library/reports/${reportId}/add`)
}

export function removeFromLibrary(reportId) {
  return del(`/library/reports/${reportId}`)
}

export function getLibraryReports() {
  return get('/library/reports')
}

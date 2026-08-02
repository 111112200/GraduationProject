import { get, post, del } from './http'

export function getCourses() {
  return get('/course/courses')
}

export function createCourse(name, code = '') {
  return post('/course/courses', { name, code })
}

export function deleteCourse(id) {
  return del(`/course/courses/${id}`)
}

export function getClasses() {
  return get('/course/classes')
}

export function createClass(name, grade = '') {
  return post('/course/classes', { name, grade })
}

export function deleteClass(id) {
  return del(`/course/classes/${id}`)
}

export function getExperiments() {
  return get('/course/experiments')
}

export function createExperiment(courseId, title, description = '') {
  return post('/course/experiments', { courseId, title, description })
}

export function deleteExperiment(id) {
  return del(`/course/experiments/${id}`)
}

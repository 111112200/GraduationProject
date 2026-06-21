import { createRouter, createWebHistory } from 'vue-router'
import Layout from '../components/Layout.vue'
import Dashboard from '../views/Dashboard.vue'
import ReportList from '../views/ReportList.vue'
import ReportUpload from '../views/ReportUpload.vue'
import ReportResult from '../views/ResultDetail.vue'
import CheckList from '../views/CheckList.vue'
import CheckCreate from '../views/CheckCreate.vue'
import CheckDetail from '../views/CheckDetail.vue'
import LibraryManage from '../views/LibraryManage.vue'
import BasicDataManage from '../views/BasicDataManage.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'

const routes = [
  { path: '/login', name: 'login', component: Login, meta: { public: true } },
  { path: '/register', name: 'register', component: Register, meta: { public: true } },
  {
    path: '/',
    component: Layout,
    children: [
      { path: '', redirect: '/dashboard' },
      { path: 'dashboard', name: 'dashboard', component: Dashboard },
      { path: 'reports', name: 'reports', component: ReportList },
      { path: 'reports/upload', name: 'report-upload', component: ReportUpload },
      { path: 'reports/:reportId/result', name: 'report-result', component: ReportResult },
      { path: 'checks', name: 'checks', component: CheckList },
      { path: 'checks/create', name: 'check-create', component: CheckCreate },
      { path: 'checks/:id', name: 'check-detail', component: CheckDetail },
      { path: 'library', name: 'library', component: LibraryManage },
      { path: 'basic-data', name: 'basic-data', component: BasicDataManage },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, from, next) => {
  const isAuthenticated = !!localStorage.getItem('token')
  if (!to.meta.public && !isAuthenticated) {
    next({ name: 'login' })
  } else if ((to.name === 'login' || to.name === 'register') && isAuthenticated) {
    next({ name: 'dashboard' })
  } else {
    next()
  }
})

export default router

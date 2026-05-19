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

const routes = [
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

export default router


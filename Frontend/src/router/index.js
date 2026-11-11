import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/appointments' },
  { path: '/appointments', component: () => import('../views/AppointmentManagement.vue') },
  { path: '/recharges', component: () => import('../views/RechargeManagement.vue') },
  { path: '/balance-query', component: () => import('../views/BalanceQuery.vue') },
  { path: '/areas', component: () => import('../views/AreaManagement.vue') },
  { path: '/students', component: () => import('../views/StudentManagement.vue') },
  { path: '/coaches', component: () => import('../views/CoachManagement.vue') },
  { path: '/vehicles', component: () => import('../views/VehicleManagement.vue') },
  { path: '/area-statistics', component: () => import('../views/AreaStatistics.vue') },
  { path: '/audit-logs', component: () => import('../views/AuditLog.vue') },
  { path: '/pivot-analysis', component: () => import('../views/PivotAnalysis.vue') },
  { path: '/settings', component: () => import('../views/Settings.vue') }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

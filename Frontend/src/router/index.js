import { createRouter, createWebHistory } from 'vue-router'
import AreaManagement from '../views/AreaManagement.vue'
import PersonManagement from '../views/PersonManagement.vue'
import AppointmentManagement from '../views/AppointmentManagement.vue'
import AreaStatistics from '../views/AreaStatistics.vue'

const routes = [
  { path: '/', redirect: '/appointments' },
  { path: '/appointments', component: AppointmentManagement },
  { path: '/area-statistics', component: AreaStatistics },
  { path: '/areas', component: AreaManagement },
  { path: '/persons', component: PersonManagement }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

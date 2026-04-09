import { createRouter, createWebHistory } from 'vue-router'
import AreaManagement from '../views/AreaManagement.vue'
import PersonManagement from '../views/PersonManagement.vue'
import AppointmentManagement from '../views/AppointmentManagement.vue'

const routes = [
  { path: '/', redirect: '/areas' },
  { path: '/areas', component: AreaManagement },
  { path: '/persons', component: PersonManagement },
  { path: '/appointments', component: AppointmentManagement }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

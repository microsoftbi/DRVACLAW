import { createRouter, createWebHistory } from 'vue-router'
import AreaManagement from '../views/AreaManagement.vue'
import PersonManagement from '../views/PersonManagement.vue'
import AppointmentManagement from '../views/AppointmentManagement.vue'
import AreaStatistics from '../views/AreaStatistics.vue'
import RechargeManagement from '../views/RechargeManagement.vue'
import BalanceQuery from '../views/BalanceQuery.vue'

const routes = [
  { path: '/', redirect: '/appointments' },
  { path: '/appointments', component: AppointmentManagement },
  { path: '/recharges', component: RechargeManagement },
  { path: '/balance-query', component: BalanceQuery },
  { path: '/areas', component: AreaManagement },
  { path: '/persons', component: PersonManagement },
  { path: '/area-statistics', component: AreaStatistics }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

export default router

import axios from 'axios'

// 默认走同源相对路径，由 Vite 代理转发到后端；可通过 VITE_API_BASE 覆盖部署地址
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE || '',
  timeout: 10000
})

service.interceptors.response.use(
  response => response.data,
  error => Promise.reject(error)
)

export default service

import axios from 'axios'

const service = axios.create({
  baseURL: 'http://localhost:8002',
  timeout: 10000
})

service.interceptors.response.use(
  response => response.data,
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default service

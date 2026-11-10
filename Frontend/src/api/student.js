import request from './request'

export const studentApi = {
  create(data) {
    return request.post('/api/students', data)
  },
  getAll() {
    return request.get('/api/students')
  },
  getById(id) {
    return request.get(`/api/students/${id}`)
  },
  update(id, data) {
    return request.put(`/api/students/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/students/${id}`)
  }
}

export default studentApi

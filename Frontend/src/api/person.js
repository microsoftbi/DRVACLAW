import request from './request'

export const personApi = {
  create(data) {
    return request.post('/api/persons', data)
  },
  getAll() {
    return request.get('/api/persons')
  },
  getStudents() {
    return request.get('/api/persons/students')
  },
  getCoaches() {
    return request.get('/api/persons/coaches')
  },
  getById(id) {
    return request.get(`/api/persons/${id}`)
  },
  update(id, data) {
    return request.put(`/api/persons/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/persons/${id}`)
  }
}

export default personApi

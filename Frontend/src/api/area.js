import request from './request'

export const areaApi = {
  create(data) {
    return request.post('/api/areas', data)
  },
  getAll() {
    return request.get('/api/areas')
  },
  getById(id) {
    return request.get(`/api/areas/${id}`)
  },
  update(id, data) {
    return request.put(`/api/areas/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/areas/${id}`)
  }
}

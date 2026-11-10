import request from './request'

export const vehicleApi = {
  create(data) {
    return request.post('/api/vehicles', data)
  },
  getAll() {
    return request.get('/api/vehicles')
  },
  getById(id) {
    return request.get(`/api/vehicles/${id}`)
  },
  update(id, data) {
    return request.put(`/api/vehicles/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/vehicles/${id}`)
  }
}

export default vehicleApi

import request from './request'

export const coachApi = {
  create(data) {
    return request.post('/api/coaches', data)
  },
  getAll() {
    return request.get('/api/coaches')
  },
  getById(id) {
    return request.get(`/api/coaches/${id}`)
  },
  getVehicles(id) {
    return request.get(`/api/coaches/${id}/vehicles`)
  },
  update(id, data) {
    return request.put(`/api/coaches/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/coaches/${id}`)
  }
}

export default coachApi

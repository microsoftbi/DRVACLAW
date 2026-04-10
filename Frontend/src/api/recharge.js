import request from './request'

const rechargeApi = {
  create: (data) => {
    return request.post('/api/recharges', data)
  },
  getAll: () => {
    return request.get('/api/recharges')
  },
  getByStudent: (studentId) => {
    return request.get(`/api/recharges/student/${studentId}`)
  },
  getById: (id) => {
    return request.get(`/api/recharges/${id}`)
  },
  update: (id, data) => {
    return request.put(`/api/recharges/${id}`, data)
  },
  delete: (id) => {
    return request.delete(`/api/recharges/${id}`)
  }
}

export default rechargeApi
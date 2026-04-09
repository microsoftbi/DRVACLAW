import request from './request'

export const appointmentApi = {
  create(data) {
    return request.post('/api/appointments', data)
  },
  getAll() {
    return request.get('/api/appointments')
  },
  getById(id) {
    return request.get(`/api/appointments/${id}`)
  },
  getByStudentId(studentId) {
    return request.get(`/api/appointments/student/${studentId}`)
  },
  getByCoachId(coachId) {
    return request.get(`/api/appointments/coach/${coachId}`)
  },
  getByDate(date) {
    return request.get(`/api/appointments/date/${date}`)
  },
  update(id, data) {
    return request.put(`/api/appointments/${id}`, data)
  },
  delete(id) {
    return request.delete(`/api/appointments/${id}`)
  }
}

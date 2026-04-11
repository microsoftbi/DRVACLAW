import request from './request'

export default {
  // 获取所有操作审计记录
  getAll() {
    return request({
      url: '/api/audit-logs/',
      method: 'get'
    })
  },
  
  // 根据学员ID获取操作审计记录
  getByStudent(studentId) {
    return request({
      url: `/api/audit-logs/student/${studentId}/`,
      method: 'get'
    })
  },
  
  // 根据教练ID获取操作审计记录
  getByCoach(coachId) {
    return request({
      url: `/api/audit-logs/coach/${coachId}/`,
      method: 'get'
    })
  }
}

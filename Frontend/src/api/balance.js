import request from './request'

const balanceApi = {
  // 获取所有余额记录
  getAll() {
    return request.get('/api/balance-records')
  },
  // 获取指定学员的余额记录
  getByStudentId(studentId) {
    return request.get(`/api/balance-records/student/${studentId}`)
  },
  // 获取指定余额记录
  getById(recordId) {
    return request.get(`/api/balance-records/${recordId}`)
  }
}

export default balanceApi
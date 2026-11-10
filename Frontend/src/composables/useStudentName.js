/**
 * 生成“学员ID → 学员姓名”的取值函数，避免各页面重复实现查找逻辑。
 * @param {import('vue').Ref<Array>} studentsRef 学员列表
 * @param {string} fallback 未匹配时的占位文案
 */
export function createStudentNameGetter(studentsRef, fallback = '未知学员') {
  return (studentId) => {
    const list = studentsRef.value
    if (!list || !studentId) return fallback
    const student = list.find(item => item.student_id === studentId)
    return student ? student.name : fallback
  }
}

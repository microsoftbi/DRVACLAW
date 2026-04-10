<template>
  <div class="balance-query">
    <h1>余额查询</h1>
    
    <!-- 学员筛选 -->
    <div style="margin-bottom: 20px;">
      <el-select v-model="selectedStudentId" placeholder="请选择学员" style="width: 300px;" filterable>
        <el-option
          v-for="student in students"
          :key="student.person_id"
          :label="`${student.name} - ${getAreaName(student.area_id)} - ${student.phone}`"
          :value="student.person_id"
        />
      </el-select>
    </div>
    
    <!-- 余额记录列表 -->
    <table class="custom-table">
      <thead>
        <tr>
          <th>学员</th>
          <th>区域</th>
          <th>日期</th>
          <th>课时</th>
          <th>类型</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(record, index) in sortedRecords" :key="index">
          <td>{{ record.studentName }}</td>
          <td>{{ record.areaName }}</td>
          <td>{{ record.date }}</td>
          <td>{{ record.hours }}</td>
          <td>{{ record.type }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import appointmentApi from '../api/appointment'
import rechargeApi from '../api/recharge'
import personApi from '../api/person'
import areaApi from '../api/area'

const appointments = ref([])
const recharges = ref([])
const students = ref([])
const areas = ref([])
const selectedStudentId = ref('')

const loadAppointments = async () => {
  try {
    const response = await appointmentApi.getAll()
    appointments.value = (response || []).filter(appointment => appointment.status === '已完成')
  } catch (error) {
    ElMessage.error('获取预约记录失败')
    appointments.value = []
  }
}

const loadRecharges = async () => {
  try {
    const response = await rechargeApi.getAll()
    recharges.value = response || []
  } catch (error) {
    ElMessage.error('获取充值记录失败')
    recharges.value = []
  }
}

const loadStudents = async () => {
  try {
    const response = await personApi.getAll()
    students.value = (response || []).filter(person => person.type === '学员')
  } catch (error) {
    ElMessage.error('获取学员列表失败')
    students.value = []
  }
}

const loadAreas = async () => {
  try {
    const response = await areaApi.getAll()
    areas.value = response || []
  } catch (error) {
    ElMessage.error('获取区域列表失败')
    areas.value = []
  }
}

const getStudentName = (studentId) => {
  if (!students.value) return '未知学员'
  const student = students.value.find(s => s.person_id === studentId)
  return student ? student.name : '未知学员'
}

const getAreaName = (areaId) => {
  if (!areas.value) return '未知区域'
  const area = areas.value.find(a => a.area_id === areaId)
  return area ? area.name : '未知区域'
}

const calculateHours = (startTime, endTime) => {
  if (!startTime || !endTime) return 0
  // 检查startTime和endTime是否为数字类型
  if (typeof startTime === 'number' && typeof endTime === 'number') {
    // 如果是数字类型，直接计算差值
    const diff = endTime - startTime
    return diff.toFixed(1)
  } else {
    // 如果是字符串类型，使用Date对象计算
    const start = new Date(startTime)
    const end = new Date(endTime)
    const diff = (end - start) / (1000 * 60 * 60) // 转换为小时
    return diff.toFixed(1)
  }
}

const records = computed(() => {
  // 处理预约记录
  let appointmentRecords = appointments.value.map(appointment => {
    const student = students.value.find(s => s.person_id === appointment.student_id)
    const areaId = student ? student.area_id : null
    return {
      studentId: appointment.student_id,
      studentName: getStudentName(appointment.student_id),
      areaName: getAreaName(areaId),
      date: appointment.appointment_date,
      hours: calculateHours(appointment.start_time, appointment.end_time),
      type: '预约',
      time: appointment.appointment_date + ' ' + appointment.start_time
    }
  })

  // 处理充值记录
  let rechargeRecords = recharges.value.map(recharge => {
    const student = students.value.find(s => s.person_id === recharge.student_id)
    const areaId = student ? student.area_id : null
    return {
      studentId: recharge.student_id,
      studentName: getStudentName(recharge.student_id),
      areaName: getAreaName(areaId),
      date: recharge.recharge_time,
      hours: recharge.course_count,
      type: '充值',
      time: recharge.recharge_time
    }
  })

  // 合并记录
  let allRecords = [...appointmentRecords, ...rechargeRecords]

  // 根据选中的学员筛选
  if (selectedStudentId.value) {
    allRecords = allRecords.filter(record => record.studentId === selectedStudentId.value)
  }

  return allRecords
})

const sortedRecords = computed(() => {
  // 按照时间排序，最新的在前面
  return [...records.value].sort((a, b) => new Date(b.time) - new Date(a.time))
})

onMounted(() => {
  loadAppointments()
  loadRecharges()
  loadStudents()
  loadAreas()
})
</script>

<style scoped>
.balance-query {
  padding: 20px;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 20px;
}

.custom-table th,
.custom-table td {
  padding: 8px 12px;
  border: 1px solid #ddd;
  text-align: left;
}

.custom-table th {
  background-color: #f5f7fa;
  font-weight: bold;
}

.custom-table tr:nth-child(even) {
  background-color: #f9f9f9;
}
</style>
<template>
  <div class="balance-query">
    <h1>余额查询</h1>
    
    <!-- 学员筛选 -->
    <div style="margin-bottom: 20px;">
      <el-select v-model="selectedStudentId" placeholder="请选择学员" style="width: 300px;" filterable>
        <el-option
          v-for="student in students.filter(s => s.type === '学员')"
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
          <th>结余</th>
          <th>类型</th>
          <th>充值详细信息</th>
          <th>课程预约详细信息</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(record, index) in filteredRecords" :key="index">
          <td>{{ record.studentName }}</td>
          <td>{{ record.areaName }}</td>
          <td>{{ record.date }}</td>
          <td>{{ record.hours }}</td>
          <td>{{ record.balance }}</td>
          <td>{{ record.type }}</td>
          <td>
            <el-button 
              v-if="record.rechargeId" 
              type="primary" 
              size="small" 
              @click="openRechargeDialog(record.rechargeId)"
            >
              查看
            </el-button>
            <span v-else>-</span>
          </td>
          <td>
            <el-button 
              v-if="record.appointmentId" 
              type="primary" 
              size="small" 
              @click="openAppointmentDialog(record.appointmentId)"
            >
              查看
            </el-button>
            <span v-else>-</span>
          </td>
        </tr>
      </tbody>
    </table>
    
    <!-- 充值详情弹窗 -->
    <el-dialog
      v-model="rechargeDialogVisible"
      title="充值详细信息"
      width="500px"
    >
      <div v-if="rechargeDetail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="充值ID">{{ rechargeDetail.recharge_id }}</el-descriptions-item>
          <el-descriptions-item label="学员ID">{{ rechargeDetail.student_id }}</el-descriptions-item>
          <el-descriptions-item label="学员姓名">{{ getStudentName(rechargeDetail.student_id) }}</el-descriptions-item>
          <el-descriptions-item label="充值金额">{{ rechargeDetail.amount }} 元</el-descriptions-item>
          <el-descriptions-item label="课程数量">{{ rechargeDetail.course_count }} 课时</el-descriptions-item>
          <el-descriptions-item label="充值时间">{{ rechargeDetail.recharge_time }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else>
        <el-empty description="加载中..." />
      </div>
    </el-dialog>
    
    <!-- 预约详情弹窗 -->
    <el-dialog
      v-model="appointmentDialogVisible"
      title="课程预约详细信息"
      width="500px"
    >
      <div v-if="appointmentDetail">
        <el-descriptions :column="1" border>
          <el-descriptions-item label="预约ID">{{ appointmentDetail.appointment_id }}</el-descriptions-item>
          <el-descriptions-item label="学员ID">{{ appointmentDetail.student_id }}</el-descriptions-item>
          <el-descriptions-item label="学员姓名">{{ getStudentName(appointmentDetail.student_id) }}</el-descriptions-item>
          <el-descriptions-item label="教练ID">{{ appointmentDetail.coach_id }}</el-descriptions-item>
          <el-descriptions-item label="教练姓名">{{ getCoachName(appointmentDetail.coach_id) }}</el-descriptions-item>
          <el-descriptions-item label="预约日期">{{ appointmentDetail.appointment_date }}</el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ appointmentDetail.start_time }}:00</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ appointmentDetail.end_time }}:00</el-descriptions-item>
          <el-descriptions-item label="状态">{{ appointmentDetail.status }}</el-descriptions-item>
          <el-descriptions-item label="创建时间">{{ appointmentDetail.create_time }}</el-descriptions-item>
        </el-descriptions>
      </div>
      <div v-else>
        <el-empty description="加载中..." />
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import balanceApi from '../api/balance'
import personApi from '../api/person'
import areaApi from '../api/area'
import rechargeApi from '../api/recharge'
import appointmentApi from '../api/appointment'

const records = ref([])
const students = ref([])
const areas = ref([])
const selectedStudentId = ref('')

// 弹窗相关
const rechargeDialogVisible = ref(false)
const appointmentDialogVisible = ref(false)
const rechargeDetail = ref(null)
const appointmentDetail = ref(null)

const loadRecords = async () => {
  try {
    const response = await balanceApi.getAll()
    records.value = response || []
  } catch (error) {
    ElMessage.error('获取余额记录失败')
    records.value = []
  }
}

const loadStudents = async () => {
  try {
    const response = await personApi.getAll()
    students.value = response || [] // 包含所有人员（学员和教练）
  } catch (error) {
    ElMessage.error('获取人员列表失败')
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
  const student = students.value.find(s => s.person_id === studentId && s.type === '学员')
  return student ? student.name : '未知学员'
}

const getAreaName = (areaId) => {
  if (!areas.value) return '未知区域'
  const area = areas.value.find(a => a.area_id === areaId)
  return area ? area.name : '未知区域'
}

const getCoachName = (coachId) => {
  if (!students.value) return '未知教练'
  const coach = students.value.find(s => s.person_id === coachId && s.type === '教练')
  return coach ? coach.name : '未知教练'
}

const openRechargeDialog = async (rechargeId) => {
  try {
    const response = await rechargeApi.getById(rechargeId)
    rechargeDetail.value = response
    rechargeDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取充值详情失败')
  }
}

const openAppointmentDialog = async (appointmentId) => {
  try {
    const response = await appointmentApi.getById(appointmentId)
    appointmentDetail.value = response
    appointmentDialogVisible.value = true
  } catch (error) {
    ElMessage.error('获取预约详情失败')
  }
}

const filteredRecords = computed(() => {
  // 处理余额记录
  let processedRecords = records.value.map(record => {
    return {
      studentId: record.student_id,
      studentName: getStudentName(record.student_id),
      areaName: getAreaName(record.area_id),
      date: record.record_date,
      hours: record.hours,
      balance: record.balance,
      type: record.type,
      rechargeId: record.recharge_id,
      appointmentId: record.appointment_id
    }
  })

  // 根据选中的学员筛选
  if (selectedStudentId.value) {
    processedRecords = processedRecords.filter(record => record.studentId === selectedStudentId.value)
  }

  return processedRecords
})

onMounted(() => {
  loadRecords()
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
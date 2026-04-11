<template>
  <div class="audit-log">
    <h1>操作审计</h1>
    
    <!-- 筛选器 -->
    <div class="filter-container">
      <el-form :inline="true" :model="filterForm" class="filter-form">
        <el-form-item label="学员">
          <el-select v-model="filterForm.student_id" placeholder="请选择学员" style="width: 200px" filterable>
            <el-option
              v-for="student in students"
              :key="student.person_id"
              :label="`${student.name} - ${getAreaName(student.area_id)}`"
              :value="student.person_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="教练">
          <el-select v-model="filterForm.coach_id" placeholder="请选择教练" style="width: 200px" filterable>
            <el-option
              v-for="coach in coaches"
              :key="coach.person_id"
              :label="`${coach.name} - ${getAreaName(coach.area_id)}`"
              :value="coach.person_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="loadAuditLogs">查询</el-button>
          <el-button @click="resetFilter">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
    
    <!-- 操作审计列表 -->
    <table class="custom-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>操作人</th>
          <th>学员</th>
          <th>教练</th>
          <th>操作时间</th>
          <th>操作类型</th>
          <th>操作结果</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="log in filteredLogs" :key="log.audit_id">
          <td>{{ log.audit_id }}</td>
          <td>{{ log.operator }}</td>
          <td>{{ getStudentName(log.student_id) }}</td>
          <td>{{ getCoachName(log.coach_id) }}</td>
          <td>{{ log.operation_time }}</td>
          <td>{{ log.operation_type }}</td>
          <td>{{ log.operation_result }}</td>
        </tr>
      </tbody>
    </table>
    
    <!-- 分页 -->
    <div style="margin-top: 20px; text-align: right;">
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="(auditLogs || []).length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import auditApi from '../api/audit'
import personApi from '../api/person'
import areaApi from '../api/area'

const auditLogs = ref([])
const students = ref([])
const coaches = ref([])
const areas = ref([])
const currentPage = ref(1)
const pageSize = ref(20)

const filterForm = ref({
  student_id: '',
  coach_id: ''
})

const paginatedLogs = computed(() => {
  if (!auditLogs.value) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return auditLogs.value.slice(start, end)
})

const filteredLogs = computed(() => {
  let result = auditLogs.value
  
  if (filterForm.value.student_id) {
    result = result.filter(log => log.student_id === filterForm.value.student_id)
  }
  
  if (filterForm.value.coach_id) {
    result = result.filter(log => log.coach_id === filterForm.value.coach_id)
  }
  
  return result
})

const loadAuditLogs = async () => {
  try {
    let logs
    if (filterForm.value.student_id) {
      logs = await auditApi.getByStudent(filterForm.value.student_id)
    } else if (filterForm.value.coach_id) {
      logs = await auditApi.getByCoach(filterForm.value.coach_id)
    } else {
      logs = await auditApi.getAll()
    }
    auditLogs.value = logs || []
  } catch (error) {
    ElMessage.error('获取操作审计记录失败')
    auditLogs.value = []
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

const loadStudentsAndCoaches = async () => {
  try {
    const response = await personApi.getAll()
    const persons = response || []
    students.value = persons.filter(person => person.type === '学员')
    coaches.value = persons.filter(person => person.type === '教练')
  } catch (error) {
    ElMessage.error('获取人员列表失败')
    students.value = []
    coaches.value = []
  }
}

const getAreaName = (areaId) => {
  if (!areas.value) return '未知区域'
  const area = areas.value.find(a => a.area_id === areaId)
  return area ? area.name : '未知区域'
}

const getStudentName = (studentId) => {
  if (!students.value || !studentId) return '未知学员'
  const student = students.value.find(s => s.person_id === studentId)
  return student ? student.name : '未知学员'
}

const getCoachName = (coachId) => {
  if (!coaches.value || !coachId) return '未知教练'
  const coach = coaches.value.find(c => c.person_id === coachId)
  return coach ? coach.name : '未知教练'
}

const resetFilter = () => {
  filterForm.value = {
    student_id: '',
    coach_id: ''
  }
  loadAuditLogs()
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (current) => {
  currentPage.value = current
}

onMounted(() => {
  loadAuditLogs()
  loadAreas()
  loadStudentsAndCoaches()
})
</script>

<style scoped>
.audit-log {
  padding: 20px;
}

.filter-container {
  margin-bottom: 20px;
  padding: 10px;
  background-color: #f5f7fa;
  border-radius: 4px;
}

.custom-table {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 20px;
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

.custom-table tr:hover {
  background-color: #f5f7fa;
}
</style>

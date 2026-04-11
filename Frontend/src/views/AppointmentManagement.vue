<template>
  <div class="appointment-management">
    <h2>预约管理</h2>
    
    <div class="filter-container" style="margin-top: 20px; padding: 16px; background-color: #f5f7fa; border-radius: 4px;">
      <el-row :gutter="20">
        <el-col :span="6">
          <el-form-item label="学员">
            <el-select v-model="filters.student_id" placeholder="选择学员" clearable filterable>
              <el-option label="全部" value="" />
              <el-option v-for="student in students" :key="student.person_id" :label="`${student.name} ${student.phone}`" :value="student.person_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="学员区域">
            <el-select v-model="filters.student_area_id" placeholder="选择学员区域" clearable>
              <el-option label="全部" value="" />
              <el-option v-for="area in areas" :key="area.area_id" :label="area.name" :value="area.area_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="教练">
            <el-select v-model="filters.coach_id" placeholder="选择教练" clearable filterable>
              <el-option label="全部" value="" />
              <el-option v-for="coach in coaches" :key="coach.person_id" :label="coach.name" :value="coach.person_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="教练区域">
            <el-select v-model="filters.coach_area_id" placeholder="选择教练区域" clearable>
              <el-option label="全部" value="" />
              <el-option v-for="area in areas" :key="area.area_id" :label="area.name" :value="area.area_id" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="时间">
            <el-date-picker
              v-model="filters.date"
              type="date"
              placeholder="选择日期"
              value-format="YYYY-MM-DD"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="状态">
            <el-select v-model="filters.status" placeholder="选择状态" clearable>
              <el-option label="全部" value="" />
              <el-option label="待确认" value="待确认" />
              <el-option label="已确认" value="已确认" />
              <el-option label="已取消" value="已取消" />
              <el-option label="已完成" value="已完成" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="6">
          <el-form-item label="操作">
            <el-button type="primary" @click="applyFilters">筛选</el-button>
            <el-button @click="resetFilters">重置</el-button>
          </el-form-item>
        </el-col>
      </el-row>
    </div>
    
    <!-- 顶部分页和添加按钮 -->
    <div style="margin-top: 20px; display: flex; justify-content: space-between; align-items: center;">
      <el-button type="primary" @click="showAddDialog">添加预约</el-button>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        :total="filteredAppointments.length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <table class="data-table" style="width: 100%; margin-top: 20px; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="width: 100px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">预约ID</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">学员</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">学员区域</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">教练</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">教练区域</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">预约日期</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">预约时间</th>
          <th style="width: 100px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">状态</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">创建时间</th>
          <th style="width: 80px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">明细</th>
          <th style="width: 250px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="appt in paginatedAppointments" :key="appt.appointment_id">
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ appt.appointment_id }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ getPersonName(appt.student_id) }} {{ getPersonPhone(appt.student_id) }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ getPersonArea(appt.student_id) }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ getPersonName(appt.coach_id) }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ getPersonArea(appt.coach_id) }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ appt.appointment_date }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ appt.start_time }}:00 - {{ appt.end_time }}:00</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-tag :type="getStatusType(appt.status)">{{ appt.status }}</el-tag>
          </td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ appt.create_time }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showDetailDialog(appt)">明细</el-button>
          </td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showEditDialog(appt)">编辑</el-button>
            <el-button size="small" type="success" @click="updateStatus(appt, '已确认')" v-if="appt.status === '待确认'">确认</el-button>
            <el-button size="small" type="warning" @click="updateStatus(appt, '已取消')" v-if="appt.status !== '已取消'">取消</el-button>
            <el-button size="small" type="danger" @click="deleteAppointment(appt.appointment_id)">删除</el-button>
          </td>
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
        :total="filteredAppointments.length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑预约' : '添加预约'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="学员">
          <el-select v-model="form.student_id">
            <el-option v-for="student in students" :key="student.person_id" :label="`${student.name} ${student.phone}`" :value="student.person_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教练">
          <el-select v-model="form.coach_id">
            <el-option v-for="coach in coaches" :key="coach.person_id" :label="coach.name" :value="coach.person_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="预约日期">
          <el-date-picker v-model="form.appointment_date" type="date" format="YYYY-MM-DD" value-format="YYYY-MM-DD" />
        </el-form-item>
        <el-form-item label="开始时间">
          <el-select v-model="form.start_time">
            <el-option v-for="i in 24" :key="i" :label="i + ':00'" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="结束时间">
          <el-select v-model="form.end_time">
            <el-option v-for="i in 24" :key="i" :label="i + ':00'" :value="i" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态" prop="status">
            <el-select v-model="form.status">
              <el-option label="待确认" value="待确认" />
              <el-option label="已确认" value="已确认" />
              <el-option label="已取消" value="已取消" />
              <el-option label="已完成" value="已完成" />
            </el-select>
          </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveAppointment">保存</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="detailDialogVisible" title="预约明细" width="600px">
      <div v-if="currentAppointment" class="detail-content">
        <div class="detail-section">
          <h3>预约信息</h3>
          <p><strong>预约ID：</strong>{{ currentAppointment.appointment_id }}</p>
          <p><strong>预约日期：</strong>{{ currentAppointment.appointment_date }}</p>
          <p><strong>预约时间：</strong>{{ currentAppointment.start_time }}:00 - {{ currentAppointment.end_time }}:00</p>
          <p><strong>状态：</strong>
            <el-tag :type="getStatusType(currentAppointment.status)">{{ currentAppointment.status }}</el-tag>
          </p>
          <p><strong>创建时间：</strong>{{ currentAppointment.create_time }}</p>
        </div>
        <div class="detail-section">
          <h3>学员信息</h3>
          <p><strong>姓名：</strong>{{ getPersonName(currentAppointment.student_id) }}</p>
          <p><strong>手机号：</strong>{{ getPersonPhone(currentAppointment.student_id) }}</p>
          <p><strong>区域：</strong>{{ getPersonArea(currentAppointment.student_id) }}</p>
        </div>
        <div class="detail-section">
          <h3>教练信息</h3>
          <p><strong>姓名：</strong>{{ getPersonName(currentAppointment.coach_id) }}</p>
          <p><strong>手机号：</strong>{{ getPersonPhone(currentAppointment.coach_id) }}</p>
          <p><strong>区域：</strong>{{ getPersonArea(currentAppointment.coach_id) }}</p>
        </div>
      </div>
      <template #footer>
        <el-button @click="detailDialogVisible = false">关闭</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { appointmentApi } from '../api/appointment'
import { personApi } from '../api/person'
import { areaApi } from '../api/area'

const appointments = ref([])
const students = ref([])
const coaches = ref([])
const persons = ref([])
const areas = ref([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const currentAppointment = ref(null)
const form = ref({ student_id: null, coach_id: null, appointment_date: '', start_time: 9, end_time: 11, status: '待确认' })
const filters = ref({ student_id: null, student_area_id: null, coach_id: null, coach_area_id: null, date: null, status: null })

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const allAppointments = ref([])
const filteredAppointments = ref([])

// 分页数据
const paginatedAppointments = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return filteredAppointments.value.slice(start, end)
})

const loadAppointments = async () => {
  try {
    allAppointments.value = await appointmentApi.getAll()
    filteredAppointments.value = [...allAppointments.value]
  } catch (error) {
    ElMessage.error('加载预约列表失败')
  }
}

const loadPersons = async () => {
  try {
    persons.value = await personApi.getAll()
    students.value = await personApi.getStudents()
    coaches.value = await personApi.getCoaches()
    areas.value = await areaApi.getAll()
  } catch (error) {
    ElMessage.error('加载人员列表失败')
  }
}

const getPersonName = (id) => {
  const person = persons.value.find(p => p.person_id === id)
  return person ? person.name : id
}

const getPersonPhone = (id) => {
  const person = persons.value.find(p => p.person_id === id)
  return person ? person.phone : '-'
}

const getPersonArea = (id) => {
  const person = persons.value.find(p => p.person_id === id)
  if (!person || !person.area_id) return '-'
  const area = areas.value.find(a => a.area_id === person.area_id)
  return area ? area.name : '-'
}

const getStatusType = (status) => {
  if (status === '待确认') return 'warning'
  if (status === '已确认') return 'success'
  return 'info'
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { student_id: null, coach_id: null, appointment_date: '', start_time: 9, end_time: 11, status: '待确认' }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentId.value = row.appointment_id
  form.value = { 
    student_id: row.student_id, 
    coach_id: row.coach_id, 
    appointment_date: row.appointment_date, 
    start_time: row.start_time, 
    end_time: row.end_time, 
    status: row.status 
  }
  dialogVisible.value = true
}

const showDetailDialog = (row) => {
  currentAppointment.value = row
  detailDialogVisible.value = true
}

const saveAppointment = async () => {
  try {
    if (isEdit.value) {
      await appointmentApi.update(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await appointmentApi.create(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    await loadAppointments()
    applyFilters()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const updateStatus = async (row, status) => {
  try {
    await appointmentApi.update(row.appointment_id, { status })
    ElMessage.success('状态更新成功')
    await loadAppointments()
    applyFilters()
  } catch (error) {
    ElMessage.error('状态更新失败')
  }
}

const deleteAppointment = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个预约吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await appointmentApi.delete(id)
    ElMessage.success('删除成功')
    await loadAppointments()
    applyFilters()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

// 分页处理
const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1 // 重置页码
}

const handleCurrentChange = (current) => {
  currentPage.value = current
}



const applyFilters = () => {
  // 实现筛选逻辑
  let filtered = [...allAppointments.value]
  
  if (filters.value.student_id && filters.value.student_id !== '') {
    filtered = filtered.filter(appt => appt.student_id === filters.value.student_id)
  }
  
  if (filters.value.student_area_id && filters.value.student_area_id !== '') {
    filtered = filtered.filter(appt => {
      const student = persons.value.find(p => p.person_id === appt.student_id)
      return student && student.area_id === filters.value.student_area_id
    })
  }
  
  if (filters.value.coach_id && filters.value.coach_id !== '') {
    filtered = filtered.filter(appt => appt.coach_id === filters.value.coach_id)
  }
  
  if (filters.value.coach_area_id && filters.value.coach_area_id !== '') {
    filtered = filtered.filter(appt => {
      const coach = persons.value.find(p => p.person_id === appt.coach_id)
      return coach && coach.area_id === filters.value.coach_area_id
    })
  }
  
  if (filters.value.date) {
    filtered = filtered.filter(appt => {
      return appt.appointment_date === filters.value.date
    })
  }
  
  if (filters.value.status && filters.value.status !== '') {
    filtered = filtered.filter(appt => appt.status === filters.value.status)
  }
  
  // 这里需要将筛选后的结果应用到表格显示
  filteredAppointments.value = filtered
  currentPage.value = 1 // 重置页码
}

const resetFilters = () => {
  // 重置筛选条件
  filters.value = { student_id: null, student_area_id: null, coach_id: null, coach_area_id: null, date: null, status: null }
  // 重新加载所有预约
  loadAppointments()
  currentPage.value = 1 // 重置页码
}

onMounted(() => {
  loadAppointments()
  loadPersons()
})
</script>

<style scoped>
.appointment-management {
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.data-table {
  width: 100%;
}

.data-table th,
.data-table td {
  padding: 8px 12px;
  line-height: 1.4;
  font-size: 14px;
}

.data-table td .el-button {
  padding: 4px 12px;
  font-size: 12px;
  margin-right: 4px;
}

.detail-content {
  padding: 20px 0;
}

.detail-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #eaeaea;
}

.detail-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
  padding-bottom: 0;
}

.detail-section h3 {
  margin-bottom: 12px;
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.detail-section p {
  margin-bottom: 8px;
  font-size: 14px;
  line-height: 1.5;
  text-align: left;
}

.detail-section strong {
  color: #606266;
  margin-right: 8px;
}
</style>

<template>
  <div class="appointment-management">
    <div class="page-header">
      <div>
        <h2 class="page-title">预约管理</h2>
        <p class="page-sub">共 {{ allAppointments.length }} 条预约 · 待确认 {{ pendingCount }} 条</p>
      </div>
      <el-button type="primary" @click="showAddDialog">添加预约</el-button>
    </div>
    
    <div class="filter-container">
      <div class="filter-item">
        <label>学员</label>
        <el-select v-model="filters.student_id" placeholder="选择学员" clearable filterable>
          <el-option label="全部" value="" />
          <el-option v-for="student in students" :key="student.student_id" :label="`${student.name} ${student.phone}`" :value="student.student_id" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>教练</label>
        <el-select v-model="filters.coach_id" placeholder="选择教练" clearable filterable>
          <el-option label="全部" value="" />
          <el-option v-for="coach in coaches" :key="coach.coach_id" :label="coach.name" :value="coach.coach_id" />
        </el-select>
      </div>
      <div class="filter-item">
        <label>预约日期</label>
        <el-date-picker
          v-model="filters.date"
          type="date"
          placeholder="选择日期"
          value-format="YYYY-MM-DD"
          clearable
          style="width: 100%;"
        />
      </div>
      <div class="filter-item">
        <label>状态</label>
        <el-select v-model="filters.status" placeholder="全部状态" clearable>
          <el-option label="全部" value="" />
          <el-option label="待确认" value="待确认" />
          <el-option label="已确认" value="已确认" />
          <el-option label="已完成" value="已完成" />
          <el-option label="已取消" value="已取消" />
        </el-select>
      </div>
      <div class="filter-actions">
        <el-button type="primary" @click="applyFilters">筛选</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </div>

    <div class="status-tabs">
      <button
        v-for="tab in statusTabs"
        :key="tab.label"
        type="button"
        class="status-tab"
        :class="{ active: (filters.status || '') === tab.value }"
        @click="selectStatus(tab.value)"
      >
        {{ tab.label }}
        <span class="count">{{ tab.count }}</span>
      </button>
    </div>
    
    <table class="data-table">
      <thead>
        <tr>
          <th style="width: 96px;">预约</th>
          <th>学员</th>
          <th style="width: 150px;">教练</th>
          <th style="width: 180px;">时段</th>
          <th style="width: 100px;">状态</th>
          <th style="width: 110px;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="appt in paginatedAppointments" :key="appt.appointment_id">
          <td>
            <div class="cell-main id">#{{ appt.appointment_id }}</div>
            <div class="cell-sub">{{ shortDate(appt.create_time) }} 创建</div>
          </td>
          <td>
            <div class="cell-main">{{ getStudentName(appt.student_id) }}</div>
            <div class="cell-sub">{{ getStudentPhone(appt.student_id) }} · {{ getStudentArea(appt.student_id) }}</div>
          </td>
          <td>
            <div class="cell-main">{{ getCoachName(appt.coach_id) }}</div>
            <div class="cell-sub">{{ getCoachArea(appt.coach_id) }}</div>
          </td>
          <td>
            <div class="cell-main">{{ appt.appointment_date }}</div>
            <div class="cell-sub">{{ appt.start_time }}:00 – {{ appt.end_time }}:00</div>
          </td>
          <td>
            <span class="status-pill" :class="getStatusClass(appt.status)"><i></i>{{ appt.status }}</span>
          </td>
          <td>
            <div class="row-actions">
              <el-button link type="primary" @click="showDetailDialog(appt)">详情</el-button>
              <el-dropdown trigger="click" @command="(command) => handleRowCommand(command, appt)">
                <el-button link class="more-btn">⋯</el-button>
                <template #dropdown>
                  <el-dropdown-menu>
                    <el-dropdown-item command="edit">编辑</el-dropdown-item>
                    <el-dropdown-item v-if="appt.status === '待确认'" command="confirm">确认</el-dropdown-item>
                    <el-dropdown-item v-if="appt.status !== '已取消'" command="cancel">取消预约</el-dropdown-item>
                    <el-dropdown-item command="delete" divided style="color: #f56c6c;">删除</el-dropdown-item>
                  </el-dropdown-menu>
                </template>
              </el-dropdown>
            </div>
          </td>
        </tr>
      </tbody>
    </table>

    <div class="table-footer">
      <span class="hint">共 {{ filteredAppointments.length }} 条</span>
      <el-pagination
        v-model:current-page="currentPage"
        v-model:page-size="pageSize"
        :page-sizes="[10, 20, 50, 100]"
        layout="sizes, prev, pager, next"
        :total="filteredAppointments.length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑预约' : '添加预约'" width="500px">
      <el-form :model="form" label-width="100px">
        <el-form-item label="学员">
          <el-select v-model="form.student_id">
            <el-option v-for="student in students" :key="student.student_id" :label="`${student.name} ${student.phone}`" :value="student.student_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="教练">
          <el-select v-model="form.coach_id">
            <el-option v-for="coach in coaches" :key="coach.coach_id" :label="coach.name" :value="coach.coach_id" />
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
          <p><strong>姓名：</strong>{{ getStudentName(currentAppointment.student_id) }}</p>
          <p><strong>手机号：</strong>{{ getStudentPhone(currentAppointment.student_id) }}</p>
          <p><strong>区域：</strong>{{ getStudentArea(currentAppointment.student_id) }}</p>
        </div>
        <div class="detail-section">
          <h3>教练信息</h3>
          <p><strong>姓名：</strong>{{ getCoachName(currentAppointment.coach_id) }}</p>
          <p><strong>手机号：</strong>{{ getCoachPhone(currentAppointment.coach_id) }}</p>
          <p><strong>区域：</strong>{{ getCoachArea(currentAppointment.coach_id) }}</p>
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
import { studentApi } from '../api/student'
import { coachApi } from '../api/coach'
import { areaApi } from '../api/area'
import { createStudentNameGetter } from '../composables/useStudentName'

const appointments = ref([])
const students = ref([])
const coaches = ref([])
const areas = ref([])
const dialogVisible = ref(false)
const detailDialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const currentAppointment = ref(null)
const form = ref({ student_id: null, coach_id: null, appointment_date: '', start_time: 9, end_time: 11, status: '待确认' })
const filters = ref({ student_id: null, coach_id: null, date: null, status: null })

// 分页
const currentPage = ref(1)
const pageSize = ref(20)
const allAppointments = ref([])
const filteredAppointments = ref([])

const statusTabs = computed(() => {
  const counts = { '待确认': 0, '已确认': 0, '已完成': 0, '已取消': 0 }
  allAppointments.value.forEach(item => {
    if (counts[item.status] !== undefined) counts[item.status] += 1
  })
  return [
    { value: '', label: '全部', count: allAppointments.value.length },
    { value: '待确认', label: '待确认', count: counts['待确认'] },
    { value: '已确认', label: '已确认', count: counts['已确认'] },
    { value: '已完成', label: '已完成', count: counts['已完成'] },
    { value: '已取消', label: '已取消', count: counts['已取消'] }
  ]
})

const pendingCount = computed(() => statusTabs.value[1].count)

const selectStatus = (value) => {
  filters.value.status = value || null
  applyFilters()
}

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
    const [studentList, coachList, areaList] = await Promise.all([
      studentApi.getAll(),
      coachApi.getAll(),
      areaApi.getAll()
    ])
    students.value = studentList || []
    coaches.value = coachList || []
    areas.value = areaList || []
  } catch (error) {
    ElMessage.error('加载人员列表失败')
  }
}

const getStudentName = createStudentNameGetter(students)

const getStudentPhone = (id) => {
  const student = students.value.find(s => s.student_id === id)
  return student ? student.phone : '-'
}

const getStudentArea = (id) => {
  const student = students.value.find(s => s.student_id === id)
  if (!student || !student.area_id) return '-'
  const area = areas.value.find(a => a.area_id === student.area_id)
  return area ? area.name : '-'
}

const getCoachName = (id) => {
  const coach = coaches.value.find(c => c.coach_id === id)
  return coach ? coach.name : id
}

const getCoachPhone = (id) => {
  const coach = coaches.value.find(c => c.coach_id === id)
  return coach ? coach.phone : '-'
}

const getCoachArea = (id) => {
  const coach = coaches.value.find(c => c.coach_id === id)
  if (!coach || !coach.area_id) return '-'
  const area = areas.value.find(a => a.area_id === coach.area_id)
  return area ? area.name : '-'
}

const getStatusType = (status) => {
  if (status === '待确认') return 'warning'
  if (status === '已确认') return 'success'
  return 'info'
}

const getStatusClass = (status) => {
  if (status === '待确认') return 'wait'
  if (status === '已确认' || status === '已完成') return 'ok'
  return 'off'
}

const shortDate = (value) => {
  if (!value) return '-'
  return String(value).slice(5, 10)
}

const handleRowCommand = (command, row) => {
  if (command === 'edit') showEditDialog(row)
  if (command === 'confirm') updateStatus(row, '已确认')
  if (command === 'cancel') updateStatus(row, '已取消')
  if (command === 'delete') deleteAppointment(row.appointment_id)
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

  if (filters.value.coach_id && filters.value.coach_id !== '') {
    filtered = filtered.filter(appt => appt.coach_id === filters.value.coach_id)
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
  filters.value = { student_id: null, coach_id: null, date: null, status: null }
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
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.appointment-management .page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--app-text);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.page-sub {
  margin: 4px 0 0;
  font-size: 12px;
  color: var(--app-text-muted);
}

.filter-container {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
  align-items: flex-end;
  margin-top: 16px;
}

.filter-item {
  flex: 1 1 160px;
  min-width: 140px;
}

.filter-item label {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--app-text-muted);
}

.filter-item :deep(.el-select) {
  width: 100%;
}

.filter-actions {
  display: flex;
  gap: 8px;
  margin-left: auto;
}

.status-tabs {
  display: flex;
  align-items: center;
  gap: 4px;
  margin-top: 16px;
  border-bottom: 1px solid var(--app-border);
}

.status-tab {
  appearance: none;
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 10px;
  border: 0;
  border-bottom: 2px solid transparent;
  background: transparent;
  font-family: inherit;
  font-size: 13px;
  color: var(--app-text-muted);
  cursor: pointer;
}

.status-tab .count {
  padding: 1px 7px;
  border-radius: 999px;
  font-size: 11px;
  background: #f3f4f6;
  color: var(--app-text-muted);
}

.status-tab.active {
  color: var(--app-primary-text);
  border-bottom-color: var(--app-primary);
  font-weight: 600;
}

.status-tab.active .count {
  background: var(--app-primary-soft);
  color: var(--app-primary-text);
}

.data-table {
  width: 100%;
}

.cell-main {
  font-size: 14px;
  line-height: 1.35;
  color: var(--app-text);
}

.cell-main.id {
  color: var(--app-text-muted);
  font-variant-numeric: tabular-nums;
}

.cell-sub {
  margin-top: 2px;
  font-size: 12px;
  line-height: 1.3;
  color: var(--app-text-muted);
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 9px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 500;
}

.status-pill i {
  display: block;
  width: 5px;
  height: 5px;
  border-radius: 50%;
}

.status-pill.wait {
  background: #fef3c7;
  color: #b45309;
}

.status-pill.wait i {
  background: #d97706;
}

.status-pill.ok {
  background: #dcfce7;
  color: #15803d;
}

.status-pill.ok i {
  background: #16a34a;
}

.status-pill.off {
  background: #f3f4f6;
  color: #6b7280;
}

.status-pill.off i {
  background: #9ca3af;
}

.row-actions {
  display: flex;
  align-items: center;
  gap: 6px;
}

.row-actions :deep(.el-button + .el-button) {
  margin-left: 0;
}

.more-btn {
  padding: 0 2px;
  font-size: 16px;
  color: var(--app-text-muted);
}

.table-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 12px;
}

.hint {
  font-size: 12px;
  color: var(--app-text-muted);
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

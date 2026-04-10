<template>
  <div class="recharge-management">
    <h1>充值管理</h1>
    
    <!-- 添加充值按钮 -->
    <div style="margin-bottom: 20px;">
      <el-button type="primary" @click="openDialog">添加充值</el-button>
    </div>
    
    <!-- 充值列表 -->
    <table class="custom-table">
      <thead>
        <tr>
          <th>ID</th>
          <th>学员</th>
          <th>充值金额</th>
          <th>课程数量</th>
          <th>充值时间</th>
          <th>操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="recharge in (recharges || [])" :key="recharge.recharge_id">
          <td>{{ recharge.recharge_id }}</td>
          <td>{{ getStudentName(recharge.student_id) }}</td>
          <td>{{ recharge.amount }}</td>
          <td>{{ recharge.course_count }}</td>
          <td>{{ recharge.recharge_time }}</td>
          <td>
            <el-button type="primary" size="small" @click="editRecharge(recharge)">编辑</el-button>
            <el-button type="danger" size="small" @click="deleteRecharge(recharge.recharge_id)">删除</el-button>
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
        :total="(recharges || []).length"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>
    
    <!-- 充值对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="isEdit ? '编辑充值' : '添加充值'"
      width="500px"
    >
      <el-form :model="form" label-width="80px">
        <el-form-item label="学员">
          <el-select v-model="form.student_id" placeholder="请选择学员" style="width: 100%;" filterable>
            <el-option
              v-for="student in students"
              :key="student.person_id"
              :label="`${student.name} - ${getAreaName(student.area_id)} - ${student.phone}`"
              :value="student.person_id"
            />
          </el-select>
        </el-form-item>
        <el-form-item label="充值金额">
          <el-input v-model.number="form.amount" placeholder="请输入充值金额" />
        </el-form-item>
        <el-form-item label="课程数量">
          <el-input v-model.number="form.course_count" placeholder="请输入课程数量" />
        </el-form-item>
        <el-form-item label="充值时间">
          <el-date-picker
            v-model="form.recharge_time"
            type="datetime"
            placeholder="选择日期时间"
            style="width: 100%;"
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="saveRecharge">确定</el-button>
        </span>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import rechargeApi from '../api/recharge'
import personApi from '../api/person'
import areaApi from '../api/area'

const recharges = ref([])
const students = ref([])
const areas = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const currentPage = ref(1)
const pageSize = ref(20)

const form = ref({
  student_id: '',
  amount: '',
  course_count: '',
  recharge_time: ''
})

const paginatedRecharges = computed(() => {
  if (!recharges.value) return []
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return recharges.value.slice(start, end)
})

const loadRecharges = async () => {
  try {
    const response = await rechargeApi.getAll()
    recharges.value = response || []
  } catch (error) {
    ElMessage.error('获取充值记录失败')
    recharges.value = []
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

const loadStudents = async () => {
  try {
    const response = await personApi.getAll()
    students.value = (response || []).filter(person => person.type === '学员')
  } catch (error) {
    ElMessage.error('获取学员列表失败')
    students.value = []
  }
}

const getAreaName = (areaId) => {
  if (!areas.value) return '未知区域'
  const area = areas.value.find(a => a.area_id === areaId)
  return area ? area.name : '未知区域'
}

const getStudentName = (studentId) => {
  if (!students.value) return '未知学员'
  const student = students.value.find(s => s.person_id === studentId)
  return student ? student.name : '未知学员'
}

const openDialog = () => {
  isEdit.value = false
  currentId.value = null
  form.value = {
    student_id: '',
    amount: '',
    course_count: '',
    recharge_time: new Date()
  }
  dialogVisible.value = true
}

const editRecharge = (recharge) => {
  isEdit.value = true
  currentId.value = recharge.recharge_id
  form.value = {
    student_id: recharge.student_id,
    amount: recharge.amount,
    course_count: recharge.course_count,
    recharge_time: new Date(recharge.recharge_time)
  }
  dialogVisible.value = true
}

const saveRecharge = async () => {
  try {
    if (!form.value.student_id) {
      ElMessage.error('请选择学员')
      return
    }
    if (!form.value.amount || form.value.amount <= 0) {
      ElMessage.error('请输入有效的充值金额')
      return
    }
    if (!form.value.course_count || form.value.course_count <= 0) {
      ElMessage.error('请输入有效的课程数量')
      return
    }
    if (!form.value.recharge_time) {
      ElMessage.error('请选择充值时间')
      return
    }
    
    const rechargeData = {
      ...form.value,
      recharge_time: form.value.recharge_time.toISOString().slice(0, 19).replace('T', ' ')
    }
    
    if (isEdit.value) {
      await rechargeApi.update(currentId.value, rechargeData)
      ElMessage.success('更新成功')
    } else {
      await rechargeApi.create(rechargeData)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadRecharges()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteRecharge = async (rechargeId) => {
  try {
    await rechargeApi.delete(rechargeId)
    ElMessage.success('删除成功')
    loadRecharges()
  } catch (error) {
    ElMessage.error('删除失败')
  }
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

const handleCurrentChange = (current) => {
  currentPage.value = current
}

onMounted(() => {
  loadRecharges()
  loadStudents()
  loadAreas()
})
</script>

<style scoped>
.recharge-management {
  padding: 20px;
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

.dialog-footer {
  width: 100%;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
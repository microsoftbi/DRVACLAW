<template>
  <div class="student-management">
    <h2>学员管理</h2>
    <el-button type="primary" @click="showAddDialog">添加学员</el-button>

    <table class="data-table" style="width: 100%; margin-top: 20px; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="width: 90px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">学员ID</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">姓名</th>
          <th style="width: 140px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">手机号</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">区域</th>
          <th style="width: 100px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">驾龄（年）</th>
          <th style="text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">备注</th>
          <th style="width: 180px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">注册时间</th>
          <th style="width: 150px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="student in students" :key="student.student_id">
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ student.student_id }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ student.name }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ student.phone }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ getAreaName(student.area_id) }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ student.driving_years }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ student.remark || '-' }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ student.register_time }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showEditDialog(student)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteStudent(student.student_id)">删除</el-button>
          </td>
        </tr>
      </tbody>
    </table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑学员' : '添加学员'">
      <el-form :model="form" label-width="90px">
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="区域">
          <el-select v-model="form.area_id" clearable style="width: 100%;">
            <el-option v-for="area in areas" :key="area.area_id" :label="area.name" :value="area.area_id" />
          </el-select>
        </el-form-item>
        <el-form-item label="驾龄（年）">
          <el-input-number v-model="form.driving_years" :min="0" :max="60" style="width: 100%;" />
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="form.remark" type="textarea" :rows="3" placeholder="请输入备注" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveStudent">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { studentApi } from '../api/student'
import { areaApi } from '../api/area'

const students = ref([])
const areas = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const form = ref({ name: '', phone: '', area_id: null, driving_years: 0, remark: '' })

const loadStudents = async () => {
  try {
    students.value = await studentApi.getAll()
  } catch (error) {
    ElMessage.error('加载学员列表失败')
  }
}

const loadAreas = async () => {
  try {
    areas.value = await areaApi.getAll()
  } catch (error) {
    ElMessage.error('加载区域列表失败')
  }
}

const getAreaName = (areaId) => {
  const area = areas.value.find(a => a.area_id === areaId)
  return area ? area.name : '-'
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { name: '', phone: '', area_id: null, driving_years: 0, remark: '' }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentId.value = row.student_id
  form.value = {
    name: row.name,
    phone: row.phone,
    area_id: row.area_id,
    driving_years: row.driving_years,
    remark: row.remark || ''
  }
  dialogVisible.value = true
}

const saveStudent = async () => {
  try {
    if (!form.value.name || !form.value.name.trim()) {
      ElMessage.error('请输入姓名')
      return
    }
    if (!form.value.phone || !form.value.phone.trim()) {
      ElMessage.error('请输入手机号')
      return
    }

    if (isEdit.value) {
      await studentApi.update(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await studentApi.create(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadStudents()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteStudent = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个学员吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await studentApi.delete(id)
    ElMessage.success('删除成功')
    loadStudents()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadStudents()
  loadAreas()
})
</script>

<style scoped>
.student-management {
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.data-table {
  width: 100%;
}
</style>

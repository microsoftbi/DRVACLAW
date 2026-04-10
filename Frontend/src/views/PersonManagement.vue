<template>
  <div class="person-management">
    <h2>人员管理</h2>
    <el-radio-group v-model="personType" @change="loadPersons" style="margin-bottom: 20px;">
      <el-radio-button value="all">全部</el-radio-button>
      <el-radio-button value="学员">学员</el-radio-button>
      <el-radio-button value="教练">教练</el-radio-button>
    </el-radio-group>
    <el-button type="primary" @click="showAddDialog">添加人员</el-button>
    
    <table class="data-table" style="width: 100%; margin-top: 20px; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="width: 100px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">人员ID</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">姓名</th>
          <th style="width: 140px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">手机号</th>
          <th style="width: 100px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">类型</th>
          <th style="width: 180px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">注册时间</th>
          <th style="width: 200px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="person in persons" :key="person.person_id">
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ person.person_id }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ person.name }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ person.phone }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ person.type }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ person.register_time }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showEditDialog(person)">编辑</el-button>
            <el-button size="small" type="danger" @click="deletePerson(person.person_id)">删除</el-button>
          </td>
        </tr>
      </tbody>
    </table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑人员' : '添加人员'">
      <el-form :model="form" label-width="80px">
        <el-form-item label="姓名">
          <el-input v-model="form.name" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" />
        </el-form-item>
        <el-form-item label="类型" v-if="!isEdit">
          <el-select v-model="form.type">
            <el-option label="学员" value="学员" />
            <el-option label="教练" value="教练" />
          </el-select>
        </el-form-item>
        <el-form-item label="区域">
          <el-select v-model="form.area_id" clearable>
            <el-option v-for="area in areas" :key="area.area_id" :label="area.name" :value="area.area_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="savePerson">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { personApi } from '../api/person'
import { areaApi } from '../api/area'

const persons = ref([])
const areas = ref([])
const personType = ref('all')
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const form = ref({ name: '', phone: '', type: '学员', area_id: null })

const loadPersons = async () => {
  try {
    if (personType.value === 'all') {
      persons.value = await personApi.getAll()
    } else if (personType.value === '学员') {
      persons.value = await personApi.getStudents()
    } else if (personType.value === '教练') {
      persons.value = await personApi.getCoaches()
    }
  } catch (error) {
    ElMessage.error('加载人员列表失败')
  }
}

const loadAreas = async () => {
  try {
    areas.value = await areaApi.getAll()
  } catch (error) {
    ElMessage.error('加载区域列表失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { name: '', phone: '', type: '学员', area_id: null }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentId.value = row.person_id
  form.value = { name: row.name, phone: row.phone, area_id: row.area_id }
  dialogVisible.value = true
}

const savePerson = async () => {
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
      await personApi.update(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await personApi.create(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadPersons()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deletePerson = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个人员吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await personApi.delete(id)
    ElMessage.success('删除成功')
    loadPersons()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadPersons()
  loadAreas()
})
</script>

<style scoped>
.person-management {
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.data-table {
  width: 100%;
}
</style>

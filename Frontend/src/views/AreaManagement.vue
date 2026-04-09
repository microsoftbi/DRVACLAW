<template>
  <div class="area-management">
    <h2>区域管理</h2>
    <el-button type="primary" @click="showAddDialog">添加区域</el-button>
    
    <table class="data-table" style="width: 100%; margin-top: 20px; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">区域ID</th>
          <th style="text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">区域名称</th>
          <th style="width: 200px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="area in areas" :key="area.area_id">
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ area.area_id }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ area.name }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showEditDialog(area)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteArea(area.area_id)">删除</el-button>
          </td>
        </tr>
      </tbody>
    </table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑区域' : '添加区域'">
      <el-form :model="form" label-width="80px">
        <el-form-item label="区域名称">
          <el-input v-model="form.name" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveArea">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { areaApi } from '../api/area'

const areas = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const form = ref({ name: '' })

const loadAreas = async () => {
  try {
    areas.value = await areaApi.getAll()
  } catch (error) {
    ElMessage.error('加载区域列表失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { name: '' }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentId.value = row.area_id
  form.value = { name: row.name }
  dialogVisible.value = true
}

const saveArea = async () => {
  try {
    if (isEdit.value) {
      await areaApi.update(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await areaApi.create(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadAreas()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteArea = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个区域吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await areaApi.delete(id)
    ElMessage.success('删除成功')
    loadAreas()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadAreas()
})
</script>

<style scoped>
.area-management {
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.data-table {
  width: 100%;
}
</style>

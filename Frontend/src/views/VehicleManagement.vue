<template>
  <div class="vehicle-management">
    <h2>车辆管理</h2>
    <el-button type="primary" @click="showAddDialog">添加车辆</el-button>

    <table class="data-table" style="width: 100%; margin-top: 20px; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="width: 90px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">车辆ID</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">车型</th>
          <th style="width: 160px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">品牌</th>
          <th style="width: 180px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">型号</th>
          <th style="width: 200px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">创建时间</th>
          <th style="width: 150px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="vehicle in vehicles" :key="vehicle.vehicle_id">
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ vehicle.vehicle_id }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ vehicle.vehicle_type }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ vehicle.brand }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ vehicle.model }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ vehicle.create_time }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showEditDialog(vehicle)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteVehicle(vehicle.vehicle_id)">删除</el-button>
          </td>
        </tr>
      </tbody>
    </table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑车辆' : '添加车辆'">
      <el-form :model="form" label-width="90px">
        <el-form-item label="车型">
          <el-select v-model="form.vehicle_type" style="width: 100%;">
            <el-option label="SUV" value="SUV" />
            <el-option label="轿车" value="轿车" />
          </el-select>
        </el-form-item>
        <el-form-item label="品牌">
          <el-input v-model="form.brand" placeholder="如：丰田" />
        </el-form-item>
        <el-form-item label="型号">
          <el-input v-model="form.model" placeholder="如：汉兰达" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveVehicle">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { vehicleApi } from '../api/vehicle'

const vehicles = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const form = ref({ vehicle_type: 'SUV', brand: '', model: '' })

const loadVehicles = async () => {
  try {
    vehicles.value = await vehicleApi.getAll()
  } catch (error) {
    ElMessage.error('加载车辆列表失败')
  }
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { vehicle_type: 'SUV', brand: '', model: '' }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentId.value = row.vehicle_id
  form.value = {
    vehicle_type: row.vehicle_type,
    brand: row.brand,
    model: row.model
  }
  dialogVisible.value = true
}

const saveVehicle = async () => {
  try {
    if (!form.value.brand || !form.value.brand.trim()) {
      ElMessage.error('请输入品牌')
      return
    }
    if (!form.value.model || !form.value.model.trim()) {
      ElMessage.error('请输入型号')
      return
    }

    if (isEdit.value) {
      await vehicleApi.update(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await vehicleApi.create(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadVehicles()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteVehicle = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这辆车吗？删除后教练的关联也会一并解除。', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await vehicleApi.delete(id)
    ElMessage.success('删除成功')
    loadVehicles()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadVehicles()
})
</script>

<style scoped>
.vehicle-management {
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.data-table {
  width: 100%;
}
</style>

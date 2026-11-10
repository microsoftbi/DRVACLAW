<template>
  <div class="coach-management">
    <h2>教练管理</h2>
    <el-button type="primary" @click="showAddDialog">添加教练</el-button>

    <table class="data-table" style="width: 100%; margin-top: 20px; border-collapse: collapse;">
      <thead>
        <tr>
          <th style="width: 90px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">教练ID</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">姓名</th>
          <th style="width: 140px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">手机号</th>
          <th style="width: 120px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">区域</th>
          <th style="text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">关联车辆</th>
          <th style="width: 180px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">注册时间</th>
          <th style="width: 150px; text-align: left; padding: 12px; border: 1px solid #ddd; background-color: #f5f7fa;">操作</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="coach in coaches" :key="coach.coach_id">
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ coach.coach_id }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ coach.name }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ coach.phone }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ getAreaName(coach.area_id) }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <template v-if="coach.vehicle_ids && coach.vehicle_ids.length">
              <el-tag v-for="vehicleId in coach.vehicle_ids" :key="vehicleId" style="margin-right: 6px;">
                {{ getVehicleLabel(vehicleId) }}
              </el-tag>
            </template>
            <span v-else>-</span>
          </td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">{{ coach.register_time }}</td>
          <td style="text-align: left; padding: 12px; border: 1px solid #ddd;">
            <el-button size="small" @click="showEditDialog(coach)">编辑</el-button>
            <el-button size="small" type="danger" @click="deleteCoach(coach.coach_id)">删除</el-button>
          </td>
        </tr>
      </tbody>
    </table>

    <el-dialog v-model="dialogVisible" :title="isEdit ? '编辑教练' : '添加教练'">
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
        <el-form-item label="关联车辆">
          <el-select v-model="form.vehicle_ids" multiple filterable clearable style="width: 100%;" placeholder="可选择多辆车">
            <el-option
              v-for="vehicle in vehicles"
              :key="vehicle.vehicle_id"
              :label="`${vehicle.brand} ${vehicle.model}（${vehicle.vehicle_type}）`"
              :value="vehicle.vehicle_id"
            />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="saveCoach">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { coachApi } from '../api/coach'
import { vehicleApi } from '../api/vehicle'
import { areaApi } from '../api/area'

const coaches = ref([])
const vehicles = ref([])
const areas = ref([])
const dialogVisible = ref(false)
const isEdit = ref(false)
const currentId = ref(null)
const form = ref({ name: '', phone: '', area_id: null, vehicle_ids: [] })

const loadCoaches = async () => {
  try {
    coaches.value = await coachApi.getAll()
  } catch (error) {
    ElMessage.error('加载教练列表失败')
  }
}

const loadVehicles = async () => {
  try {
    vehicles.value = await vehicleApi.getAll()
  } catch (error) {
    ElMessage.error('加载车辆列表失败')
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

const getVehicleLabel = (vehicleId) => {
  const vehicle = vehicles.value.find(v => v.vehicle_id === vehicleId)
  return vehicle ? `${vehicle.brand} ${vehicle.model}` : `车辆${vehicleId}`
}

const showAddDialog = () => {
  isEdit.value = false
  form.value = { name: '', phone: '', area_id: null, vehicle_ids: [] }
  dialogVisible.value = true
}

const showEditDialog = (row) => {
  isEdit.value = true
  currentId.value = row.coach_id
  form.value = {
    name: row.name,
    phone: row.phone,
    area_id: row.area_id,
    vehicle_ids: [...(row.vehicle_ids || [])]
  }
  dialogVisible.value = true
}

const saveCoach = async () => {
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
      await coachApi.update(currentId.value, form.value)
      ElMessage.success('更新成功')
    } else {
      await coachApi.create(form.value)
      ElMessage.success('添加成功')
    }
    dialogVisible.value = false
    loadCoaches()
  } catch (error) {
    ElMessage.error('操作失败')
  }
}

const deleteCoach = async (id) => {
  try {
    await ElMessageBox.confirm('确定要删除这个教练吗？', '提示', {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning'
    })
    await coachApi.delete(id)
    ElMessage.success('删除成功')
    loadCoaches()
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error('删除失败')
    }
  }
}

onMounted(() => {
  loadCoaches()
  loadVehicles()
  loadAreas()
})
</script>

<style scoped>
.coach-management {
  padding: 20px;
  width: 100%;
  height: 100%;
  box-sizing: border-box;
}

.data-table {
  width: 100%;
}
</style>

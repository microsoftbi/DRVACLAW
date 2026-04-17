<template>
  <div class="pivot-analysis-container">
    <h2>透视分析</h2>
    <div class="pivot-layout">
      <div class="fields-panel">
        <h3>字段列表</h3>
        <div class="field-section">
          <div class="section-title">课程</div>
          <div class="subsection">
            <div class="subsection-title">度量值</div>
            <div
              v-for="measure in measures"
              :key="measure.id"
              class="field-item measure-item"
              draggable="true"
              @dragstart="handleDragStart($event, measure, 'measure')"
            >
              <el-icon><DataLine /></el-icon>
              {{ measure.name }}
            </div>
          </div>
          <div class="subsection">
            <div class="subsection-title">维度</div>
            <div
              v-for="dimension in dimensions"
              :key="dimension.id"
              class="field-item dimension-item"
              draggable="true"
              @dragstart="handleDragStart($event, dimension, 'dimension')"
            >
              <el-icon><Grid /></el-icon>
              {{ dimension.name }}
            </div>
          </div>
        </div>
      </div>
      
      <div class="pivot-workspace">
        <div class="filter-panel" v-if="filters.length > 0">
          <div class="filter-panel-title">筛选条件</div>
          <div class="filter-items">
            <div
              v-for="(filter, index) in filters"
              :key="`filter-${index}`"
              class="filter-item"
            >
              <div class="filter-label">
                <span>{{ filter.name }}</span>
                <el-icon class="remove-icon" @click="removeFilter(index)"><Close /></el-icon>
              </div>
              <el-select
                v-model="filter.selectedValues"
                multiple
                filterable
                collapse-tags
                collapse-tags-tooltip
                placeholder="请选择"
                style="width: 100%"
                @change="generatePivotTable"
              >
                <el-option
                  v-for="value in getFilterValues(filter.field)"
                  :key="value"
                  :label="value"
                  :value="value"
                />
              </el-select>
            </div>
          </div>
        </div>
        
        <div class="drop-zones">
          <div class="drop-zone">
            <div class="zone-title">筛选</div>
            <div
              class="zone-content"
              @dragover.prevent
              @drop="handleDrop($event, 'filters')"
            >
              <div
                v-for="(item, index) in filters"
                :key="`filter-${index}`"
                class="dropped-item dimension-item"
              >
                {{ item.name }}
                <el-icon class="remove-icon" @click="removeItem('filters', index)"><Close /></el-icon>
              </div>
              <div v-if="filters.length === 0" class="placeholder">拖入维度</div>
            </div>
          </div>
          <div class="drop-zone">
            <div class="zone-title">值</div>
            <div
              class="zone-content"
              @dragover.prevent
              @drop="handleDrop($event, 'values')"
            >
              <div
                v-for="(item, index) in values"
                :key="`value-${index}`"
                class="dropped-item measure-item"
              >
                {{ item.name }}
                <el-icon class="remove-icon" @click="removeItem('values', index)"><Close /></el-icon>
              </div>
              <div v-if="values.length === 0" class="placeholder">拖入度量值</div>
            </div>
          </div>
          <div class="drop-zone">
            <div class="zone-title">行</div>
            <div
              class="zone-content"
              @dragover.prevent
              @drop="handleDrop($event, 'rows')"
            >
              <div
                v-for="(item, index) in rows"
                :key="`row-${index}`"
                class="dropped-item dimension-item"
              >
                {{ item.name }}
                <el-icon class="remove-icon" @click="removeItem('rows', index)"><Close /></el-icon>
              </div>
              <div v-if="rows.length === 0" class="placeholder">拖入维度</div>
            </div>
          </div>
          <div class="drop-zone">
            <div class="zone-title">列</div>
            <div
              class="zone-content"
              @dragover.prevent
              @drop="handleDrop($event, 'columns')"
            >
              <div
                v-for="(item, index) in columns"
                :key="`col-${index}`"
                class="dropped-item dimension-item"
              >
                {{ item.name }}
                <el-icon class="remove-icon" @click="removeItem('columns', index)"><Close /></el-icon>
              </div>
              <div v-if="columns.length === 0" class="placeholder">拖入维度</div>
            </div>
          </div>
        </div>
        
        <div class="pivot-table-container">
          <div class="table-actions">
            <el-button type="primary" @click="generatePivotTable" :disabled="values.length === 0">
              生成透视表
            </el-button>
            <el-button @click="clearAll">清空</el-button>
            <el-button type="success" @click="exportToExcel" :disabled="tableData.length === 0">
              <el-icon><Download /></el-icon>
              导出Excel
            </el-button>
          </div>
          <div class="table-wrapper" v-loading="loading">
            <el-table
              v-if="tableData.length > 0"
              :data="tableData"
              border
              stripe
              style="width: 100%"
              :span-method="tableSpanMethod"
            >
              <el-table-column
                v-for="col in tableColumns"
                :key="col.prop"
                :prop="col.prop"
                :label="col.label"
                :align="col.align || 'center'"
              />
            </el-table>
            <div v-else class="empty-table">
              <el-empty description="请拖入字段并点击生成透视表" />
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { DataLine, Grid, Close, Download } from '@element-plus/icons-vue'
import { appointmentApi } from '../api/appointment'
import { personApi } from '../api/person'
import * as XLSX from 'xlsx'
import { saveAs } from 'file-saver'

const measures = ref([
  { id: 'course_count', name: '课程数量', field: 'count' },
  { id: 'course_duration', name: '课程时长', field: 'duration' }
])

const dimensions = ref([
  { id: 'student', name: '学员', field: 'student_name' },
  { id: 'coach', name: '教练', field: 'coach_name' },
  { id: 'status', name: '状态', field: 'status' },
  { id: 'date', name: '日期', field: 'appointment_date' }
])

const values = ref([])
const rows = ref([])
const columns = ref([])
const filters = ref([])
const tableData = ref([])
const tableColumns = ref([])
const loading = ref(false)
const appointments = ref([])
const persons = ref([])
const enrichedAppointmentsCache = ref([])

const draggedItem = ref(null)
const draggedType = ref(null)

const handleDragStart = (event, item, type) => {
  draggedItem.value = item
  draggedType.value = type
  event.dataTransfer.effectAllowed = 'move'
}

const handleDrop = (event, zone) => {
  event.preventDefault()
  if (!draggedItem.value) return
  
  if (zone === 'values') {
    if (draggedType.value === 'measure') {
      if (!values.value.find(v => v.id === draggedItem.value.id)) {
        values.value.push({ ...draggedItem.value })
      }
    }
  } else {
    if (draggedType.value === 'dimension') {
      let targetArray
      if (zone === 'filters') {
        targetArray = filters
      } else if (zone === 'rows') {
        targetArray = rows
      } else {
        targetArray = columns
      }
      
      if (!targetArray.value.find(v => v.id === draggedItem.value.id)) {
        if (zone === 'filters') {
          filters.value.push({ ...draggedItem.value, selectedValues: [] })
        } else {
          targetArray.value.push({ ...draggedItem.value })
        }
      }
    }
  }
  
  draggedItem.value = null
  draggedType.value = null
}

const removeItem = (zone, index) => {
  let targetArray
  if (zone === 'filters') {
    targetArray = filters
  } else if (zone === 'values') {
    targetArray = values
  } else if (zone === 'rows') {
    targetArray = rows
  } else {
    targetArray = columns
  }
  targetArray.value.splice(index, 1)
}

const removeFilter = (index) => {
  filters.value.splice(index, 1)
  if (tableData.value.length > 0) {
    generatePivotTable()
  }
}

const getFilterValues = (field) => {
  return [...new Set(enrichedAppointmentsCache.value.map(d => d[field]))].sort()
}

const clearAll = () => {
  values.value = []
  rows.value = []
  columns.value = []
  filters.value = []
  tableData.value = []
  tableColumns.value = []
}

const loadData = async () => {
  try {
    [appointments.value, persons.value] = await Promise.all([
      appointmentApi.getAll(),
      personApi.getAll()
    ])
    prepareEnrichedAppointments()
  } catch (error) {
    console.error('加载数据失败:', error)
  }
}

const prepareEnrichedAppointments = () => {
  enrichedAppointmentsCache.value = appointments.value.map(apt => {
    const student = persons.value.find(p => p.person_id === apt.student_id)
    const coach = persons.value.find(p => p.person_id === apt.coach_id)
    
    const startTime = typeof apt.start_time === 'number' ? apt.start_time : parseInt(apt.start_time)
    const endTime = typeof apt.end_time === 'number' ? apt.end_time : parseInt(apt.end_time)
    const duration = endTime - startTime
    
    return {
      ...apt,
      student_name: student ? student.name : '未知',
      coach_name: coach ? coach.name : '未知',
      duration: duration
    }
  })
}

const applyFilters = (data) => {
  let filteredData = [...data]
  
  filters.value.forEach(filter => {
    if (filter.selectedValues && filter.selectedValues.length > 0) {
      filteredData = filteredData.filter(item => 
        filter.selectedValues.includes(item[filter.field])
      )
    }
  })
  
  return filteredData
}

const generatePivotTable = () => {
  if (values.value.length === 0) return
  
  loading.value = true
  
  setTimeout(() => {
    try {
      const filteredData = applyFilters(enrichedAppointmentsCache.value)
      const result = buildPivotTable(filteredData)
      tableData.value = result.data
      tableColumns.value = result.columns
    } catch (error) {
      console.error('生成透视表失败:', error)
    } finally {
      loading.value = false
    }
  }, 300)
}

const buildPivotTable = (data) => {
  const rowFields = rows.value.map(r => r.field)
  const colFields = columns.value.map(c => c.field)
  const valueFields = values.value.map(v => v)
  
  const colValuesMap = {}
  colFields.forEach(field => {
    colValuesMap[field] = [...new Set(data.map(d => d[field]))].sort()
  })
  
  const colCombinations = generateCombinations(colFields, colValuesMap)
  
  const rowGroups = {}
  data.forEach(item => {
    const rowKey = rowFields.map(f => item[f]).join('|')
    if (!rowGroups[rowKey]) {
      rowGroups[rowKey] = {
        rowValues: rowFields.map(f => item[f]),
        colData: {}
      }
    }
    
    const colKey = colFields.map(f => item[f]).join('|')
    if (!rowGroups[rowKey].colData[colKey]) {
      rowGroups[rowKey].colData[colKey] = { count: 0, duration: 0 }
    }
    rowGroups[rowKey].colData[colKey].count += 1
    rowGroups[rowKey].colData[colKey].duration += item.duration
  })
  
  const tableColumns = []
  rowFields.forEach((field, idx) => {
    const dim = dimensions.value.find(d => d.field === field)
    tableColumns.push({
      prop: `row_${idx}`,
      label: dim ? dim.name : field,
      align: 'left'
    })
  })
  
  colCombinations.forEach(colComb => {
    valueFields.forEach(vf => {
      tableColumns.push({
        prop: `col_${colComb.key}_${vf.field}`,
        label: colFields.length > 0 
          ? `${colComb.labels.join(' / ')} - ${vf.name}`
          : vf.name,
        align: 'center'
      })
    })
  })
  
  const tableData = []
  Object.values(rowGroups).forEach(group => {
    const row = {}
    rowFields.forEach((_, idx) => {
      row[`row_${idx}`] = group.rowValues[idx]
    })
    
    colCombinations.forEach(colComb => {
      const colData = group.colData[colComb.key] || { count: 0, duration: 0 }
      valueFields.forEach(vf => {
        row[`col_${colComb.key}_${vf.field}`] = colData[vf.field]
      })
    })
    
    tableData.push(row)
  })
  
  return { data: tableData, columns: tableColumns }
}

const generateCombinations = (fields, valuesMap) => {
  if (fields.length === 0) {
    return [{ key: '', labels: [] }]
  }
  
  const combinations = []
  const firstField = fields[0]
  const remainingFields = fields.slice(1)
  const subCombinations = generateCombinations(remainingFields, valuesMap)
  
  valuesMap[firstField].forEach(value => {
    subCombinations.forEach(sub => {
      combinations.push({
        key: [value, sub.key].filter(k => k).join('|'),
        labels: [value, ...sub.labels].filter(l => l)
      })
    })
  })
  
  return combinations
}

const tableSpanMethod = ({ row, column, rowIndex, columnIndex }) => {
  return { colspan: 1, rowspan: 1 }
}

const exportToExcel = () => {
  if (tableData.value.length === 0) return
  
  try {
    const headers = tableColumns.value.map(col => col.label)
    const excelData = tableData.value.map(row => {
      const rowData = {}
      tableColumns.value.forEach(col => {
        rowData[col.label] = row[col.prop]
      })
      return rowData
    })
    
    const worksheet = XLSX.utils.json_to_sheet(excelData)
    const workbook = XLSX.utils.book_new()
    XLSX.utils.book_append_sheet(workbook, worksheet, '透视表数据')
    
    const excelBuffer = XLSX.write(workbook, { bookType: 'xlsx', type: 'array' })
    const blob = new Blob([excelBuffer], { type: 'application/octet-stream' })
    
    const today = new Date().toISOString().slice(0, 10)
    saveAs(blob, `透视表数据_${today}.xlsx`)
  } catch (error) {
    console.error('导出Excel失败:', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.pivot-analysis-container {
  padding: 20px;
  height: 100%;
  background-color: #f0f2f5;
  overflow: hidden;
}

.pivot-layout {
  display: flex;
  gap: 20px;
  height: calc(100% - 60px);
  margin-top: 20px;
}

.fields-panel {
  width: 240px;
  background-color: white;
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.fields-panel h3 {
  margin-bottom: 16px;
  font-size: 16px;
  color: #303133;
}

.field-section {
  border: 1px solid #e4e7ed;
  border-radius: 4px;
}

.section-title {
  padding: 10px 12px;
  background-color: #f5f7fa;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
}

.subsection {
  padding: 8px;
}

.subsection + .subsection {
  border-top: 1px solid #e4e7ed;
}

.subsection-title {
  font-size: 12px;
  color: #909399;
  margin-bottom: 8px;
  padding-left: 4px;
}

.field-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 4px;
  cursor: grab;
  transition: all 0.2s;
  font-size: 14px;
}

.field-item:hover {
  background-color: #ecf5ff;
}

.field-item:active {
  cursor: grabbing;
}

.measure-item {
  background-color: #f0f9ff;
  border: 1px solid #b3d8ff;
  color: #409eff;
}

.dimension-item {
  background-color: #f0f9eb;
  border: 1px solid #c2e7b0;
  color: #67c23a;
}

.pivot-workspace {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 16px;
  overflow: hidden;
}

.filter-panel {
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  padding: 16px;
}

.filter-panel-title {
  font-weight: 600;
  margin-bottom: 12px;
  color: #303133;
}

.filter-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.filter-item {
  min-width: 200px;
}

.filter-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
  color: #606266;
}

.drop-zones {
  display: flex;
  gap: 16px;
}

.drop-zone {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow: hidden;
}

.zone-title {
  padding: 12px 16px;
  background-color: #f5f7fa;
  font-weight: 600;
  border-bottom: 1px solid #e4e7ed;
}

.zone-content {
  min-height: 80px;
  padding: 12px;
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-content: flex-start;
}

.zone-content .placeholder {
  color: #c0c4cc;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 100%;
}

.dropped-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 13px;
  position: relative;
}

.remove-icon {
  cursor: pointer;
  font-size: 12px;
  opacity: 0.7;
  transition: opacity 0.2s;
}

.remove-icon:hover {
  opacity: 1;
}

.pivot-table-container {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.table-actions {
  padding: 16px;
  border-bottom: 1px solid #e4e7ed;
  display: flex;
  gap: 12px;
}

.table-wrapper {
  flex: 1;
  overflow: auto;
  padding: 16px;
}

.empty-table {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}
</style>

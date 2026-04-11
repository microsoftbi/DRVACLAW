<template>
  <div class="area-statistics-container">
    <h2>区域统计</h2>
    <div class="filter-container" style="margin-bottom: 20px; padding: 16px; background-color: #f5f7fa; border-radius: 4px;">
      <el-row :gutter="10">
        <el-col :span="8">
          <el-form-item label="开始日期">
            <el-date-picker
              v-model="dateRange[0]"
              type="date"
              placeholder="选择开始日期"
              value-format="YYYY-MM-DD"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <el-form-item label="结束日期">
            <el-date-picker
              v-model="dateRange[1]"
              type="date"
              placeholder="选择结束日期"
              value-format="YYYY-MM-DD"
              clearable
            />
          </el-form-item>
        </el-col>
        <el-col :span="8">
          <div style="display: flex; gap: 10px; margin-top: 24px;">
            <el-button type="primary" @click="applyDateFilter">应用筛选</el-button>
            <el-button @click="resetDateFilter">重置</el-button>
          </div>
        </el-col>
      </el-row>
    </div>
    <div class="dashboard">
      <div class="map-section">
        <h3>郑州各区地图</h3>
        <div id="areaMap" class="map-container"></div>
      </div>
      <div class="stats-section">
        <h3>区域统计数据</h3>
        <div class="area-details">
          <div class="stats-card">
            <h4>{{ selectedArea ? selectedArea.name + '区统计' : '郑州全市统计' }}</h4>
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-label">学员人数</div>
                <div class="stat-value">{{ selectedAreaStats.studentCount }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">教练人数</div>
                <div class="stat-value">{{ selectedAreaStats.coachCount }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">预约课程数</div>
                <div class="stat-value">{{ selectedAreaStats.appointmentCount }}</div>
              </div>
              <div class="stat-item">
                <div class="stat-label">充值总计</div>
                <div class="stat-value">{{ selectedAreaStats.rechargeTotal }}</div>
              </div>
            </div>
            <div class="chart-container">
              <h5>预约状态分布</h5>
              <div id="statusChart" class="chart"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'
import { areaApi } from '../api/area'
import { personApi } from '../api/person'
import { appointmentApi } from '../api/appointment'
import rechargeApi from '../api/recharge'

const areas = ref([])
const selectedArea = ref(null)
const dateRange = ref([null, null])
const selectedAreaStats = ref({
  studentCount: 0,
  coachCount: 0,
  appointmentCount: 0,
  rechargeTotal: 0,
  statusCounts: {}
})

const mapChart = ref(null)
const statusChart = ref(null)

// 加载区域数据
const loadAreas = async () => {
  try {
    areas.value = await areaApi.getAll()
    initMap()
  } catch (error) {
    console.error('加载区域数据失败:', error)
  }
}

// 初始化地图
const initMap = () => {
  // 使用实际的郑州地图
  const mapDom = document.getElementById('areaMap')
  mapChart.value = echarts.init(mapDom)
  
  // 加载郑州地图数据
  fetch('https://geo.datav.aliyun.com/areas_v3/bound/410100_full.json')
    .then(response => response.json())
    .then(geoJson => {
      // 注册地图
      echarts.registerMap('zhengzhou', geoJson)
      
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}'
        },
        series: [
          {
            type: 'map',
            map: 'zhengzhou',
            data: areas.value.map(area => ({
              name: area.name,
              value: area.area_id
            })),
            itemStyle: {
              emphasis: {
                label: {
                  show: true
                },
                itemStyle: {
                  areaColor: '#409eff'
                }
              }
            },
            label: {
              show: true,
              fontSize: 12
            }
          }
        ]
      }
      
      mapChart.value.setOption(option)
      
      // 点击区域事件
      mapChart.value.on('click', params => {
        const area = areas.value.find(a => a.name === params.name)
        if (area) {
          selectedArea.value = area
          loadAreaStats(area.area_id, dateRange.value[0], dateRange.value[1])
        }
      })
    })
    .catch(error => {
      console.error('加载地图数据失败:', error)
      // 如果地图数据加载失败，使用模拟数据
      const option = {
        tooltip: {
          trigger: 'item',
          formatter: '{b}'
        },
        series: [
          {
            type: 'map',
            map: 'china',
            roam: true,
            center: [113.6, 34.7],
            zoom: 8,
            data: areas.value.map(area => ({
              name: area.name,
              value: area.area_id
            })),
            itemStyle: {
              emphasis: {
                label: {
                  show: true
                },
                itemStyle: {
                  areaColor: '#409eff'
                }
              }
            },
            label: {
              show: true,
              fontSize: 12
            }
          }
        ]
      }
      
      mapChart.value.setOption(option)
      
      // 点击区域事件
      mapChart.value.on('click', params => {
        const area = areas.value.find(a => a.name === params.name)
        if (area) {
          selectedArea.value = area
          loadAreaStats(area.area_id, dateRange.value[0], dateRange.value[1])
        }
      })
    })
}

// 加载区域统计数据
const loadAreaStats = async (areaId = null, startDate = null, endDate = null) => {
  try {
    // 加载人员数据
    const persons = await personApi.getAll()
    // 加载预约数据
    const appointments = await appointmentApi.getAll()
    // 加载充值数据
    const recharges = await rechargeApi.getAll()
    
    // 日期筛选函数
    const isDateInRange = (dateStr, start, end) => {
      if (!start && !end) return true
      const date = new Date(dateStr)
      const startDateObj = start ? new Date(start) : null
      const endDateObj = end ? new Date(end) : null
      
      if (startDateObj && endDateObj) {
        return date >= startDateObj && date <= endDateObj
      } else if (startDateObj) {
        return date >= startDateObj
      } else if (endDateObj) {
        return date <= endDateObj
      }
      return true
    }
    
    // 统计学员人数
    const studentCount = areaId 
      ? persons.filter(p => p.type === '学员' && p.area_id === areaId && isDateInRange(p.register_time, startDate, endDate)).length
      : persons.filter(p => p.type === '学员' && isDateInRange(p.register_time, startDate, endDate)).length
    
    // 统计教练人数
    const coachCount = areaId 
      ? persons.filter(p => p.type === '教练' && p.area_id === areaId && isDateInRange(p.register_time, startDate, endDate)).length
      : persons.filter(p => p.type === '教练' && isDateInRange(p.register_time, startDate, endDate)).length
    
    // 统计预约课程数
    const appointmentCount = areaId 
      ? appointments.filter(a => {
          const student = persons.find(p => p.person_id === a.student_id)
          return student && student.area_id === areaId && isDateInRange(a.appointment_date, startDate, endDate)
        }).length
      : appointments.filter(a => isDateInRange(a.appointment_date, startDate, endDate)).length
    
    // 统计充值总计
    const rechargeTotal = areaId 
      ? recharges.reduce((total, recharge) => {
          const student = persons.find(p => p.person_id === recharge.student_id)
          if (student && student.area_id === areaId && isDateInRange(recharge.recharge_time, startDate, endDate)) {
            return total + recharge.amount
          }
          return total
        }, 0)
      : recharges.reduce((total, recharge) => {
          if (isDateInRange(recharge.recharge_time, startDate, endDate)) {
            return total + recharge.amount
          }
          return total
        }, 0)
    
    // 统计各状态的预约数
    const statusCounts = {
      '待确认': 0,
      '已确认': 0,
      '已取消': 0,
      '已完成': 0
    }
    
    appointments.forEach(a => {
      if (isDateInRange(a.appointment_date, startDate, endDate)) {
        if (areaId) {
          const student = persons.find(p => p.person_id === a.student_id)
          if (student && student.area_id === areaId) {
            statusCounts[a.status] = (statusCounts[a.status] || 0) + 1
          }
        } else {
          statusCounts[a.status] = (statusCounts[a.status] || 0) + 1
        }
      }
    })
    
    selectedAreaStats.value = {
      studentCount,
      coachCount,
      appointmentCount,
      rechargeTotal,
      statusCounts
    }
    
    // 更新状态分布图表
    updateStatusChart()
  } catch (error) {
    console.error('加载区域统计数据失败:', error)
  }
}

// 更新状态分布图表
const updateStatusChart = () => {
  const chartDom = document.getElementById('statusChart')
  if (!chartDom) return
  
  if (!statusChart.value) {
    statusChart.value = echarts.init(chartDom)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: {
        type: 'shadow'
      }
    },
    xAxis: {
      type: 'category',
      data: ['待确认', '已确认', '已取消', '已完成']
    },
    yAxis: {
      type: 'value'
    },
    series: [
      {
        data: [
          selectedAreaStats.value.statusCounts['待确认'] || 0,
          selectedAreaStats.value.statusCounts['已确认'] || 0,
          selectedAreaStats.value.statusCounts['已取消'] || 0,
          selectedAreaStats.value.statusCounts['已完成'] || 0
        ],
        type: 'bar',
        itemStyle: {
          color: function(params) {
            const colors = ['#409eff', '#67c23a', '#f56c6c', '#909399']
            return colors[params.dataIndex]
          }
        }
      }
    ]
  }
  
  statusChart.value.setOption(option)
}

// 应用日期筛选
const applyDateFilter = () => {
  loadAreaStats(selectedArea.value?.area_id, dateRange.value[0], dateRange.value[1])
}

// 重置日期筛选
const resetDateFilter = () => {
  dateRange.value = [null, null]
  loadAreaStats(selectedArea.value?.area_id)
}

// 监听窗口大小变化，调整图表大小
const handleResize = () => {
  if (mapChart.value) {
    mapChart.value.resize()
  }
  if (statusChart.value) {
    statusChart.value.resize()
  }
}

onMounted(() => {
  loadAreas()
  loadAreaStats() // 加载默认的全郑州统计数据
  window.addEventListener('resize', handleResize)
})
</script>

<style scoped>
.area-statistics-container {
  padding: 20px;
  height: 100%;
  background-color: #f0f2f5;
}

.dashboard {
  display: flex;
  gap: 20px;
  margin-top: 20px;
  height: calc(100% - 80px);
}

.map-section {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.stats-section {
  flex: 1;
  background-color: white;
  border-radius: 8px;
  padding: 20px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  overflow-y: auto;
}

.map-container {
  width: 100%;
  height: calc(100% - 50px);
}

.area-details {
  margin-top: 20px;
}

.stats-card {
  background-color: #f9f9f9;
  border-radius: 8px;
  padding: 20px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin: 20px 0;
}

.stat-item {
  background-color: white;
  border-radius: 8px;
  padding: 15px;
  text-align: center;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.stat-label {
  font-size: 14px;
  color: #606266;
  margin-bottom: 5px;
}

.stat-value {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.chart-container {
  margin-top: 30px;
}

.chart {
  width: 100%;
  height: 300px;
  margin-top: 10px;
}

.no-selection {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  color: #909399;
  font-size: 16px;
}

@media screen and (max-width: 768px) {
  .dashboard {
    flex-direction: column;
  }
  
  .map-section,
  .stats-section {
    flex: none;
    height: 500px;
  }
}
</style>
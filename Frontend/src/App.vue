<template>
  <el-container class="app-container">
    <el-header class="app-header">
      <h1>驾驶陪练小龙虾管理系统</h1>
    </el-header>
    <el-container>
      <el-aside width="200px" class="app-aside">
        <el-menu
          :default-active="activeMenu"
          router
          background-color="#545c64"
          text-color="#fff"
          active-text-color="#ffd04b"
        >
          <el-menu-item index="/appointments">
            <el-icon><Calendar /></el-icon>
            <span>预约管理</span>
          </el-menu-item>
          <el-menu-item index="/areas">
            <el-icon><Location /></el-icon>
            <span>区域管理</span>
          </el-menu-item>
          <el-menu-item index="/persons">
            <el-icon><User /></el-icon>
            <span>人员管理</span>
          </el-menu-item>
          <el-menu-item index="/area-statistics">
            <el-icon><DataAnalysis /></el-icon>
            <span>区域统计</span>
          </el-menu-item>
        </el-menu>
      </el-aside>
      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Location, User, Calendar, DataAnalysis } from '@element-plus/icons-vue'

const route = useRoute()
const activeMenu = computed(() => route.path)
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body, #app {
  height: 100%;
  width: 100%;
  margin: 0;
  padding: 0;
}

.app-container {
  height: 100%;
  width: 100%;
}

.app-header {
  background-color: #409eff;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 0;
}

.app-header h1 {
  font-size: 24px;
}

.app-aside {
  background-color: #545c64;
}

.app-main {
  background-color: #f0f2f5;
  padding: 0;
  width: 100%;
}
</style>

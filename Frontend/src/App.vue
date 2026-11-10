<template>
  <el-container class="app-container">
    <el-header height="56px" class="app-header">
      <div class="brand">
        <div class="brand-mark">智</div>
        <div class="brand-text">
          <span class="brand-name">驾驶智陪工作台</span>
          <span class="brand-sub">驾驶陪练运营系统</span>
        </div>
      </div>
      <div class="header-right">
        <span class="role-chip">管理员</span>
        <div class="header-avatar">管</div>
      </div>
    </el-header>
    <el-container class="app-body">
      <el-aside width="208px" class="app-aside">
        <el-menu
          :default-active="activeMenu"
          router
          class="app-menu"
          background-color="transparent"
          text-color="#6b7280"
          active-text-color="#1e2a78"
        >
          <el-menu-item-group>
            <template #title>业务</template>
            <el-menu-item index="/appointments">
              <el-icon><Calendar /></el-icon>
              <span>预约管理</span>
            </el-menu-item>
            <el-menu-item index="/recharges">
              <el-icon><Money /></el-icon>
              <span>充值管理</span>
            </el-menu-item>
            <el-menu-item index="/balance-query">
              <el-icon><DataAnalysis /></el-icon>
              <span>余额查询</span>
            </el-menu-item>
            <el-menu-item index="/areas">
              <el-icon><Location /></el-icon>
              <span>区域管理</span>
            </el-menu-item>
          </el-menu-item-group>

          <el-sub-menu index="/persons">
            <template #title>
              <el-icon><User /></el-icon>
              <span>人员管理</span>
            </template>
            <el-menu-item index="/students">学员管理</el-menu-item>
            <el-menu-item index="/coaches">教练管理</el-menu-item>
            <el-menu-item index="/vehicles">车辆管理</el-menu-item>
          </el-sub-menu>

          <el-menu-item-group>
            <template #title>分析</template>
            <el-menu-item index="/area-statistics">
              <el-icon><DataAnalysis /></el-icon>
              <span>区域统计</span>
            </el-menu-item>
            <el-menu-item index="/audit-logs">
              <el-icon><View /></el-icon>
              <span>操作审计</span>
            </el-menu-item>
            <el-menu-item index="/pivot-analysis">
              <el-icon><DataAnalysis /></el-icon>
              <span>透视分析</span>
            </el-menu-item>
          </el-menu-item-group>
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
import { Location, User, Calendar, DataAnalysis, Money, View } from '@element-plus/icons-vue'

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
  background: #ffffff;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}

.brand-mark {
  width: 32px;
  height: 32px;
  border-radius: 8px;
  background: #2f54eb;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 15px;
  font-weight: 600;
}

.brand-text {
  display: flex;
  flex-direction: column;
  line-height: 1.3;
}

.brand-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  letter-spacing: 0.2px;
}

.brand-sub {
  font-size: 12px;
  color: #6b7280;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.role-chip {
  font-size: 12px;
  color: #6b7280;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 3px 10px;
  background: #fafbfc;
}

.header-avatar {
  width: 30px;
  height: 30px;
  border-radius: 999px;
  background: #eef1ff;
  color: #1e2a78;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 500;
}

.app-body {
  height: calc(100% - 56px);
}

.app-aside {
  background: #ffffff;
  border-right: 1px solid #e5e7eb;
}

.app-menu {
  border-right: none;
  padding: 8px;
}

.app-menu .el-menu-item-group__title {
  padding: 10px 12px 4px;
  font-size: 12px;
  color: #9ca3af;
}

.app-menu .el-menu-item,
.app-menu .el-sub-menu__title {
  height: 38px;
  line-height: 38px;
  border-radius: 8px;
  margin-bottom: 2px;
  font-size: 14px;
}

.app-menu .el-menu-item.is-active {
  background: #eef1ff;
  box-shadow: inset 3px 0 0 #2f54eb;
  font-weight: 500;
}

.app-menu .el-sub-menu .el-menu-item {
  min-width: auto;
  height: 34px;
  line-height: 34px;
  padding-left: 40px !important;
  font-size: 13px;
}

.app-menu .el-menu-item:hover,
.app-menu .el-sub-menu__title:hover {
  background: #f5f7fa;
}

.app-main {
  background: #f5f7fa;
  padding: 20px 24px;
  overflow-y: auto;
}
</style>

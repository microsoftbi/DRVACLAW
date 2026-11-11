<template>
  <div class="settings-page">
    <h2>设置</h2>

    <el-card class="settings-card" shadow="never">
      <div class="switch-row">
        <div>
          <div class="card-title">启用 AI 助手</div>
          <div class="card-sub">关闭后，界面右下角的 AI 助理气泡与聊天面板将不再显示，模型配置会保留</div>
        </div>
        <el-switch v-model="agentEnabled" @change="handleAgentSwitch" />
      </div>
    </el-card>

    <el-card class="settings-card" shadow="never">
      <template #header>
        <div class="card-header">
          <div>
            <div class="card-title">AI 助理 · 大模型</div>
            <div class="card-sub">配置后，右下角 AI 助理即可对话并操作业务数据</div>
          </div>
          <el-tag :type="ready ? 'success' : 'info'" effect="light">
            {{ ready ? '已就绪' : '未配置' }}
          </el-tag>
        </div>
      </template>

      <el-form :model="form" label-width="140px" class="settings-form">
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="https://ark.cn-beijing.volces.com/api/v3" />
          <div class="field-tip">火山方舟 Ark 的 OpenAI 兼容地址，默认已填好；其它兼容 OpenAI 的服务填对应 /v1 地址。</div>
        </el-form-item>

        <el-form-item label="API Key">
          <el-input
            v-model="form.api_key"
            type="password"
            show-password
            autocomplete="new-password"
            :placeholder="apiKeyMasked ? `已保存：${apiKeyMasked}（留空表示不修改）` : '请输入 API Key'"
          />
          <div class="field-tip">仅保存在本机 Agent 服务的配置文件中，不会写进浏览器或代码仓库。</div>
        </el-form-item>

        <el-form-item label="模型 / Endpoint ID">
          <el-input v-model="form.model" placeholder="例如 doubao-seed-1-6-250615 或方舟推理接入点 ID" />
          <div class="field-tip">火山方舟通常填写推理接入点 ID（ep-xxxx）或模型名称。</div>
        </el-form-item>

        <el-form-item>
          <div class="actions">
            <el-button type="primary" :loading="saving" @click="handleSave">保存配置</el-button>
            <el-button :loading="testing" @click="handleTest">测试连接</el-button>
          </div>
        </el-form-item>
      </el-form>

      <div v-if="statusText" class="status-line" :class="statusOk ? 'ok' : 'bad'">{{ statusText }}</div>
    </el-card>

    <el-card class="settings-card" shadow="never">
      <template #header><div class="card-title">服务说明</div></template>
      <ul class="notes">
        <li>AI 助理服务运行在本机 8003 端口，业务接口为 8002；两者需同时启动（执行 <code>./start.sh</code>）。</li>
        <li>会话按会话 ID 持久保存在 <code>Agent/data/agent.sqlite</code>，刷新页面后仍可继续对话。</li>
        <li>新增、修改、删除类操作会在聊天框中弹出确认卡片，确认后才写入业务系统。</li>
      </ul>
    </el-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { agentApi } from '../api/agent'

const form = ref({ base_url: '', api_key: '', model: '' })
const apiKeyMasked = ref('')
const ready = ref(false)
const saving = ref(false)
const testing = ref(false)
const statusText = ref('')
const statusOk = ref(false)

const AGENT_SWITCH_KEY = 'drvaclaws_agent_enabled'
const agentEnabled = ref(localStorage.getItem(AGENT_SWITCH_KEY) !== 'false')

const handleAgentSwitch = (value) => {
  localStorage.setItem(AGENT_SWITCH_KEY, value ? 'true' : 'false')
  window.dispatchEvent(new Event('drvaclaws-agent-switch'))
  ElMessage.success(value ? 'AI 助手已启用' : 'AI 助手已关闭')
}

const load = async () => {
  try {
    const data = await agentApi.getConfig()
    form.value.base_url = data.base_url || ''
    form.value.model = data.model || ''
    form.value.api_key = ''
    apiKeyMasked.value = data.api_key_masked || ''
    ready.value = !!data.ready
  } catch (error) {
    statusText.value = 'AI 助理服务未启动，请先运行 ./start.sh'
    statusOk.value = false
  }
}

const handleSave = async () => {
  saving.value = true
  statusText.value = ''
  try {
    const payload = { base_url: form.value.base_url.trim(), model: form.value.model.trim() }
    if (form.value.api_key.trim()) payload.api_key = form.value.api_key.trim()
    const data = await agentApi.saveConfig(payload)
    form.value.api_key = ''
    apiKeyMasked.value = data.api_key_masked || ''
    ready.value = !!data.ready
    statusText.value = data.ready ? '配置已保存，可以进行测试连接。' : '已保存，但仍有必填项未填写。'
    statusOk.value = !!data.ready
    ElMessage.success('配置已保存')
  } catch (error) {
    statusText.value = error.message
    statusOk.value = false
  } finally {
    saving.value = false
  }
}

const handleTest = async () => {
  testing.value = true
  statusText.value = '正在连接大模型...'
  statusOk.value = false
  try {
    const data = await agentApi.testConfig()
    statusText.value = data.message
    statusOk.value = !!data.ok
  } catch (error) {
    statusText.value = error.message
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.settings-page {
  max-width: 860px;
}

.settings-page h2 {
  font-size: 18px;
  color: #1f2937;
  margin-bottom: 16px;
}

.settings-card {
  border-radius: 10px;
  border: 1px solid #e5e7eb;
  margin-bottom: 16px;
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
}

.card-sub {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.settings-form {
  max-width: 640px;
}

.field-tip {
  font-size: 12px;
  color: #9ca3af;
  line-height: 1.5;
  margin-top: 4px;
}

.actions {
  display: flex;
  gap: 10px;
}

.status-line {
  font-size: 13px;
  padding: 8px 12px;
  border-radius: 6px;
}

.status-line.ok {
  color: #067647;
  background: #ecfdf3;
}

.status-line.bad {
  color: #b42318;
  background: #fef3f2;
}

.notes {
  font-size: 13px;
  color: #4b5563;
  line-height: 1.9;
  padding-left: 18px;
}

.notes code {
  background: #f3f4f6;
  padding: 1px 5px;
  border-radius: 4px;
  font-size: 12px;
}
</style>

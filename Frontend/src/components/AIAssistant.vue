<template>
  <div class="ai-assistant">
    <!-- 收起态：右下角气泡 -->
    <button v-if="collapsed" class="ai-bubble" title="打开 AI 助理" @click="openPanel">
      <el-icon :size="22"><ChatDotRound /></el-icon>
      <span class="bubble-dot" :class="{ online: modelReady }"></span>
    </button>

    <!-- 展开态：聊天面板 -->
    <div v-else class="ai-panel" :class="{ maximized }">
      <div class="panel-header">
        <div class="panel-title">
          <div class="panel-avatar">智</div>
          <div class="panel-title-text">
            <span class="panel-name">AI 助理</span>
            <span class="panel-sub">
              <span class="status-dot" :class="{ online: modelReady }"></span>
              {{ modelReady ? '已连接大模型' : '未配置大模型' }}
            </span>
          </div>
        </div>
        <div class="panel-actions">
          <el-tooltip :content="maximized ? '恢复默认大小' : '最大化'" placement="bottom">
            <button class="icon-btn" @click="toggleMaximize">
              <el-icon>
                <ScaleToOriginal v-if="maximized" />
                <FullScreen v-else />
              </el-icon>
            </button>
          </el-tooltip>
          <el-tooltip content="新会话" placement="bottom">
            <button class="icon-btn" @click="startNewSession"><el-icon><Plus /></el-icon></button>
          </el-tooltip>
          <el-tooltip content="刷新会话" placement="bottom">
            <button class="icon-btn" @click="reloadHistory"><el-icon><Refresh /></el-icon></button>
          </el-tooltip>
          <el-tooltip content="最小化" placement="bottom">
            <button class="icon-btn" @click="minimize"><el-icon><Close /></el-icon></button>
          </el-tooltip>
        </div>
      </div>

      <div v-if="!modelReady" class="setup-banner">
        <span>请先在设置中填写大模型的 Base URL 与 API Key</span>
        <button class="link-btn" @click="goSettings">去设置</button>
      </div>

      <div ref="scrollRef" class="panel-body">
        <div v-if="!messages.length" class="welcome">
          <div class="welcome-title">你好，我是驾驶智陪工作台的 AI 助理</div>
          <div class="welcome-sub">可以帮你查学员、查余额、排预约、建充值，也能做区域统计。试试这样说：</div>
          <div class="chips">
            <button v-for="item in suggestions" :key="item" class="chip" @click="applySuggestion(item)">
              {{ item }}
            </button>
          </div>
        </div>

        <div v-for="(msg, index) in messages" :key="index" class="msg-row" :class="msg.role">
          <div v-if="msg.role === 'assistant'" class="msg-avatar">智</div>
          <div class="msg-content">
            <div v-if="msg.tools && msg.tools.length" class="tool-list">
              <div v-for="(tool, ti) in msg.tools" :key="ti" class="tool-item" :class="tool.status">
                <el-icon v-if="tool.status === 'running'" class="is-loading"><Loading /></el-icon>
                <el-icon v-else><Check /></el-icon>
                <span>{{ toolLabel(tool.name) }}</span>
              </div>
            </div>
            <div v-if="msg.content" class="bubble markdown" v-html="renderMarkdown(msg.content)"></div>
            <div v-if="msg.pending" class="approval-card">
              <div class="approval-title">
                <el-icon><WarningFilled /></el-icon>
                <span>以下操作需要你确认后执行</span>
              </div>
              <div v-for="(action, ai) in msg.pending.action_requests" :key="ai" class="approval-item">
                <div class="approval-name">{{ toolLabel(action.name) }}</div>
                <pre class="approval-args">{{ prettyArgs(action.args) }}</pre>
              </div>
              <div class="approval-actions">
                <el-button size="small" type="primary" :loading="sending" @click="handleApprove(true)">确认执行</el-button>
                <el-button size="small" :loading="sending" @click="handleApprove(false)">取消</el-button>
              </div>
            </div>
            <div v-if="msg.error" class="error-line">{{ msg.error }}</div>
          </div>
        </div>
      </div>

      <div class="panel-footer">
        <textarea
          ref="inputRef"
          v-model="input"
          class="chat-input"
          rows="2"
          placeholder="例如：查一下徐学员的余额（Enter 发送，Shift+Enter 换行）"
          :disabled="sending"
          @keydown.enter.exact.prevent="send"
        ></textarea>
        <button class="send-btn" :disabled="sending || !input.trim()" @click="send">
          <el-icon v-if="!sending"><Promotion /></el-icon>
          <el-icon v-else class="is-loading"><Loading /></el-icon>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ChatDotRound, Close, Plus, Refresh, Check, Loading, Promotion, WarningFilled, FullScreen, ScaleToOriginal } from '@element-plus/icons-vue'
import MarkdownIt from 'markdown-it'
import DOMPurify from 'dompurify'
import { agentApi, streamAgent } from '../api/agent'

const THREAD_KEY = 'drvaclaws_agent_thread'

const TOOL_LABELS = {
  list_areas: '查询区域',
  list_students: '查询学员',
  list_coaches: '查询教练',
  list_vehicles: '查询车辆',
  list_coach_vehicles: '查询教练车辆',
  list_appointments: '查询预约',
  list_recharges: '查询充值记录',
  get_balance: '查询余额',
  list_audit_logs: '查询操作审计',
  area_statistics: '区域统计',
  create_area: '新增区域',
  update_area: '修改区域',
  delete_area: '删除区域',
  create_student: '新增学员',
  update_student: '修改学员',
  delete_student: '删除学员',
  create_coach: '新增教练',
  update_coach: '修改教练',
  delete_coach: '删除教练',
  assign_coach_vehicle: '分配教练车辆',
  create_vehicle: '新增车辆',
  update_vehicle: '修改车辆',
  delete_vehicle: '删除车辆',
  create_appointment: '创建预约',
  update_appointment: '修改预约',
  delete_appointment: '删除预约',
  create_recharge: '学员充值',
  update_recharge: '修改充值',
  delete_recharge: '删除充值'
}

const md = new MarkdownIt({ html: false, breaks: true, linkify: true })

const router = useRouter()
const collapsed = ref(true)
const maximized = ref(false)
const modelReady = ref(false)
const sending = ref(false)
const input = ref('')
const messages = ref([])
const threadId = ref('')
const scrollRef = ref(null)
const inputRef = ref(null)
let activeAssistant = null

const suggestions = ['查一下各区域的学员数量', '张教练明天有哪些预约', '给徐学员充值 2000 元、20 课时', '看看最近的充值记录']

const renderMarkdown = (text) => DOMPurify.sanitize(md.render(text || ''))
const toolLabel = (name) => TOOL_LABELS[name] || name || '调用工具'
const prettyArgs = (args) => {
  if (!args) return '{}'
  try {
    const parsed = typeof args === 'string' ? JSON.parse(args) : args
    return JSON.stringify(parsed, null, 2)
  } catch {
    return String(args)
  }
}

const scrollToBottom = async () => {
  await nextTick()
  if (scrollRef.value) scrollRef.value.scrollTop = scrollRef.value.scrollHeight
}

const ensureAssistant = () => {
  if (activeAssistant) return activeAssistant
  const msg = reactive({ role: 'assistant', content: '', tools: [], error: '', pending: null })
  messages.value.push(msg)
  activeAssistant = msg
  return msg
}

const openPanel = async () => {
  collapsed.value = false
  maximized.value = false
  await nextTick()
  scrollToBottom()
  inputRef.value?.focus()
}

const minimize = () => {
  collapsed.value = true
  maximized.value = false
}

const toggleMaximize = async () => {
  maximized.value = !maximized.value
  await nextTick()
  scrollToBottom()
  inputRef.value?.focus()
}

const goSettings = () => {
  router.push('/settings')
}

const applySuggestion = (text) => {
  input.value = text
  inputRef.value?.focus()
}

const handleEvent = (assistant) => (event, data) => {
  if (event === 'meta' && data.thread_id) {
    threadId.value = data.thread_id
    localStorage.setItem(THREAD_KEY, data.thread_id)
  } else if (event === 'token') {
    assistant.content += data.text || ''
    scrollToBottom()
  } else if (event === 'tool_start') {
    assistant.tools.push({ name: data.name, args: data.args, status: 'running' })
    scrollToBottom()
  } else if (event === 'tool_end') {
    const running = [...assistant.tools].reverse().find((t) => t.status === 'running')
    if (running) running.status = 'done'
  } else if (event === 'approval_required') {
    assistant.pending = data
    pendingAssistant = assistant
    scrollToBottom()
  } else if (event === 'error') {
    assistant.error = data.message || '请求失败'
    if (data.code === 'model_not_ready') modelReady.value = false
  }
}

let pendingAssistant = null

const send = async () => {
  const text = input.value.trim()
  if (!text || sending.value) return
  if (!threadId.value) threadId.value = localStorage.getItem(THREAD_KEY) || ''
  messages.value.push({ role: 'user', content: text })
  input.value = ''
  sending.value = true
  const assistant = ensureAssistant()
  await scrollToBottom()
  try {
    await streamAgent('/chat', { message: text, thread_id: threadId.value }, handleEvent(assistant))
  } catch (error) {
    assistant.error = error.message
  } finally {
    sending.value = false
    activeAssistant = null
    await scrollToBottom()
  }
}

const handleApprove = async (approve) => {
  if (!threadId.value || sending.value) return
  const assistant = pendingAssistant || ensureAssistant()
  if (assistant.pending) assistant.pending = null
  sending.value = true
  try {
    await streamAgent(
      '/approve',
      { thread_id: threadId.value, approve, message: approve ? null : '管理员取消了该操作。' },
      handleEvent(assistant)
    )
  } catch (error) {
    assistant.error = error.message
  } finally {
    sending.value = false
    pendingAssistant = null
    activeAssistant = null
    await scrollToBottom()
  }
}

const reloadHistory = async () => {
  if (!threadId.value) return
  try {
    const data = await agentApi.history(threadId.value)
    messages.value = (data.messages || []).map((m) => ({
      role: m.role,
      content: m.content,
      tools: [],
      error: '',
      pending: null
    }))
    if (data.pending && data.pending.action_requests?.length) {
      const last = messages.value.length && messages.value[messages.value.length - 1].role === 'assistant'
        ? messages.value[messages.value.length - 1]
        : null
      if (last) {
        last.pending = data.pending
        pendingAssistant = last
      } else {
        const msg = reactive({ role: 'assistant', content: '', tools: [], error: '', pending: data.pending })
        messages.value.push(msg)
        pendingAssistant = msg
      }
    }
    await scrollToBottom()
  } catch (error) {
    if (!messages.value.length) {
      messages.value.push({ role: 'assistant', content: '', tools: [], error: '刷新会话失败：' + error.message, pending: null })
    }
  }
}

const startNewSession = async () => {
  try {
    const data = await agentApi.newSession()
    threadId.value = data.thread_id
    localStorage.setItem(THREAD_KEY, data.thread_id)
  } catch {
    threadId.value = crypto.randomUUID()
    localStorage.setItem(THREAD_KEY, threadId.value)
  }
  messages.value = []
  pendingAssistant = null
  activeAssistant = null
  input.value = ''
}

const checkHealth = async () => {
  try {
    const data = await agentApi.health()
    modelReady.value = !!data.model_ready
  } catch {
    modelReady.value = false
  }
}

watch(modelReady, (value) => {
  if (!value) return
  activeAssistant = null
})

onMounted(async () => {
  threadId.value = localStorage.getItem(THREAD_KEY) || ''
  await checkHealth()
  if (threadId.value) {
    await reloadHistory()
  }
})
</script>

<style scoped>
.ai-bubble {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 54px;
  height: 54px;
  border-radius: 50%;
  border: none;
  cursor: pointer;
  background: linear-gradient(135deg, #2f54eb, #1e2a78);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8px 24px rgba(47, 84, 235, 0.35);
  z-index: 3000;
  transition: transform 0.2s ease;
}

.ai-bubble:hover {
  transform: translateY(-2px);
}

.bubble-dot {
  position: absolute;
  top: 8px;
  right: 8px;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #f59e0b;
}

.bubble-dot.online {
  background: #22c55e;
}

.ai-panel {
  position: fixed;
  right: 24px;
  bottom: 24px;
  width: 380px;
  height: 600px;
  max-height: calc(100vh - 100px);
  background: #fff;
  border-radius: 14px;
  border: 1px solid #e5e7eb;
  box-shadow: 0 16px 48px rgba(15, 23, 42, 0.18);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  z-index: 3000;
}

.ai-panel.maximized {
  top: 0;
  right: 0;
  bottom: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  max-height: 100vh;
  border: none;
  border-radius: 0;
  box-shadow: none;
  z-index: 4000;
}

.ai-panel.maximized .msg-row {
  max-width: 860px;
  margin-left: auto;
  margin-right: auto;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 14px;
  border-bottom: 1px solid #f1f3f5;
  background: #fff;
}

.panel-title {
  display: flex;
  align-items: center;
  gap: 10px;
}

.panel-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: #eef1ff;
  color: #1e2a78;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-title-text {
  display: flex;
  flex-direction: column;
  line-height: 1.4;
}

.panel-name {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
}

.panel-sub {
  font-size: 11px;
  color: #9ca3af;
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #f59e0b;
  display: inline-block;
}

.status-dot.online {
  background: #22c55e;
}

.panel-actions {
  display: flex;
  gap: 2px;
}

.icon-btn {
  width: 28px;
  height: 28px;
  border: none;
  border-radius: 6px;
  background: transparent;
  color: #6b7280;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.icon-btn:hover {
  background: #f5f7fa;
  color: #2f54eb;
}

.setup-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 8px 14px;
  font-size: 12px;
  color: #b45309;
  background: #fffbeb;
  border-bottom: 1px solid #fef3c7;
}

.link-btn {
  border: none;
  background: transparent;
  color: #2f54eb;
  font-size: 12px;
  cursor: pointer;
  white-space: nowrap;
}

.panel-body {
  flex: 1;
  overflow-y: auto;
  padding: 14px;
  background: #fafbfc;
}

.welcome {
  color: #6b7280;
}

.welcome-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 6px;
}

.welcome-sub {
  font-size: 12px;
  line-height: 1.7;
}

.chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 12px;
}

.chip {
  border: 1px solid #e5e7eb;
  background: #fff;
  color: #4b5563;
  font-size: 12px;
  border-radius: 999px;
  padding: 5px 10px;
  cursor: pointer;
}

.chip:hover {
  border-color: #2f54eb;
  color: #2f54eb;
}

.msg-row {
  display: flex;
  gap: 8px;
  margin-bottom: 14px;
  align-items: flex-start;
}

.msg-row.user {
  flex-direction: row-reverse;
}

.msg-avatar {
  width: 26px;
  height: 26px;
  border-radius: 7px;
  background: #eef1ff;
  color: #1e2a78;
  font-size: 11px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.msg-content {
  max-width: 82%;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.msg-row.user .msg-content {
  align-items: flex-end;
}

.bubble {
  padding: 9px 12px;
  border-radius: 10px;
  font-size: 13px;
  line-height: 1.65;
  background: #fff;
  border: 1px solid #eef0f2;
  color: #1f2937;
  word-break: break-word;
}

.msg-row.user .bubble {
  background: #2f54eb;
  border-color: #2f54eb;
  color: #fff;
}

.tool-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.tool-item {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11px;
  color: #6b7280;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 999px;
  padding: 3px 8px;
}

.tool-item.running {
  color: #2f54eb;
  border-color: #c7d2fe;
  background: #eef1ff;
}

.approval-card {
  background: #fff;
  border: 1px solid #fde68a;
  border-radius: 10px;
  padding: 10px;
}

.approval-title {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  font-weight: 600;
  color: #b45309;
  margin-bottom: 8px;
}

.approval-item {
  border-top: 1px dashed #f1f3f5;
  padding-top: 6px;
  margin-top: 6px;
}

.approval-name {
  font-size: 12px;
  color: #1f2937;
  font-weight: 500;
}

.approval-args {
  font-size: 11px;
  color: #6b7280;
  background: #f9fafb;
  border-radius: 6px;
  padding: 6px 8px;
  margin-top: 4px;
  max-height: 120px;
  overflow: auto;
  white-space: pre-wrap;
  word-break: break-all;
}

.approval-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.error-line {
  font-size: 12px;
  color: #b42318;
  background: #fef3f2;
  border-radius: 6px;
  padding: 6px 10px;
}

.panel-footer {
  display: flex;
  gap: 8px;
  align-items: flex-end;
  padding: 10px 12px;
  border-top: 1px solid #f1f3f5;
  background: #fff;
}

.chat-input {
  flex: 1;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 8px 10px;
  font-size: 13px;
  line-height: 1.5;
  resize: none;
  outline: none;
  font-family: inherit;
  color: #1f2937;
}

.chat-input:focus {
  border-color: #2f54eb;
}

.send-btn {
  width: 34px;
  height: 34px;
  border: none;
  border-radius: 8px;
  background: #2f54eb;
  color: #fff;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.send-btn:disabled {
  background: #c7d2fe;
  cursor: not-allowed;
}

.markdown :deep(h1),
.markdown :deep(h2),
.markdown :deep(h3) {
  font-size: 13px;
  font-weight: 600;
  margin: 6px 0 4px;
}

.markdown :deep(p) {
  margin: 4px 0;
}

.markdown :deep(ul),
.markdown :deep(ol) {
  padding-left: 18px;
  margin: 4px 0;
}

.markdown :deep(table) {
  border-collapse: collapse;
  width: 100%;
  font-size: 12px;
  margin: 6px 0;
}

.markdown :deep(th),
.markdown :deep(td) {
  border: 1px solid #e5e7eb;
  padding: 4px 6px;
  text-align: left;
}

.markdown :deep(th) {
  background: #f5f7fa;
  font-weight: 600;
}

.markdown :deep(code) {
  background: #f3f4f6;
  border-radius: 4px;
  padding: 1px 4px;
  font-size: 12px;
}

.markdown :deep(pre) {
  background: #f3f4f6;
  border-radius: 6px;
  padding: 8px;
  overflow-x: auto;
}

@media (max-width: 640px) {
  .ai-panel {
    right: 12px;
    bottom: 12px;
    width: calc(100vw - 24px);
    height: calc(100vh - 96px);
  }
}
</style>

// AI 助理服务（8003）的前端封装，经 vite 代理 /agent-api 访问
const BASE = '/agent-api'

async function jsonFetch(path, options = {}) {
  const resp = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options
  })
  if (!resp.ok) {
    throw new Error(`请求失败（HTTP ${resp.status}）`)
  }
  return resp.json()
}

export const agentApi = {
  getConfig() {
    return jsonFetch('/config')
  },
  saveConfig(data) {
    return jsonFetch('/config', { method: 'PUT', body: JSON.stringify(data) })
  },
  testConfig() {
    return jsonFetch('/config/test', { method: 'POST' })
  },
  newSession() {
    return jsonFetch('/session', { method: 'POST' })
  },
  history(threadId) {
    return jsonFetch(`/history?thread_id=${encodeURIComponent(threadId)}`)
  },
  health() {
    return jsonFetch('/health')
  }
}

function parseBlocks(buffer, onEvent) {
  const blocks = buffer.split('\n\n')
  const rest = blocks.pop()
  for (const block of blocks) {
    let event = 'message'
    let data = ''
    for (const line of block.split('\n')) {
      if (line.startsWith('event:')) event = line.slice(6).trim()
      else if (line.startsWith('data:')) data += line.slice(5).trim()
    }
    if (!data) continue
    try {
      onEvent(event, JSON.parse(data))
    } catch {
      onEvent(event, { raw: data })
    }
  }
  return rest
}

// 流式读取 SSE：onEvent(eventName, payload)
export async function streamAgent(path, payload, onEvent) {
  const resp = await fetch(BASE + path, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  })
  if (!resp.ok || !resp.body) {
    throw new Error(`请求失败（HTTP ${resp.status}）`)
  }
  const reader = resp.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    buffer = parseBlocks(buffer, onEvent)
  }
  if (buffer.trim()) parseBlocks(buffer + '\n\n', onEvent)
}

export default agentApi

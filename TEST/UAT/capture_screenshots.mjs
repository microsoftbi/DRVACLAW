#!/usr/bin/env node
/**
 * UAT 用例截图服务
 *
 * 常驻进程：启动一个无头 Chrome，按行协议接收 JSON 任务，
 * 打开前端业务页面（或后端原始接口地址），高亮关键数据行，
 * 顶部叠加用例信息条后截屏保存。
 *
 * 协议：
 *   启动后输出 {"ready":true}
 *   每行请求 {"case_id","url","focus","title","caption","status","out"}
 *   每行响应 {"ok":true,"path":"..."} 或 {"ok":false,"error":"..."}
 *   收到 {"exit":true} 后退出
 */

import { spawn } from 'node:child_process'
import { createServer } from 'node:net'
import { mkdirSync, writeFileSync, rmSync } from 'node:fs'
import { dirname, resolve } from 'node:path'
import { createInterface } from 'node:readline'

const CHROME_BIN = process.env.CHROME_BIN
  || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
const OUT_DIR = resolve(process.argv[2] || './report/screenshots')
const VIEW_WIDTH = 1440
const VIEW_HEIGHT = 900

const sleep = (ms) => new Promise((r) => setTimeout(r, ms))

function log(msg) {
  process.stderr.write('[shot] ' + msg + '\n')
}

function reply(payload) {
  process.stdout.write(JSON.stringify(payload) + '\n')
}

function freePort() {
  return new Promise((resolvePort) => {
    const server = createServer()
    server.listen(0, '127.0.0.1', () => {
      const port = server.address().port
      server.close(() => resolvePort(port))
    })
  })
}

class CDP {
  constructor(ws) {
    this.ws = ws
    this.nextId = 1
    this.pending = new Map()
    this.ws.addEventListener('message', (event) => {
      let msg
      try {
        msg = JSON.parse(event.data)
      } catch {
        return
      }
      if (!msg.id) return
      const task = this.pending.get(msg.id)
      if (!task) return
      this.pending.delete(msg.id)
      if (msg.error) task.reject(new Error(msg.error.message))
      else task.resolve(msg.result)
    })
  }

  send(method, params = {}) {
    const id = this.nextId++
    return new Promise((resolveSend, rejectSend) => {
      this.pending.set(id, { resolve: resolveSend, reject: rejectSend })
      this.ws.send(JSON.stringify({ id, method, params }))
    })
  }

  close() {
    try {
      this.ws.close()
    } catch {
      /* ignore */
    }
  }
}

async function waitForTarget(port) {
  const deadline = Date.now() + 15000
  while (Date.now() < deadline) {
    try {
      const response = await fetch(`http://127.0.0.1:${port}/json/list`)
      const targets = await response.json()
      const page = targets.find((item) => item.type === 'page' && item.webSocketDebuggerUrl)
      if (page) return page
    } catch {
      /* chrome not ready yet */
    }
    await sleep(200)
  }
  throw new Error('无头 Chrome 启动超时')
}

function injectExpression(item) {
  const cid = JSON.stringify(item.case_id)
  const title = JSON.stringify(item.title || '')
  const caption = JSON.stringify(item.caption || '')
  const status = JSON.stringify(item.status || 'PASS')
  const focus = JSON.stringify(item.focus || '')
  return `(function(){
    var cid=${cid}, title=${title}, caption=${caption}, status=${status}, focus=${focus};
    var oldBanner=document.getElementById('__uat_banner');
    if(oldBanner) oldBanner.remove();
    var oldTag=document.getElementById('__uat_tag');
    if(oldTag) oldTag.remove();
    var oldHl=document.getElementById('__uat_hl');
    if(oldHl){ oldHl.removeAttribute('id'); oldHl.style.outline=''; oldHl.style.background=''; }

    var banner=document.createElement('div');
    banner.id='__uat_banner';
    banner.style.cssText='position:fixed;left:0;top:0;right:0;z-index:2147483000;display:flex;align-items:center;gap:10px;padding:9px 18px;background:rgba(17,24,39,.94);color:#fff;font-family:"PingFang SC","Microsoft YaHei",system-ui,sans-serif;box-shadow:0 2px 8px rgba(0,0,0,.25)';

    var badge=document.createElement('span');
    badge.textContent=status;
    badge.style.cssText='background:'+(status==='PASS'?'#16a34a':'#dc2626')+';color:#fff;border-radius:4px;padding:2px 8px;font-size:12px;font-weight:700;letter-spacing:.4px';

    var idEl=document.createElement('span');
    idEl.textContent=cid;
    idEl.style.cssText='font-weight:700;font-size:13px';

    var titleEl=document.createElement('span');
    titleEl.textContent=title;
    titleEl.style.cssText='font-size:13px';

    var captionEl=document.createElement('span');
    captionEl.textContent=caption;
    captionEl.style.cssText='margin-left:auto;max-width:600px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;opacity:.78;font-size:12px';

    banner.appendChild(badge);
    banner.appendChild(idEl);
    banner.appendChild(titleEl);
    banner.appendChild(captionEl);
    document.body.appendChild(banner);
    document.body.style.paddingTop='46px';

    var target=null;
    if(focus){
      var rows=Array.prototype.slice.call(document.querySelectorAll('tbody tr, .el-table__row'));
      for(var i=0;i<rows.length;i++){
        if(rows[i].innerText && rows[i].innerText.indexOf(focus)!==-1){ target=rows[i]; break; }
      }
      if(!target){
        var leaves=Array.prototype.slice.call(document.querySelectorAll('body *'));
        for(var j=0;j<leaves.length;j++){
          if(leaves[j].children.length===0 && leaves[j].innerText===focus){ target=leaves[j]; break; }
        }
      }
    }
    if(!target){
      // 接口原始响应 / 文档页没有业务表格，直接标注正文内容（如 404 的 {"detail": ...}）
      var pre=document.querySelector('pre');
      if(pre && pre.innerText && pre.innerText.trim().length>0){ target=pre; }
    }
    if(target){
      target.id='__uat_hl';
      target.style.outline='3px solid #e11d48';
      target.style.outlineOffset='-3px';
      if(target.tagName!=='PRE'){ target.style.background='#fff1f2'; }
      try { target.scrollIntoView({ block:'center', inline:'nearest' }); } catch(e) {}
      var rect=target.getBoundingClientRect();
      var tag=document.createElement('div');
      tag.id='__uat_tag';
      tag.textContent='关键数据';
      tag.style.cssText='position:fixed;z-index:2147483000;background:#e11d48;color:#fff;'
        + 'font-size:12px;font-weight:700;padding:1px 8px;border-radius:4px;letter-spacing:.5px;'
        + 'left:'+Math.max(8,rect.left)+'px;top:'+Math.max(48,rect.top-24)+'px';
      document.body.appendChild(tag);
    }
    return { highlighted: !!target };
  })()`
}

async function waitReadyAndFocus(cdp, focus) {
  const deadline = Date.now() + 7000
  let ready = false
  while (Date.now() < deadline) {
    const result = await cdp.send('Runtime.evaluate', {
      expression: `(function(){
        var rows=document.querySelectorAll('tbody tr, .el-table__row').length;
        var text=document.body?document.body.innerText.length:0;
        return JSON.stringify({state:document.readyState,rows:rows,text:text});
      })()`,
      returnByValue: true
    })
    let info = null
    try {
      info = JSON.parse(result.result.value)
    } catch {
      /* ignore */
    }
    if (info && info.state === 'complete' && (info.rows > 0 || info.text > 120)) {
      ready = true
      if (!focus) break
      const hasFocus = await cdp.send('Runtime.evaluate', {
        expression: `document.body && document.body.innerText.indexOf(${JSON.stringify(focus)}) !== -1`,
        returnByValue: true
      })
      if (hasFocus.result.value) break
      if (Date.now() + 600 > deadline) break
      await sleep(150)
    } else {
      await sleep(120)
    }
  }
  await sleep(250)
  return ready
}

async function main() {
  mkdirSync(OUT_DIR, { recursive: true })
  const port = await freePort()
  const profile = `/tmp/uat-shot-profile-${process.pid}`

  const chrome = spawn(CHROME_BIN, [
    '--headless=new',
    `--remote-debugging-port=${port}`,
    `--user-data-dir=${profile}`,
    '--no-first-run',
    '--no-default-browser-check',
    '--disable-gpu',
    '--hide-scrollbars',
    '--mute-audio',
    '--disable-extensions',
    '--disable-background-networking',
    `--window-size=${VIEW_WIDTH},${VIEW_HEIGHT}`,
    'about:blank'
  ], { stdio: 'ignore' })

  let cdp = null
  try {
    const target = await waitForTarget(port)
    const ws = new WebSocket(target.webSocketDebuggerUrl)
    await new Promise((resolveOpen, rejectOpen) => {
      ws.addEventListener('open', resolveOpen, { once: true })
      ws.addEventListener('error', () => rejectOpen(new Error('CDP 连接失败')), { once: true })
    })
    cdp = new CDP(ws)
    await cdp.send('Page.enable')
    await cdp.send('Runtime.enable')
    await cdp.send('Emulation.setDeviceMetricsOverride', {
      width: VIEW_WIDTH,
      height: VIEW_HEIGHT,
      deviceScaleFactor: 1,
      mobile: false
    })
  } catch (error) {
    log(error.message)
    reply({ ready: false, error: error.message })
    chrome.kill('SIGKILL')
    process.exit(1)
  }

  reply({ ready: true })
  log('截图服务就绪，端口 ' + port)

  const rl = createInterface({ input: process.stdin, crlfDelay: Infinity })
  let closing = false
  const queue = []
  let busy = false

  async function handleTask(task) {
    if (task.exit) {
      closing = true
      cdp.close()
      chrome.kill('SIGKILL')
      try {
        rmSync(profile, { recursive: true, force: true })
      } catch {
        /* ignore */
      }
      process.exit(0)
    }
    try {
      const plain = !!task.plain
      // 原始接口响应页内容很短，用紧凑高度避免截图大片空白
      const rawApi = task.url.startsWith('http://127.0.0.1:8002') && !task.url.includes('/docs')
      await cdp.send('Emulation.setDeviceMetricsOverride', {
        width: VIEW_WIDTH,
        height: task.height || (rawApi && !plain ? 420 : VIEW_HEIGHT),
        deviceScaleFactor: 1,
        mobile: false
      })
      await cdp.send('Page.navigate', { url: task.url })
      await waitReadyAndFocus(cdp, plain ? '' : task.focus)
      if (!plain) {
        await cdp.send('Runtime.evaluate', {
          expression: injectExpression(task),
          returnByValue: true
        })
      }
      if (task.script) {
        await cdp.send('Runtime.evaluate', {
          expression: task.script,
          awaitPromise: true,
          returnByValue: true
        })
        await sleep(700)
      }
      await sleep(plain ? 500 : 200)

      const shot = await cdp.send('Page.captureScreenshot', {
        format: 'jpeg',
        quality: 88,
        captureBeyondViewport: false
      })

      const outPath = resolve(task.out)
      mkdirSync(dirname(outPath), { recursive: true })
      writeFileSync(outPath, Buffer.from(shot.data, 'base64'))
      reply({ ok: true, path: outPath })
    } catch (error) {
      log('截屏失败 ' + (task.case_id || '') + ': ' + error.message)
      reply({ ok: false, error: error.message })
    }
  }

  async function drain() {
    if (busy) return
    busy = true
    while (queue.length && !closing) {
      await handleTask(queue.shift())
    }
    busy = false
  }

  rl.on('line', (line) => {
    const text = line.trim()
    if (!text || closing) return
    try {
      queue.push(JSON.parse(text))
    } catch {
      reply({ ok: false, error: '任务格式错误' })
      return
    }
    drain()
  })

  rl.on('close', () => {
    if (closing) return
    closing = true
    cdp.close()
    chrome.kill('SIGKILL')
    try {
      rmSync(profile, { recursive: true, force: true })
    } catch {
      /* ignore */
    }
    process.exit(0)
  })
}

main().catch((error) => {
  log(error.stack || error.message)
  reply({ ready: false, error: error.message })
  process.exit(1)
})

import SwiftUI
import AppKit
import CryptoKit

// MARK: - 三个服务

enum ServiceKind: String, CaseIterable, Identifiable {
    case backend, agent, frontend

    var id: String { rawValue }

    var title: String {
        switch self {
        case .backend: return "后端服务"
        case .agent: return "AI 助理服务"
        case .frontend: return "前端服务"
        }
    }

    var detail: String {
        switch self {
        case .backend: return "FastAPI · 业务接口"
        case .agent: return "deepagents · 对话与审批"
        case .frontend: return "Vite · 管理界面"
        }
    }

    var port: Int {
        switch self {
        case .backend: return 8002
        case .agent: return 8003
        case .frontend: return 5174
        }
    }

    var healthPath: String {
        switch self {
        case .backend: return "/docs"
        case .agent: return "/health"
        case .frontend: return "/"
        }
    }

    var logName: String {
        switch self {
        case .backend: return "backend.log"
        case .agent: return "agent.log"
        case .frontend: return "frontend.log"
        }
    }

    var symbol: String {
        switch self {
        case .backend: return "server.rack"
        case .agent: return "brain"
        case .frontend: return "macwindow"
        }
    }

    var directory: String {
        switch self {
        case .backend: return "Backend"
        case .agent: return "Agent"
        case .frontend: return "Frontend"
        }
    }

    // 用于 pkill -f 的进程特征，兼容 start.sh 启动的进程
    var processPattern: String {
        switch self {
        case .backend: return "uvicorn main:app"
        case .agent: return "uvicorn server:app"
        case .frontend: return "vite/bin/vite.js"
        }
    }
}

// MARK: - 日志筛选

enum LogFilter: String, CaseIterable, Identifiable {
    case all, backend, agent, frontend

    var id: String { rawValue }

    var title: String {
        switch self {
        case .all: return "全部"
        case .backend: return "后端"
        case .agent: return "AI 助理"
        case .frontend: return "前端"
        }
    }

    var kind: ServiceKind? {
        switch self {
        case .all: return nil
        case .backend: return .backend
        case .agent: return .agent
        case .frontend: return .frontend
        }
    }
}

// MARK: - 应用状态与进程管理

final class AppModel: ObservableObject {
    static let shared = AppModel()
    static let defaultRoot = "/Users/wadesong/Desktop/TEST/DRVACLAW"
    private let rootKey = "Drvaclaw.ProjectRoot"

    @Published var root: String
    @Published var healthy: [ServiceKind: Bool] = [:]
    @Published var starting: Set<ServiceKind> = []
    @Published var logText: String = ""
    @Published var logs: [ServiceKind: String] = [:]
    @Published var notice: String = ""
    @Published var isBackingUp: Bool = false
    @Published var backups: [BackupRecord] = []
    @Published var logFilter: LogFilter = .all
    @Published var collecting: Bool = false

    private var processes: [ServiceKind: Process] = [:]
    private var logOffsets: [ServiceKind: UInt64] = [:]
    private let backupDirKey = "Drvaclaw.BackupDestination"
    private let backupRecordsKey = "Drvaclaw.BackupRecords"

    init() {
        root = UserDefaults.standard.string(forKey: rootKey) ?? AppModel.defaultRoot
        for kind in ServiceKind.allCases { healthy[kind] = false }
        if let data = UserDefaults.standard.data(forKey: backupRecordsKey),
           let saved = try? JSONDecoder().decode([BackupRecord].self, from: data) {
            backups = saved
        }
        let timer = Timer(timeInterval: 2.0, repeats: true) { [weak self] _ in
            self?.checkAll()
        }
        RunLoop.main.add(timer, forMode: .common)
        let logTimer = Timer(timeInterval: 1.5, repeats: true) { [weak self] _ in
            self?.pollLogs()
        }
        RunLoop.main.add(logTimer, forMode: .common)
        checkAll()
    }

    // MARK: 状态轮询

    func checkAll() {
        for kind in ServiceKind.allCases { check(kind) }
    }

    private func check(_ kind: ServiceKind) {
        guard let url = URL(string: "http://127.0.0.1:\(kind.port)\(kind.healthPath)") else { return }
        var request = URLRequest(url: url)
        request.timeoutInterval = 2
        request.httpMethod = "GET"
        URLSession.shared.dataTask(with: request) { [weak self] _, response, _ in
            let ok = (response as? HTTPURLResponse)?.statusCode == 200
            DispatchQueue.main.async {
                guard let self else { return }
                if self.healthy[kind] != ok { self.healthy[kind] = ok }
                if ok { self.starting.remove(kind) }
            }
        }.resume()
    }

    func isRunning(_ kind: ServiceKind) -> Bool {
        (healthy[kind] ?? false) || (processes[kind]?.isRunning ?? false)
    }

    // MARK: 启动 / 停止

    func startAll() {
        start(.backend)
        start(.agent)
        DispatchQueue.main.asyncAfter(deadline: .now() + 2.5) { [weak self] in
            self?.start(.frontend)
        }
    }

    func start(_ kind: ServiceKind) {
        if healthy[kind] ?? false {
            notice = "\(kind.title)已在运行（端口 \(kind.port)），无需重复启动"
            return
        }
        if let p = processes[kind], p.isRunning { return }
        guard FileManager.default.fileExists(atPath: root) else {
            notice = "项目目录不存在：\(root)"
            return
        }
        starting.insert(kind)
        notice = ""

        let process = Process()
        process.executableURL = URL(fileURLWithPath: "/bin/zsh")
        process.arguments = ["-lc", command(for: kind)]
        process.currentDirectoryURL = URL(fileURLWithPath: root)
        var env = ProcessInfo.processInfo.environment
        env["HOME"] = NSHomeDirectory()
        process.environment = env

        process.terminationHandler = { [weak self] proc in
            DispatchQueue.main.async {
                guard let self else { return }
                if self.processes[kind] === proc { self.processes[kind] = nil }
                self.starting.remove(kind)
                self.healthy[kind] = false
                self.append("进程已退出（状态码 \(proc.terminationStatus)）\n", kind: kind)
            }
        }

        do {
            try process.run()
            processes[kind] = process
            append("启动 \(kind.title)…\n", kind: kind)
        } catch {
            starting.remove(kind)
            notice = "启动失败：\(error.localizedDescription)"
        }
    }

    func stop(_ kind: ServiceKind) {
        if let p = processes[kind], p.isRunning { p.terminate() }
        processes[kind] = nil
        starting.remove(kind)
        healthy[kind] = false
        killRemaining(kind)
        append("已停止 \(kind.title)\n", kind: kind)
    }

    func stopAll() {
        for kind in ServiceKind.allCases { stop(kind) }
    }

    // 兜底：清理由 start.sh 或历史会话启动的同名进程
    private func killRemaining(_ kind: ServiceKind) {
        let pattern = kind.processPattern
        DispatchQueue.global(qos: .utility).async {
            let p = Process()
            p.executableURL = URL(fileURLWithPath: "/usr/bin/pkill")
            p.arguments = ["-f", pattern]
            try? p.run()
            p.waitUntilExit()
        }
    }

    // MARK: 命令拼装

    private func command(for kind: ServiceKind) -> String {
        let prefix = pathPrefix() + " && export PYTHONUNBUFFERED=1"
        let dir = "\(root)/\(kind.directory)"
        let log = "'\(logURL(kind).path)'"
        switch kind {
        case .backend:
            return "\(prefix); cd '\(dir)' && exec '\(pythonPath(in: "Backend"))' -m uvicorn main:app --host 0.0.0.0 --port 8002 > \(log) 2>&1"
        case .agent:
            return "\(prefix); cd '\(dir)' && exec '\(pythonPath(in: "Agent"))' -m uvicorn server:app --host 0.0.0.0 --port 8003 > \(log) 2>&1"
        case .frontend:
            return "\(prefix); cd '\(dir)' && exec node ./node_modules/vite/bin/vite.js --host 0.0.0.0 --port 5174 > \(log) 2>&1"
        }
    }

    private func pythonPath(in sub: String) -> String {
        let venv = "\(root)/\(sub)/.venv/bin/python"
        return FileManager.default.isExecutableFile(atPath: venv) ? venv : "/usr/bin/python3"
    }

    // GUI 应用不继承终端 PATH，这里补齐 node / Homebrew 等常见路径
    private func pathPrefix() -> String {
        var dirs = ["/opt/homebrew/bin", "/usr/local/bin"]
        let local = NSHomeDirectory() + "/.local"
        if let items = try? FileManager.default.contentsOfDirectory(atPath: local) {
            for item in items where item.hasPrefix("node-") {
                dirs.append("\(local)/\(item)/bin")
            }
        }
        return "export PATH=\"\(dirs.joined(separator: ":")):$PATH\""
    }

    // MARK: 日志

    private func logURL(_ kind: ServiceKind) -> URL {
        URL(fileURLWithPath: root).appendingPathComponent(kind.logName)
    }

    // 用户手动开启后才读取，避免日志过载；从当前文件末尾开始，只看新输出
    func startCollecting() {
        resetLogOffsets()
        collecting = true
    }

    func stopCollecting() {
        collecting = false
    }

    private func resetLogOffsets() {
        for kind in ServiceKind.allCases {
            let url = logURL(kind)
            guard let attrs = try? FileManager.default.attributesOfItem(atPath: url.path),
                  let size = (attrs[.size] as? NSNumber)?.uint64Value else {
                logOffsets[kind] = 0
                continue
            }
            logOffsets[kind] = size
        }
    }

    // 轮询日志文件的新增内容，不依赖当前 App 是否启动了该服务
    private func pollLogs() {
        guard collecting else { return }
        for kind in ServiceKind.allCases {
            let url = logURL(kind)
            guard let attrs = try? FileManager.default.attributesOfItem(atPath: url.path),
                  let size = (attrs[.size] as? NSNumber)?.uint64Value else { continue }
            var offset = logOffsets[kind] ?? 0
            if size < offset { offset = 0 }
            guard size > offset else {
                logOffsets[kind] = size
                continue
            }
            guard let handle = try? FileHandle(forReadingFrom: url) else { continue }
            defer { try? handle.close() }
            try? handle.seek(toOffset: offset)
            let data = (try? handle.readToEnd()) ?? Data()
            logOffsets[kind] = size
            guard !data.isEmpty else { continue }
            append(String(decoding: data, as: UTF8.self), kind: kind)
        }
    }

    private func append(_ text: String, kind: ServiceKind) {
        guard collecting else { return }
        let body = text.hasSuffix("\n") ? text : text + "\n"
        var per = logs[kind] ?? ""
        per += body
        if per.count > 16000 { per = String(per.suffix(12000)) }
        logs[kind] = per
        logText += "[\(kind.title)] " + body
        if logText.count > 20000 {
            logText = String(logText.suffix(16000))
        }
    }

    // 备份等系统提示也进入统一日志，便于在「日志」页查看
    private func appendSystemLog(_ text: String) {
        logText += text.hasSuffix("\n") ? text : text + "\n"
        if logText.count > 20000 {
            logText = String(logText.suffix(16000))
        }
    }

    func clearLog() {
        logText = ""
        logs = [:]
    }

    func logText(for kind: ServiceKind?) -> String {
        guard let kind else { return logText }
        return logs[kind] ?? ""
    }

    func openSystem() {
        NSWorkspace.shared.open(URL(string: "http://localhost:5174")!)
    }

    func chooseRoot() {
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.directoryURL = URL(fileURLWithPath: root)
        panel.prompt = "选择项目目录"
        if panel.runModal() == .OK, let url = panel.url {
            stopAll()
            root = url.path
            UserDefaults.standard.set(root, forKey: rootKey)
            logs = [:]
            logText = ""
            logOffsets = [:]
            if collecting { resetLogOffsets() }
            notice = "项目目录已切换"
        }
    }

    // MARK: 数据备份

    func chooseBackupDestination() {
        guard !isBackingUp else { return }
        let panel = NSOpenPanel()
        panel.canChooseDirectories = true
        panel.canChooseFiles = false
        panel.allowsMultipleSelection = false
        panel.canCreateDirectories = true
        panel.prompt = "选择备份位置"
        if let last = UserDefaults.standard.string(forKey: backupDirKey) {
            panel.directoryURL = URL(fileURLWithPath: last)
        } else {
            panel.directoryURL = FileManager.default.urls(for: .documentDirectory, in: .userDomainMask).first
        }
        guard panel.runModal() == .OK, let url = panel.url else { return }
        UserDefaults.standard.set(url.path, forKey: backupDirKey)
        startBackup(to: url.path)
    }

    func reveal(path: String) {
        NSWorkspace.shared.selectFile(nil, inFileViewerRootedAtPath: path)
    }

    private func startBackup(to directory: String) {
        guard FileManager.default.fileExists(atPath: root) else {
            notice = "项目目录不存在：\(root)"
            return
        }
        isBackingUp = true
        notice = "正在备份…"
        appendSystemLog("[备份] 目标目录：\(directory)")
        let projectRoot = root
        let running = healthy
        DispatchQueue.global(qos: .userInitiated).async { [weak self] in
            do {
                let result = try BackupService.run(projectRoot: projectRoot, destination: directory, running: running)
                DispatchQueue.main.async {
                    guard let self = self else { return }
                    self.isBackingUp = false
                    self.notice = "备份完成：\(result.summary)"
                    self.appendSystemLog(result.log)
                    self.addBackupRecord(BackupRecord(
                        path: result.path,
                        createdAt: Date(),
                        fileCount: result.fileCount,
                        bytes: result.bytes
                    ))
                }
            } catch {
                DispatchQueue.main.async {
                    guard let self = self else { return }
                    self.isBackingUp = false
                    self.notice = "备份失败：\(error.localizedDescription)"
                    self.appendSystemLog("[备份] 失败：\(error.localizedDescription)")
                }
            }
        }
    }

    private func addBackupRecord(_ record: BackupRecord) {
        backups.insert(record, at: 0)
        if backups.count > 30 { backups.removeLast(backups.count - 30) }
        if let data = try? JSONEncoder().encode(backups) {
            UserDefaults.standard.set(data, forKey: backupRecordsKey)
        }
    }
}

// MARK: - 数据备份实现

struct BackupResult {
    let path: String
    let summary: String
    let log: String
    let fileCount: Int
    let bytes: Int
}

struct BackupRecord: Codable, Identifiable, Hashable {
    var id = UUID()
    let path: String
    let createdAt: Date
    let fileCount: Int
    let bytes: Int
}

enum BackupService {
    static func run(projectRoot: String, destination: String, running: [ServiceKind: Bool]) throws -> BackupResult {
        let fm = FileManager.default
        var log = ""
        let stamp = timestamp()
        let base = (destination as NSString).appendingPathComponent("backup-\(stamp)")
        var target = base
        var index = 2
        while fm.fileExists(atPath: target) {
            target = base + "-\(index)"
            index += 1
        }
        try fm.createDirectory(atPath: target, withIntermediateDirectories: true)
        log += "[备份] 创建目录 \(target)\n"

        var files: [[String: Any]] = []
        var integrity: [[String: String]] = []

        // 业务数据库（在线一致性快照）
        if let entry = try backupDatabase(
            source: projectRoot + "/Backend/drvaclaw.db",
            relative: "db/drvaclaw.db",
            target: target,
            files: &files,
            integrity: &integrity,
            log: &log
        ) {
            log += "[备份] 业务数据库 → db/drvaclaw.db（\(entry)）\n"
        }

        // AI 会话数据库
        if let entry = try backupDatabase(
            source: projectRoot + "/Agent/data/agent.sqlite",
            relative: "db/agent.sqlite",
            target: target,
            files: &files,
            integrity: &integrity,
            log: &log
        ) {
            log += "[备份] AI 会话库 → db/agent.sqlite（\(entry)）\n"
        }

        // 大模型配置（含密钥，强制 600 权限）
        let configSource = projectRoot + "/Agent/data/config.json"
        if fm.fileExists(atPath: configSource) {
            let destDir = target + "/config"
            try fm.createDirectory(atPath: destDir, withIntermediateDirectories: true)
            let dest = destDir + "/config.json"
            try fm.copyItem(atPath: configSource, toPath: dest)
            try? fm.setAttributes([.posixPermissions: 0o600], ofItemAtPath: dest)
            files.append(fileEntry(relative: "config/config.json", full: dest, kind: "config", sensitive: true))
            log += "[备份] 大模型配置 → config/config.json（含 API Key，权限 600）\n"
        } else {
            log += "[备份] 跳过大模型配置：未找到 \(configSource)\n"
        }

        // 技能配置
        let skillsSource = projectRoot + "/SKILLS"
        if fm.fileExists(atPath: skillsSource) {
            let destDir = target + "/config"
            try fm.createDirectory(atPath: destDir, withIntermediateDirectories: true)
            let dest = destDir + "/SKILLS"
            try fm.copyItem(atPath: skillsSource, toPath: dest)
            stripPythonCache(dest)
            let (count, bytes) = directoryStat(dest)
            files.append(["path": "config/SKILLS", "kind": "skills", "files": count, "bytes": bytes])
            log += "[备份] 技能配置 → config/SKILLS（\(count) 个文件）\n"
        } else {
            log += "[备份] 跳过技能配置：未找到 \(skillsSource)\n"
        }

        // 清单
        var runningMap: [String: Bool] = [:]
        for kind in ServiceKind.allCases { runningMap[kind.rawValue] = running[kind] ?? false }
        let manifest: [String: Any] = [
            "schema": "drvaclaw-backup/v1",
            "createdAt": isoNow(),
            "projectRoot": projectRoot,
            "servicesRunning": runningMap,
            "files": files,
            "integrity": integrity
        ]
        let data = try JSONSerialization.data(withJSONObject: manifest, options: [.prettyPrinted, .sortedKeys])
        let manifestPath = target + "/manifest.json"
        try data.write(to: URL(fileURLWithPath: manifestPath))

        let (count, bytes) = directoryStat(target)
        let summary = "\(count) 个文件 · \(humanSize(bytes))" + (integrity.isEmpty ? "" : " · 数据库校验通过")
        log += "[备份] 写入 manifest.json 并完成，共 \(summary)\n"
        return BackupResult(path: target, summary: summary, log: log, fileCount: count, bytes: bytes)
    }

    private static func backupDatabase(
        source: String,
        relative: String,
        target: String,
        files: inout [[String: Any]],
        integrity: inout [[String: String]],
        log: inout String
    ) throws -> String? {
        let fm = FileManager.default
        guard fm.fileExists(atPath: source) else {
            log += "[备份] 跳过数据库：未找到 \(source)\n"
            return nil
        }
        let destDir = target + "/db"
        try fm.createDirectory(atPath: destDir, withIntermediateDirectories: true)
        let dest = target + "/" + relative

        // 优先用 sqlite3 .backup 生成一致性快照（服务运行中也安全）
        var mode = "文件复制"
        let sqlite = "/usr/bin/sqlite3"
        if fm.isExecutableFile(atPath: sqlite) {
            let (code, _) = runProcess(sqlite, [source, ".backup \(dest)"])
            if code == 0, fm.fileExists(atPath: dest) {
                mode = "一致性快照"
            } else {
                try? fm.removeItem(atPath: dest)
            }
        }
        if mode == "文件复制" {
            try fm.copyItem(atPath: source, toPath: dest)
        }

        let check = integrityCheck(dest)
        // 清理校验过程产生的 WAL/SHM 伴生文件（SHM 为临时共享内存，WAL 仅在为空时删除）
        try? fm.removeItem(atPath: dest + "-shm")
        if let attrs = try? fm.attributesOfItem(atPath: dest + "-wal"),
           let size = attrs[.size] as? NSNumber, size.intValue == 0 {
            try? fm.removeItem(atPath: dest + "-wal")
        }
        integrity.append(["file": relative, "result": check])
        files.append(fileEntry(relative: relative, full: dest, kind: "database"))
        return "\(mode)，完整性 \(check)"
    }

    private static func integrityCheck(_ path: String) -> String {
        let (code, output) = runProcess("/usr/bin/sqlite3", [path, "PRAGMA integrity_check;"])
        guard code == 0 else { return "无法校验" }
        let value = output.trimmingCharacters(in: .whitespacesAndNewlines)
        return value.isEmpty ? "未知" : value
    }

    private static func runProcess(_ tool: String, _ args: [String]) -> (Int32, String) {
        guard FileManager.default.isExecutableFile(atPath: tool) else { return (-1, "") }
        let process = Process()
        process.executableURL = URL(fileURLWithPath: tool)
        process.arguments = args
        let pipe = Pipe()
        process.standardOutput = pipe
        process.standardError = pipe
        do {
            try process.run()
        } catch {
            return (-1, error.localizedDescription)
        }
        let data = pipe.fileHandleForReading.readDataToEndOfFile()
        process.waitUntilExit()
        return (process.terminationStatus, String(data: data, encoding: .utf8) ?? "")
    }

    private static func fileEntry(relative: String, full: String, kind: String, sensitive: Bool = false) -> [String: Any] {
        var entry: [String: Any] = ["path": relative, "kind": kind]
        if let attrs = try? FileManager.default.attributesOfItem(atPath: full),
           let size = attrs[.size] as? NSNumber {
            entry["bytes"] = size.intValue
        }
        entry["sha256"] = sha256(full)
        if sensitive { entry["sensitive"] = true }
        return entry
    }

    private static func sha256(_ path: String) -> String {
        guard let handle = try? FileHandle(forReadingFrom: URL(fileURLWithPath: path)) else { return "" }
        defer { try? handle.close() }
        var hasher = SHA256()
        while true {
            let chunk = handle.readData(ofLength: 1 << 20)
            if chunk.isEmpty { break }
            hasher.update(data: chunk)
        }
        return hasher.finalize().map { String(format: "%02x", $0) }.joined()
    }

    private static func stripPythonCache(_ root: String) {
        let fm = FileManager.default
        var stack = [root]
        while let dir = stack.popLast() {
            guard let items = try? fm.contentsOfDirectory(atPath: dir) else { continue }
            for item in items {
                let full = dir + "/" + item
                if item == "__pycache__" || item == ".DS_Store" {
                    try? fm.removeItem(atPath: full)
                } else {
                    var isDir: ObjCBool = false
                    if fm.fileExists(atPath: full, isDirectory: &isDir), isDir.boolValue {
                        stack.append(full)
                    }
                }
            }
        }
    }

    private static func directoryStat(_ path: String) -> (Int, Int) {
        let fm = FileManager.default
        guard let enumerator = fm.enumerator(atPath: path) else { return (0, 0) }
        var count = 0
        var bytes = 0
        for case let item as String in enumerator {
            let full = path + "/" + item
            var isDir: ObjCBool = false
            guard fm.fileExists(atPath: full, isDirectory: &isDir), !isDir.boolValue else { continue }
            count += 1
            if let attrs = try? fm.attributesOfItem(atPath: full), let size = attrs[.size] as? NSNumber {
                bytes += size.intValue
            }
        }
        return (count, bytes)
    }

    static func humanSize(_ bytes: Int) -> String {
        let kb = Double(bytes) / 1024
        return kb >= 1024 ? String(format: "%.1f MB", kb / 1024) : String(format: "%.0f KB", kb)
    }

    private static func timestamp() -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.dateFormat = "yyyyMMdd-HHmmss"
        return formatter.string(from: Date())
    }

    private static func isoNow() -> String {
        let formatter = ISO8601DateFormatter()
        return formatter.string(from: Date())
    }
}

// MARK: - 界面

struct ContentView: View {
    @ObservedObject var model: AppModel

    var body: some View {
        TabView {
            systemTab
                .tabItem { Label("系统", systemImage: "square.grid.2x2") }
            logTab
                .tabItem { Label("日志", systemImage: "doc.text") }
            backupTab
                .tabItem { Label("备份", systemImage: "externaldrive") }
        }
        .frame(width: 760, height: 660)
    }

    // MARK: 系统

    private var systemTab: some View {
        VStack(alignment: .leading, spacing: 0) {
            header
            Divider().padding(.vertical, 14)
            VStack(spacing: 10) {
                ForEach(ServiceKind.allCases) { kind in
                    ServiceRow(kind: kind, model: model)
                }
            }
            Spacer(minLength: 0)
            footer
        }
        .padding(20)
    }

    private var header: some View {
        HStack(alignment: .top) {
            VStack(alignment: .leading, spacing: 4) {
                Text("驾驶智陪工作台 · 服务控制台")
                    .font(.system(size: 17, weight: .semibold))
                Text("三个服务独立启停，关闭窗口会同时停止全部服务")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
            }
            Spacer()
            HStack(spacing: 8) {
                Button("全部启动") { model.startAll() }
                Button("全部停止") { model.stopAll() }
                Button("打开系统") { model.openSystem() }
                    .buttonStyle(.borderedProminent)
            }
        }
    }

    private var footer: some View {
        HStack(spacing: 8) {
            Image(systemName: "folder")
                .foregroundColor(.secondary)
            Text(model.root)
                .font(.system(size: 10.5))
                .foregroundColor(.secondary)
                .lineLimit(1)
                .truncationMode(.middle)
                .help(model.root)
            Spacer()
            if !model.notice.isEmpty {
                Text(model.notice)
                    .font(.system(size: 10.5))
                    .foregroundColor(.orange)
                    .lineLimit(1)
            }
            Button("选择目录…") { model.chooseRoot() }
                .font(.system(size: 11))
        }
        .padding(.top, 10)
    }

    // MARK: 日志

    private var displayLog: String { model.logText(for: model.logFilter.kind) }

    private var emptyLogText: String {
        if !displayLog.isEmpty { return displayLog }
        if !model.collecting { return "日志收集未开启。点击右上角「开始收集」后，新的服务输出会显示在这里。" }
        return "暂无日志。去「系统」页启动服务后，输出会实时显示在这里。"
    }

    private var logTab: some View {
        VStack(alignment: .leading, spacing: 10) {
            HStack {
                Text("服务日志")
                    .font(.system(size: 17, weight: .semibold))
                Spacer()
                Picker("", selection: $model.logFilter) {
                    ForEach(LogFilter.allCases) { filter in
                        Text(filter.title).tag(filter)
                    }
                }
                .pickerStyle(.segmented)
                .labelsHidden()
                .frame(width: 320)
                Button(model.collecting ? "停止收集" : "开始收集") {
                    if model.collecting { model.stopCollecting() } else { model.startCollecting() }
                }
                .buttonStyle(.borderedProminent)
                .font(.system(size: 11))
                Button("清空") { model.clearLog() }
                    .font(.system(size: 11))
            }
            Text(model.collecting
                 ? "正在收集服务终端输出，最新内容在底部。备份过程也会记录在这里。"
                 : "为避免日志过载，日志收集默认关闭。点击「开始收集」后开始读取服务输出。")
                .font(.system(size: 11))
                .foregroundColor(.secondary)
            ScrollViewReader { proxy in
                ScrollView {
                    Text(emptyLogText)
                        .font(.system(size: 10.5, design: .monospaced))
                        .foregroundColor(displayLog.isEmpty ? .secondary : .primary)
                        .frame(maxWidth: .infinity, alignment: .leading)
                        .textSelection(.enabled)
                        .padding(10)
                        .id("logBottom")
                }
                .onChange(of: displayLog) { _ in
                    proxy.scrollTo("logBottom", anchor: .bottom)
                }
            }
            .frame(maxWidth: .infinity, maxHeight: .infinity)
            .background(RoundedRectangle(cornerRadius: 6).fill(Color(nsColor: .textBackgroundColor)))
            .overlay(RoundedRectangle(cornerRadius: 6).stroke(Color(nsColor: .separatorColor), lineWidth: 0.5))
        }
        .padding(20)
    }

    // MARK: 备份

    private var backupTab: some View {
        VStack(alignment: .leading, spacing: 12) {
            HStack(alignment: .top) {
                VStack(alignment: .leading, spacing: 4) {
                    Text("数据备份")
                        .font(.system(size: 17, weight: .semibold))
                    Text("完整备份业务数据库、AI 会话库、大模型配置与技能配置，每次备份时选择保存位置。")
                        .font(.system(size: 11))
                        .foregroundColor(.secondary)
                }
                Spacer()
                Button(model.isBackingUp ? "备份中…" : "数据备份") { model.chooseBackupDestination() }
                    .buttonStyle(.borderedProminent)
                    .disabled(model.isBackingUp)
            }
            if model.notice.contains("备份") {
                Text(model.notice)
                    .font(.system(size: 11))
                    .foregroundColor(isFailure ? .red : .secondary)
                    .lineLimit(2)
            }
            Divider()
            HStack(spacing: 8) {
                Text("备份记录")
                    .font(.system(size: 13, weight: .semibold))
                Text("\(model.backups.count) 条")
                    .font(.system(size: 11))
                    .foregroundColor(.secondary)
                Spacer()
            }
            if model.backups.isEmpty {
                VStack(spacing: 8) {
                    Spacer()
                    Image(systemName: "externaldrive")
                        .font(.system(size: 26))
                        .foregroundColor(Color(nsColor: .tertiaryLabelColor))
                    Text("还没有备份记录")
                        .font(.system(size: 12))
                        .foregroundColor(.secondary)
                    Text("点击右上角「数据备份」开始第一次备份。")
                        .font(.system(size: 10.5))
                        .foregroundColor(.secondary)
                    Spacer()
                }
                .frame(maxWidth: .infinity)
            } else {
                ScrollView {
                    VStack(spacing: 8) {
                        ForEach(model.backups) { record in
                            BackupRow(record: record, model: model)
                        }
                    }
                }
                .frame(maxWidth: .infinity, maxHeight: .infinity)
            }
        }
        .padding(20)
        .frame(maxWidth: .infinity, maxHeight: .infinity, alignment: .topLeading)
    }

    private var isFailure: Bool {
        model.notice.hasPrefix("备份失败") || model.notice.contains("不存在")
    }
}

struct ServiceRow: View {
    let kind: ServiceKind
    @ObservedObject var model: AppModel

    private var healthy: Bool { model.healthy[kind] ?? false }
    private var starting: Bool { model.starting.contains(kind) }

    private var statusText: String {
        if starting && !healthy { return "启动中…" }
        return healthy ? "运行中" : "已停止"
    }

    private var statusColor: Color {
        if healthy { return .green }
        if starting { return .orange }
        return Color(nsColor: .tertiaryLabelColor)
    }

    var body: some View {
        HStack(spacing: 12) {
            Image(systemName: kind.symbol)
                .font(.system(size: 16))
                .foregroundColor(.accentColor)
                .frame(width: 24)

            VStack(alignment: .leading, spacing: 2) {
                Text(kind.title)
                    .font(.system(size: 13, weight: .medium))
                Text(kind.detail)
                    .font(.system(size: 10.5))
                    .foregroundColor(.secondary)
            }

            Spacer()

            Text(":\(String(kind.port))")
                .font(.system(size: 10.5, design: .monospaced))
                .foregroundColor(.secondary)

            HStack(spacing: 5) {
                Circle().fill(statusColor).frame(width: 7, height: 7)
                Text(statusText)
                    .font(.system(size: 11))
                    .foregroundColor(statusColor)
                    .frame(width: 52, alignment: .leading)
            }

            Button(healthy || starting ? "停止" : "启动") {
                if healthy || starting {
                    model.stop(kind)
                } else {
                    model.start(kind)
                }
            }
            .frame(width: 62)
            .disabled(starting)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 10)
        .background(RoundedRectangle(cornerRadius: 8).fill(Color(nsColor: .controlBackgroundColor)))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(nsColor: .separatorColor), lineWidth: 0.5))
    }
}

struct BackupRow: View {
    let record: BackupRecord
    @ObservedObject var model: AppModel

    private var exists: Bool { FileManager.default.fileExists(atPath: record.path) }

    private var timeText: String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "zh_CN")
        formatter.dateFormat = "yyyy-MM-dd HH:mm:ss"
        return formatter.string(from: record.createdAt)
    }

    var body: some View {
        HStack(alignment: .top, spacing: 10) {
            Image(systemName: exists ? "externaldrive.fill" : "exclamationmark.triangle.fill")
                .font(.system(size: 14))
                .foregroundColor(exists ? .accentColor : .orange)
                .frame(width: 20)

            VStack(alignment: .leading, spacing: 3) {
                HStack(spacing: 8) {
                    Text(timeText)
                        .font(.system(size: 12, weight: .medium))
                    Text("\(record.fileCount) 个文件 · \(BackupService.humanSize(record.bytes))")
                        .font(.system(size: 10.5))
                        .foregroundColor(.secondary)
                    if !exists {
                        Text("已缺失")
                            .font(.system(size: 10))
                            .foregroundColor(.orange)
                    }
                }
                Text(record.path)
                    .font(.system(size: 10.5, design: .monospaced))
                    .foregroundColor(.secondary)
                    .lineLimit(1)
                    .truncationMode(.middle)
                    .help(record.path)
            }

            Spacer(minLength: 8)

            Button("在访达显示") { model.reveal(path: record.path) }
                .font(.system(size: 10.5))
                .disabled(!exists)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 9)
        .background(RoundedRectangle(cornerRadius: 8).fill(Color(nsColor: .controlBackgroundColor)))
        .overlay(RoundedRectangle(cornerRadius: 8).stroke(Color(nsColor: .separatorColor), lineWidth: 0.5))
    }
}

// MARK: - 入口

final class AppDelegate: NSObject, NSApplicationDelegate {
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool {
        true
    }

    // 无界面备份入口，便于自动化验证：DrvaclawLauncher --backup-to <目录>
    func applicationDidFinishLaunching(_ notification: Notification) {
        let args = CommandLine.arguments
        guard let index = args.firstIndex(of: "--backup-to"), index + 1 < args.count else { return }
        let destination = args[index + 1]
        let model = AppModel.shared
        do {
            let result = try BackupService.run(
                projectRoot: model.root,
                destination: destination,
                running: model.healthy
            )
            print("PATH: \(result.path)")
            print("SUMMARY: \(result.summary)")
            print(result.log, terminator: "")
            exit(0)
        } catch {
            FileHandle.standardError.write(Data("BACKUP FAILED: \(error.localizedDescription)\n".utf8))
            exit(1)
        }
    }

    func applicationWillTerminate(_ notification: Notification) {
        AppModel.shared.stopAll()
        Thread.sleep(forTimeInterval: 0.5)
    }
}

@main
struct DrvaclawLauncherApp: App {
    @NSApplicationDelegateAdaptor(AppDelegate.self) private var delegate

    var body: some Scene {
        WindowGroup("驾驶智陪工作台 · 服务控制台") {
            ContentView(model: .shared)
        }
        .windowResizability(.contentSize)
        .commands {
            CommandGroup(replacing: .newItem) {}
        }
    }
}

# Private Skills

这是一组面向本地网页工具、浏览器采集、流媒体偏好分析和 GitHub 发布的 Codex skills。

## Skills 总览

| Skill | 主要用途 |
|---|---|
| `media-usage-report` | 采集、整理和分析视频、音乐、阅读等流媒体使用记录，生成用户偏好报告。 |
| `local-browser-bridge-debug` | 诊断网页工具、bb-browser、Chrome CDP、普通 Chrome/Edge、PyCharm 和 Codex 环境之间的浏览器桥接问题。 |
| `windows-local-service-lifecycle` | 管理 Windows 本地 Web 服务、采集服务、浏览器进程和子进程的启动、端口复用及关闭。 |
| `project-anchor-management` | 管理项目中的锚点版本、用户确认的基准、变更边界和安全回退。 |
| `git-push-guide` | 审核本地文件并安全提交、推送到 GitHub，处理认证、网络和 Git HTTPS 异常。 |

## 详细说明

### 1. media-usage-report

用于构建流媒体用户偏好画像。它覆盖以下工作：

- 确定平台、时间范围、设备范围和数据来源。
- 合并浏览器、账号、App、导出文件或手动记录。
- 按标题、作者、UP 主、歌手、标签和内容类型进行分类。
- 统计观看量、活跃天数、活跃时段、常看创作者和内容类型。
- 生成包含文字解读、统计卡片、趋势图表、排名和记录抽样的 HTML 报告。

适用场景：用户希望分析 B 站、抖音、小红书、微博、YouTube、音乐平台、阅读平台等历史使用记录时使用。

### 2. local-browser-bridge-debug

用于处理“网页工具需要访问已登录浏览器”这一类问题。重点是区分：

- Codex 提供的 Chrome 控制连接器。
- bb-browser 及其浏览器守护进程。
- Chrome CDP 端口和浏览器 profile。
- 普通 Chrome/Edge 与采集专用浏览器。
- Python、PyCharm、PowerShell 和 Codex 沙箱的权限差异。

它适合排查 CDP 端口无法连接、权限错误、登录态未复用、浏览器窗口重复打开、刷新页面意外触发采集，以及“外部命令行能运行但 Codex 中失败”等问题。

### 3. windows-local-service-lifecycle

用于管理 Windows 本地项目的进程生命周期。它关注：

- Web 服务、采集服务、浏览器守护进程和浏览器窗口的进程边界。
- 启动顺序、健康检查、就绪状态和端口占用。
- PyCharm、PowerShell 或 `run.py` 启动时的子进程管理。
- 旧进程、孤儿进程、端口复用和错误服务残留。
- 正常退出、优雅关闭和仅停止项目自己创建的进程。

适用场景：本地服务启动后卡住、启动了旧代码、刷新页面复用旧服务、关闭 PyCharm 后采集服务仍残留时使用。

### 4. project-anchor-management

用于保护项目开发过程中的重要基准。例如用户确认“当前版本为锚点 A”或“当前版本为锚点 B”时，skill 会帮助记录：

- 锚点对应的功能和行为。
- 分支、提交、运行地址和测试结果。
- 浏览器登录态来源、服务端口等运行条件。
- 锚点之后新增的修改和不应被覆盖的用户文件。

适用场景：需要对比当前版本与锚点、回退到已确认版本、避免误删后续修改，或需要进行阶段性验收时使用。

### 5. git-push-guide

用于把项目安全发布到 GitHub。主要流程包括：

1. 检查项目说明、当前分支、远程仓库和工作区状态。
2. 审核 PDF、Excel、数据库、浏览器 profile、Cookie、`.env`、token 和生成文件。
3. 只暂存明确允许发布的文件，避免盲目使用 `git add -A`。
4. 提交前检查 staged diff、提交统计和敏感文件模式。
5. 优先使用普通 Git push，失败后再诊断认证、网络或分支保护问题。
6. 必要时使用 GitHub CLI/API 作为受控备用方案。

它还明确区分 GitHub 网页登录状态、Git 凭据和本地仓库状态，避免因为浏览器已打开 GitHub 就误判 Git push 一定可用。

## 推荐协作顺序

开发本地流媒体查询工具时，推荐按以下顺序使用：

1. 使用 `project-anchor-management` 记录当前锚点和变更边界。
2. 使用 `local-browser-bridge-debug` 确认登录态、CDP 和浏览器桥接方式。
3. 使用 `windows-local-service-lifecycle` 设计并检查 Web/采集服务的启动与关闭。
4. 使用 `media-usage-report` 处理记录、分类、统计和报告生成。
5. 使用 `git-push-guide` 审核文件并发布到 GitHub。

## 使用原则

- 先确认数据来源，再修改采集逻辑。
- 健康检查接口应保持只读，不应因为刷新页面而自动打开浏览器。
- 只管理当前项目创建的进程，不要随意结束用户自己的 Chrome/Edge。
-  named anchor 只作为比较基准，不代表可以覆盖锚点之后的用户修改。
- 发布到公共仓库前，默认把账号数据、浏览器 profile、Cookie、数据库和原始记录视为敏感内容。


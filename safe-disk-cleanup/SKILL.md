---
name: safe-disk-cleanup
description: Use when a Windows drive is low on space or Codex/development work has left behind caches, temporary files, package caches, browser caches, or other suspected regenerable artifacts that need safe cross-drive cleanup.
---

# Safe Disk Cleanup

## Overview

按“审计—预览—确认—执行—验证”处理 Windows 盘符清理。默认只读、只接受精确目录、跳过重解析点和被占用文件，并把日志和非系统工作产物优先放到 `F:\codex`。

## Required Workflow

1. **审计**：先运行脚本的 `Scan` 模式，记录盘符、准确路径、大小、最近修改时间、可再生成性、所属应用和风险。
2. **预览**：把候选项缩小到明确的目录白名单，运行 `Preview`，检查它不会触及凭据、数据库、项目或系统目录。
3. **确认**：把每个候选的路径、大小、风险、可能副作用和预计收益展示给用户；没有明确确认时不得执行 `Clean`。
4. **执行**：只传入用户确认过的精确目录。脚本保留目录本身，逐项删除内容；遇到重解析点或锁定文件就跳过并记录。
5. **验证**：重新统计大小和文件数，检查日志、关键应用启动情况，并报告实际释放量和未处理原因。

## Quick Reference

| 目标 | 做法 |
|---|---|
| 扫描候选 | `powershell -File scripts\clean_disk.ps1 -Mode Scan -Roots C:\,D:\,F:\` |
| 预览精确目录 | `powershell -File scripts\clean_disk.ps1 -Mode Preview -TargetPaths <精确目录>` |
| 执行已确认目录 | `powershell -File scripts\clean_disk.ps1 -Mode Clean -Confirmed -TargetPaths <已确认目录>` |
| 日志位置 | 默认 `F:\codex\logs\disk-cleanup`，可用 `-LogPath` 覆盖 |

## Safety Boundaries

- 永远拒绝盘符根目录、`Windows`、`Program Files`、`Program Files (x86)`、`WindowsApps`、已安装程序目录、用户文档、项目、备份、数据库、Cookie、令牌、SSH 密钥和 Codex 登录/状态目录。
- `CODEX_HOME` 已设置时，继续使用它保存 Codex 状态；不要把 `auth.json`、SQLite、会话、日志或浏览器 profile 当作普通缓存。Codex 的非系统产物默认使用 `F:\codex`。
- 文件名含 `cache` 或 `temp` 不是删除依据；必须确认目录归属、可再生成性和风险。
- 不使用 `Remove-Item C:\...\*` 这类未审计通配符，不跟随符号链接/联接点，不为“越快越好”关闭确认。
- 不停止用户进程来强行删除锁定文件；清理失败的项目留给用户在关闭对应应用后重新确认。

## Path Placement

- 会话、技能、日志、脚本、项目输出、临时工作目录和可再生开发缓存优先放在 `F:\codex`。
- 必须留在 C 盘的内容仅限 Windows 应用安装目录、系统组件、硬件/驱动运行时以及用户明确要求保留的底层依赖。
- 运行清理脚本时把 `-LogPath` 指向 F 盘；不要在 C 盘创建报告、备份或中间产物。

## Common Mistakes

- 把 `npm-cache`、`npx` 缓存当成项目依赖：它们通常可再生成，但会影响离线构建和下载速度，必须单独列项确认。
- 把 WebView 的 `Cache` 与登录状态混为一谈：只处理明确的缓存目录，不碰同级的 `Login Data`、`History`、`Local Storage` 或数据库。
- 把 C 盘运行时迁移到 F 盘：先确认是否由安装器管理；未经验证的移动会导致 Codex 或插件无法启动。
- 把“清理完成”理解成“所有候选都消失”：锁定、权限不足或重解析点都必须在结果中报告。

脚本位于 `scripts/clean_disk.ps1`。它不负责判断“无用”，只负责执行已经完成审计和确认的精确路径操作。

<!-- 以下是初始化脚本留下的模板说明，保留但不作为 skill 指令。 -->
## Structuring This Skill

[TODO: Choose the structure that best fits this skill's purpose. Common patterns:

**1. Workflow-Based** (best for sequential processes)
- Works well when there are clear step-by-step procedures
- Example: DOCX skill with "Workflow Decision Tree" -> "Reading" -> "Creating" -> "Editing"
- Structure: ## Overview -> ## Workflow Decision Tree -> ## Step 1 -> ## Step 2...

**2. Task-Based** (best for tool collections)
- Works well when the skill offers different operations/capabilities
- Example: PDF skill with "Quick Start" -> "Merge PDFs" -> "Split PDFs" -> "Extract Text"
- Structure: ## Overview -> ## Quick Start -> ## Task Category 1 -> ## Task Category 2...

**3. Reference/Guidelines** (best for standards or specifications)
- Works well for brand guidelines, coding standards, or requirements
- Example: Brand styling with "Brand Guidelines" -> "Colors" -> "Typography" -> "Features"
- Structure: ## Overview -> ## Guidelines -> ## Specifications -> ## Usage...

**4. Capabilities-Based** (best for integrated systems)
- Works well when the skill provides multiple interrelated features
- Example: Product Management with "Core Capabilities" -> numbered capability list
- Structure: ## Overview -> ## Core Capabilities -> ### 1. Feature -> ### 2. Feature...

Patterns can be mixed and matched as needed. Most skills combine patterns (e.g., start with task-based, add workflow for complex operations).

Delete this entire "Structuring This Skill" section when done - it's just guidance.]

## [TODO: Replace with the first main section based on chosen structure]

[TODO: Add content here. See examples in existing skills:
- Code samples for technical skills
- Decision trees for complex workflows
- Concrete examples with realistic user requests
- References to scripts/templates/references as needed]

## Resources (optional)

Create only the resource directories this skill actually needs. Delete this section if no resources are required.

### scripts/
Executable code (Python/Bash/etc.) that can be run directly to perform specific operations.

**Examples from other skills:**
- PDF skill: `fill_fillable_fields.py`, `extract_form_field_info.py` - utilities for PDF manipulation
- DOCX skill: `document.py`, `utilities.py` - Python modules for document processing

**Appropriate for:** Python scripts, shell scripts, or any executable code that performs automation, data processing, or specific operations.

**Note:** Scripts may be executed without loading into context, but can still be read by Codex for patching or environment adjustments.

### references/
Documentation and reference material intended to be loaded into context to inform Codex's process and thinking.

**Examples from other skills:**
- Product management: `communication.md`, `context_building.md` - detailed workflow guides
- BigQuery: API reference documentation and query examples
- Finance: Schema documentation, company policies

**Appropriate for:** In-depth documentation, API references, database schemas, comprehensive guides, or any detailed information that Codex should reference while working.

### assets/
Files not intended to be loaded into context, but rather used within the output Codex produces.

**Examples from other skills:**
- Brand styling: PowerPoint template files (.pptx), logo files
- Frontend builder: HTML/React boilerplate project directories
- Typography: Font files (.ttf, .woff2)

**Appropriate for:** Templates, boilerplate code, document templates, images, icons, fonts, or any files meant to be copied or used in the final output.

---

**Not every skill requires all three types of resources.**
-->

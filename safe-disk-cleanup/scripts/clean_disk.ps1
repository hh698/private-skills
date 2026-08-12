[CmdletBinding()]
param(
    [ValidateSet('Scan', 'Preview', 'Clean')]
    [string]$Mode = 'Scan',
    [string[]]$Roots = @('C:\', 'D:\', 'F:\'),
    [string[]]$TargetPaths = @(),
    [switch]$Confirmed,
    [string]$LogPath = 'F:\codex\logs\disk-cleanup'
)

$ErrorActionPreference = 'Stop'

# 这些名称只用于生成候选清单，不代表可以自动删除。
$CandidateNames = @(
    'Cache', 'Code Cache', 'GPUCache', 'ShaderCache', 'GrShaderCache',
    'Temp', 'npm-cache', 'node-gyp', '_cacache', '_npx'
)

# 这些路径或目录名包含用户数据、系统组件、凭据或已安装程序，始终拒绝处理。
$ProtectedPattern = '(?i)(^|\\)(Windows|WindowsApps|Program Files|Program Files \(x86\)|Documents|Desktop|Pictures|Videos|Music|Downloads|\.codex)(\\|$)|(^|\\)(auth\.json|.*\.sqlite(-.*)?|Login Data|History|Local Storage|Cookies)(\\|$)'

function Get-DirectoryStats {
    param([Parameter(Mandatory)][string]$Path)

    $item = Get-Item -LiteralPath $Path -Force -ErrorAction Stop
    if (-not $item.PSIsContainer) { throw "目标不是目录：$Path" }
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "拒绝处理重解析点：$Path"
    }

    $files = @(Get-ChildItem -LiteralPath $Path -Force -File -Recurse -ErrorAction SilentlyContinue)
    $sum = ($files | Measure-Object -Property Length -Sum).Sum
    if ($null -eq $sum) { $sum = 0 }

    [pscustomobject]@{
        Path = $Path
        Files = $files.Count
        SizeBytes = [int64]$sum
        SizeMB = [math]::Round($sum / 1MB, 1)
        NewestWrite = ($files | Sort-Object LastWriteTime -Descending | Select-Object -First 1 -ExpandProperty LastWriteTime)
    }
}

function Assert-SafeTarget {
    param([Parameter(Mandatory)][string]$Path)

    $full = [IO.Path]::GetFullPath($Path).TrimEnd('\')
    if ($full -match '^[A-Za-z]:$') { throw "拒绝处理盘符根目录：$full" }
    if ($full -match $ProtectedPattern) { throw "命中受保护路径或目录名：$full" }
    if (-not (Test-Path -LiteralPath $full -PathType Container)) { throw "目录不存在：$full" }

    $item = Get-Item -LiteralPath $full -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "拒绝处理重解析点：$full"
    }
    return $full
}

function Write-CleanupLog {
    param([Parameter(Mandatory)][object]$Record)

    # 日志默认放在 F 盘，避免清理流程继续制造 C 盘中间文件。
    New-Item -ItemType Directory -Force -Path $LogPath | Out-Null
    $file = Join-Path $LogPath ("cleanup-{0}.json" -f (Get-Date -Format 'yyyyMMdd-HHmmss'))
    $Record | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $file -Encoding UTF8
    Write-Output "LogPath=$file"
}

if ($Mode -eq 'Scan') {
    $results = @()
    foreach ($root in $Roots) {
        if (-not (Test-Path -LiteralPath $root -PathType Container)) { continue }
        $dirs = @(Get-ChildItem -LiteralPath $root -Directory -Force -Recurse -Depth 5 -ErrorAction SilentlyContinue |
            Where-Object {
                $CandidateNames -contains $_.Name -and
                $_.FullName -notmatch $ProtectedPattern -and
                ($_.Attributes -band [IO.FileAttributes]::ReparsePoint) -eq 0
            })
        foreach ($dir in $dirs) {
            try { $results += Get-DirectoryStats -Path $dir.FullName } catch { }
        }
    }
    $results | Sort-Object SizeBytes -Descending | Select-Object Path, Files, SizeMB, NewestWrite | Format-Table -AutoSize
    return
}

if ($TargetPaths.Count -eq 0) { throw "Preview 或 Clean 必须提供 -TargetPaths 精确目录。" }

$safePaths = @($TargetPaths | ForEach-Object { Assert-SafeTarget -Path $_ })

if ($Mode -eq 'Preview') {
    $safePaths | ForEach-Object { Get-DirectoryStats -Path $_ } |
        Select-Object Path, Files, SizeMB, NewestWrite | Format-Table -AutoSize
    return
}

if (-not $Confirmed) {
    throw "Clean 模式必须显式传入 -Confirmed；先向用户展示 Preview 结果并取得明确授权。"
}

$before = @($safePaths | ForEach-Object { Get-DirectoryStats -Path $_ })
$deleted = @()
$skipped = @()
$failed = @()

foreach ($path in $safePaths) {
    foreach ($child in @(Get-ChildItem -LiteralPath $path -Force -ErrorAction SilentlyContinue)) {
        if (($child.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) {
            $skipped += [pscustomobject]@{Path=$child.FullName; Reason='重解析点'}
            continue
        }
        try {
            Remove-Item -LiteralPath $child.FullName -Recurse -Force -ErrorAction Stop
            $deleted += $child.FullName
        } catch {
            $failed += [pscustomobject]@{Path=$child.FullName; Reason=$_.Exception.Message}
        }
    }
}

$after = @($safePaths | ForEach-Object { Get-DirectoryStats -Path $_ })
$summary = [pscustomobject]@{
    Mode = $Mode
    Timestamp = Get-Date
    Before = $before
    After = $after
    DeletedTopLevelItems = $deleted.Count
    Skipped = $skipped
    Failed = $failed
}

$after | Select-Object Path, Files, SizeMB, NewestWrite | Format-Table -AutoSize
Write-Output "DeletedTopLevelItems=$($deleted.Count)"
Write-Output "SkippedItems=$($skipped.Count)"
Write-Output "FailedItems=$($failed.Count)"
Write-CleanupLog -Record $summary

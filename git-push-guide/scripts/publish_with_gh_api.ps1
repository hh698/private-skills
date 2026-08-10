param(
    [Parameter(Mandatory = $true)]
    [string]$Repository,

    [string]$Branch = "main",

    [string]$Message = "chore: publish project",

    [string]$BlockPattern = "output|\\.xlsx$|\\.docx$|\\.pdf$|\\.env$|secret|token|credential|cookie|session",

    [switch]$Force
)

$ErrorActionPreference = "Stop"
$enc = [System.Text.UTF8Encoding]::new($false)

function Invoke-GhJson {
    param(
        [Parameter(Mandatory = $true)] [string]$Method,
        [Parameter(Mandatory = $true)] [string]$Endpoint,
        [Parameter(Mandatory = $true)] [hashtable]$Object
    )

    $tmp = Join-Path $env:TEMP ("gh-payload-" + [guid]::NewGuid().ToString() + ".json")
    try {
        $payload = $Object | ConvertTo-Json -Depth 30 -Compress
        [System.IO.File]::WriteAllText($tmp, $payload, $enc)
        $raw = gh api -X $Method $Endpoint --input $tmp
        if ($LASTEXITCODE -ne 0) {
            throw "gh api failed: $Endpoint"
        }
        return ($raw | ConvertFrom-Json)
    }
    finally {
        if (Test-Path $tmp) {
            Remove-Item -LiteralPath $tmp -Force
        }
    }
}

function Invoke-GhRaw {
    param([Parameter(Mandatory = $true)] [string]$Endpoint)
    $raw = gh api $Endpoint
    if ($LASTEXITCODE -ne 0) {
        throw "gh api failed: $Endpoint"
    }
    return ($raw | ConvertFrom-Json)
}

$gitRoot = git rev-parse --show-toplevel
if ($LASTEXITCODE -ne 0) {
    throw "Current directory is not inside a Git repository."
}
Set-Location $gitRoot

$status = git status --short
if ($status) {
    Write-Warning "Working tree has changes. Commit or intentionally stage/amend before publishing."
    $status
    throw "Refusing to publish a dirty working tree."
}

$files = git ls-files
if (-not $files) {
    throw "No tracked files found."
}

$blocked = $files | Select-String -Pattern $BlockPattern
if ($blocked) {
    Write-Error "Blocked tracked files matched sensitive pattern:"
    $blocked | ForEach-Object { Write-Error $_.Line }
    throw "Refusing to publish until tracked file scope is cleaned."
}

$auth = gh auth status 2>&1
if ($LASTEXITCODE -ne 0) {
    $auth
    throw "GitHub CLI is not authenticated. Run: gh auth login -h github.com"
}

$ref = Invoke-GhRaw "repos/$Repository/git/ref/heads/$Branch"
$parent = $ref.object.sha
$parentCommit = Invoke-GhRaw "repos/$Repository/git/commits/$parent"

$treeItems = @()
foreach ($file in $files) {
    $full = Join-Path $gitRoot $file
    $bytes = [System.IO.File]::ReadAllBytes($full)
    $blob = Invoke-GhJson "POST" "repos/$Repository/git/blobs" @{
        content = [Convert]::ToBase64String($bytes)
        encoding = "base64"
    }
    $treeItems += @{
        path = ($file -replace "\\", "/")
        mode = "100644"
        type = "blob"
        sha = $blob.sha
    }
}

$tree = Invoke-GhJson "POST" "repos/$Repository/git/trees" @{
    base_tree = $parentCommit.tree.sha
    tree = $treeItems
}

$commit = Invoke-GhJson "POST" "repos/$Repository/git/commits" @{
    message = $Message
    tree = $tree.sha
    parents = @($parent)
}

Invoke-GhJson "PATCH" "repos/$Repository/git/refs/heads/$Branch" @{
    sha = $commit.sha
    force = [bool]$Force
} | Out-Null

Write-Output "Published commit: $($commit.sha)"
Write-Output "Commit URL: https://github.com/$Repository/commit/$($commit.sha)"
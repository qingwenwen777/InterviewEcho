[CmdletBinding()]
param(
    [string]$ServerHost = "154.36.185.85",
    [string]$ServerUser = "root",
    [string]$RemoteRoot = "/srv/interviewecho",
    [switch]$SkipFrontendBuild,
    [switch]$SkipBackendDeps,
    [switch]$ForceRagBuild,
    [switch]$DryRun,
    [switch]$KeepArchive
)

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Require-Command {
    param([string]$Name)
    if (-not (Get-Command $Name -ErrorAction SilentlyContinue)) {
        throw "Required command not found: $Name"
    }
}

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [string]$WorkingDirectory
    )

    $display = "$FilePath $($Arguments -join ' ')"
    if ($WorkingDirectory) {
        $display = "cd $WorkingDirectory; $display"
    }

    if ($DryRun) {
        Write-Host "[dry-run] $display"
        return
    }

    if ($WorkingDirectory) {
        Push-Location $WorkingDirectory
        try {
            & $FilePath @Arguments
        }
        finally {
            Pop-Location
        }
    }
    else {
        & $FilePath @Arguments
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $display"
    }
}

function Invoke-RemoteBash {
    param(
        [Parameter(Mandatory = $true)][string]$Target,
        [Parameter(Mandatory = $true)][string]$Script,
        [string[]]$RemoteArgs = @()
    )

    $normalizedScript = $Script -replace "`r`n", "`n"

    if ($DryRun) {
        Write-Host "[dry-run] scp <temporary bash script> ${Target}:/tmp/interviewecho-deploy.sh"
        Write-Host "[dry-run] ssh $Target /tmp/interviewecho-deploy.sh $($RemoteArgs -join ' ')"
        Write-Host $normalizedScript
        return
    }

    function Quote-BashArg {
        param([string]$Value)
        $escaped = $Value.Replace("'", "'\''")
        return "'" + $escaped + "'"
    }

    $localTemp = [System.IO.Path]::GetTempFileName()
    $remoteTemp = "/tmp/interviewecho-deploy-$PID-$([guid]::NewGuid().ToString('N')).sh"

    try {
        [System.IO.File]::WriteAllText(
            $localTemp,
            $normalizedScript,
            [System.Text.UTF8Encoding]::new($false)
        )

        & scp $localTemp "${Target}:$remoteTemp"
        if ($LASTEXITCODE -ne 0) {
            throw "Failed to upload temporary remote script"
        }

        $quotedRemoteTemp = Quote-BashArg $remoteTemp
        $quotedArgs = ($RemoteArgs | ForEach-Object { Quote-BashArg $_ }) -join " "
        $remoteCommand = "bash $quotedRemoteTemp $quotedArgs; status=`$?; rm -f $quotedRemoteTemp; exit `$status"

        & ssh $Target $remoteCommand
        if ($LASTEXITCODE -ne 0) {
            throw "Remote command failed with exit code $LASTEXITCODE"
        }
    }
    finally {
        Remove-Item -LiteralPath $localTemp -Force -ErrorAction SilentlyContinue
    }
}

$RepoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RepoName = Split-Path $RepoRoot -Leaf
$RepoParent = Split-Path $RepoRoot -Parent
$FrontendDir = Join-Path $RepoRoot "frontend"
$BackendDir = Join-Path $RepoRoot "backend"
$Target = "${ServerUser}@${ServerHost}"
$Stamp = Get-Date -Format "yyyyMMddHHmmss"
$ArchiveDir = Join-Path ([System.IO.Path]::GetTempPath()) "interviewecho-deploy"
$ArchivePath = Join-Path $ArchiveDir "interviewecho-$Stamp.tgz"
$RemoteArchive = "$RemoteRoot/uploads/interviewecho-$Stamp.tgz"

if (-not (Test-Path $FrontendDir)) {
    throw "frontend directory not found: $FrontendDir"
}
if (-not (Test-Path $BackendDir)) {
    throw "backend directory not found: $BackendDir"
}

Require-Command "ssh"
Require-Command "scp"
Require-Command "tar"
if (-not $SkipFrontendBuild) {
    Require-Command "npm"
}

New-Item -ItemType Directory -Force -Path $ArchiveDir | Out-Null

try {
    if (-not $SkipFrontendBuild) {
        Write-Step "Build frontend"
        $previousViteApiUrl = $env:VITE_API_URL
        $env:VITE_API_URL = "/api"
        try {
            if (-not (Test-Path (Join-Path $FrontendDir "node_modules"))) {
                Invoke-Checked -FilePath "npm" -Arguments @("ci") -WorkingDirectory $FrontendDir
            }
            Invoke-Checked -FilePath "npm" -Arguments @("run", "build") -WorkingDirectory $FrontendDir
        }
        finally {
            if ($null -eq $previousViteApiUrl) {
                Remove-Item Env:\VITE_API_URL -ErrorAction SilentlyContinue
            }
            else {
                $env:VITE_API_URL = $previousViteApiUrl
            }
        }
    }
    else {
        Write-Step "Skip frontend build"
    }

    Write-Step "Create release archive"
    if (Test-Path $ArchivePath) {
        Remove-Item $ArchivePath -Force
    }
    Invoke-Checked -FilePath "tar" -Arguments @(
        "--exclude=.git",
        "--exclude=frontend/node_modules",
        "--exclude=frontend/.env",
        "--exclude=backend/.env",
        "--exclude=backend/rag/chroma_db",
        "--exclude=backend/rag/vector_index.json",
        "--exclude=backend/rag/.source_hash",
        "--exclude=__pycache__",
        "--exclude=*.pyc",
        "-czf",
        $ArchivePath,
        "-C",
        $RepoParent,
        $RepoName
    )

    Write-Step "Prepare remote upload directory"
    $prepareRemote = @'
set -euo pipefail
remote_root="$1"
mkdir -p "$remote_root/uploads" "$remote_root/releases" "$remote_root/shared"
'@
    Invoke-RemoteBash -Target $Target -Script $prepareRemote -RemoteArgs @($RemoteRoot)

    Write-Step "Upload archive"
    Invoke-Checked -FilePath "scp" -Arguments @($ArchivePath, "${Target}:$RemoteArchive")

    Write-Step "Deploy on server"
    $skipDepsFlag = if ($SkipBackendDeps) { "1" } else { "0" }
    $forceRagFlag = if ($ForceRagBuild) { "1" } else { "0" }
    $deployRemote = @'
set -euo pipefail

remote_root="$1"
stamp="$2"
archive="$3"
skip_deps="$4"
force_rag="$5"

release_dir="$remote_root/releases/$stamp"
previous_current=""
if [ -e "$remote_root/current" ]; then
  previous_current="$(readlink -f "$remote_root/current" || true)"
fi

mkdir -p "$release_dir"
tar -xzf "$archive" -C "$release_dir" --strip-components=1

if [ ! -f "$release_dir/frontend/dist/index.html" ]; then
  echo "frontend/dist/index.html is missing. Run the frontend build before deploying." >&2
  exit 1
fi
if [ ! -f "$release_dir/backend/main.py" ]; then
  echo "backend/main.py is missing. Archive layout looks wrong." >&2
  exit 1
fi

if [ "$skip_deps" != "1" ]; then
  echo "Installing backend dependencies..."
  sed 's/^numpy==2\.4\.3$/numpy==2.2.6/' "$release_dir/backend/requirements.txt" > "$remote_root/shared/requirements.deploy.txt"
  "$remote_root/shared/venv/bin/pip" install -r "$remote_root/shared/requirements.deploy.txt"
else
  echo "Skipping backend dependency install."
fi

hash_source() {
  local source_dir="$1"
  (
    cd "$source_dir"
    {
      if [ -d knowledge-base ]; then
        find knowledge-base -type f
      fi
      if [ -d backend/rag ]; then
        find backend/rag -type f \
          ! -name 'vector_index.json' \
          ! -name '.source_hash' \
          ! -name '*.pyc' \
          ! -path '*/__pycache__/*' \
          ! -path '*/chroma_db/*'
      fi
    } | sort | while IFS= read -r source_file; do
      sha256sum "$source_file"
    done
    if [ -f "$remote_root/shared/backend.env" ]; then
      grep -E '^(EMBEDDING_MODEL|LLM_BASE_URL)=' "$remote_root/shared/backend.env" || true
    fi
  ) | sha256sum | awk '{print $1}'
}

new_hash="$(hash_source "$release_dir")"
old_hash=""
old_index=""
if [ -n "$previous_current" ] && [ -f "$previous_current/backend/rag/vector_index.json" ]; then
  old_index="$previous_current/backend/rag/vector_index.json"
elif [ -d "$remote_root/releases" ]; then
  old_index="$(
    find "$remote_root/releases" -path '*/backend/rag/vector_index.json' -type f -printf '%T@ %p\n' 2>/dev/null \
      | sort -nr \
      | head -n 1 \
      | cut -d' ' -f2-
  )"
fi

if [ -n "$old_index" ]; then
  old_release="${old_index%/backend/rag/vector_index.json}"
  if [ -f "$old_release/backend/rag/.source_hash" ]; then
    old_hash="$(cat "$old_release/backend/rag/.source_hash" || true)"
  fi
fi

need_rag="0"
if [ "$force_rag" = "1" ]; then
  need_rag="1"
elif [ -z "$old_index" ] || [ ! -f "$old_index" ]; then
  need_rag="1"
elif [ -n "$old_hash" ] && [ "$old_hash" != "$new_hash" ]; then
  echo "RAG source changed; reusing the existing index for this deploy. Run with -ForceRagBuild to rebuild embeddings."
fi

if [ "$need_rag" = "1" ]; then
  echo "Building RAG index..."
  cd "$release_dir/backend"
  if [ -f "$remote_root/shared/backend.env" ]; then
    set -a
    # shellcheck disable=SC1091
    . "$remote_root/shared/backend.env"
    set +a
  fi
  "$remote_root/shared/venv/bin/python" -m rag.build_index
  if [ ! -f "$release_dir/backend/rag/vector_index.json" ]; then
    echo "RAG index build did not produce backend/rag/vector_index.json" >&2
    exit 1
  fi
  echo "$new_hash" > "$release_dir/backend/rag/.source_hash"
else
  echo "Reusing existing RAG index."
  mkdir -p "$release_dir/backend/rag"
  cp "$old_index" "$release_dir/backend/rag/vector_index.json"
  echo "$new_hash" > "$release_dir/backend/rag/.source_hash"
fi

ln -sfn "$release_dir" "$remote_root/current"

systemctl restart interviewecho-backend

if docker ps -a --format '{{.Names}}' | grep -qx 'interviewecho-web'; then
  docker rm -f interviewecho-web >/dev/null
fi

docker run -d \
  --name interviewecho-web \
  --restart unless-stopped \
  --network host \
  -v "$remote_root/current/frontend/dist:/usr/share/nginx/html:ro" \
  -v "$remote_root/nginx/default.conf:/etc/nginx/conf.d/default.conf:ro" \
  nginx:1.27-alpine >/dev/null

healthy="0"
for _ in $(seq 1 30); do
  if curl -fsS -I http://127.0.0.1:18080/ >/dev/null 2>&1 \
    && curl -fsS http://127.0.0.1:18080/api/interview/roles >/dev/null 2>&1; then
    healthy="1"
    break
  fi
  sleep 2
done

if [ "$healthy" != "1" ]; then
  echo "Health check failed after waiting for frontend/backend startup." >&2
  exit 1
fi

rm -f "$archive"
echo "Deployment complete: $release_dir"
'@
    Invoke-RemoteBash -Target $Target -Script $deployRemote -RemoteArgs @(
        $RemoteRoot,
        $Stamp,
        $RemoteArchive,
        $skipDepsFlag,
        $forceRagFlag
    )

    Write-Step "Done"
    Write-Host "Visit: http://$ServerHost`:18080/"
}
finally {
    if ((-not $KeepArchive) -and (Test-Path $ArchivePath) -and (-not $DryRun)) {
        Remove-Item $ArchivePath -Force
    }
}

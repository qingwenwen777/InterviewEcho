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

compose() {
  if docker compose version >/dev/null 2>&1; then
    docker compose "$@"
  else
    docker-compose "$@"
  fi
}

ensure_backend_env_judge0() {
  local env_file="$remote_root/shared/backend.env"
  touch "$env_file"
  set_backend_env() {
    local key="$1"
    local value="$2"
    if grep -q "^${key}=" "$env_file"; then
      sed -i "s|^${key}=.*|${key}=${value}|" "$env_file"
    else
      echo "${key}=${value}" >> "$env_file"
    fi
  }
  set_backend_env JUDGE0_BASE_URL "http://127.0.0.1:2358"
  set_backend_env JUDGE0_TIMEOUT_SECONDS "12"
  set_backend_env JUDGE0_POLL_INTERVAL_SECONDS "0.6"
  set_backend_env JUDGE0_MAX_POLL_ATTEMPTS "90"
  set_backend_env CODE_MAX_SOURCE_LENGTH "20000"
  set_backend_env CODE_MAX_TEST_CASES "30"
  set_backend_env CODE_MAX_CONCURRENT_JUDGE_CASES "8"
  set_backend_env CODE_OUTPUT_LIMIT "4000"
  set_backend_env ASR_PROVIDER "dashscope"
  set_backend_env ASR_BASE_URL "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
  set_backend_env ASR_MODEL "qwen3-asr-flash"
  set_backend_env ASR_LANGUAGE "zh"
  set_backend_env ASR_TIMEOUT_SECONDS "35"
  set_backend_env ASR_ENABLE_ITN "true"
  set_backend_env ASR_TRANSCODE_AUDIO "true"
  set_backend_env ASR_MAX_AUDIO_BYTES "10485760"
  set_backend_env VOICE_UPLOAD_DIR "$remote_root/shared/voice"
  set_backend_env MIMO_BASE_URL "https://token-plan-sgp.xiaomimimo.com/v1"
  set_backend_env MIMO_TTS_MODEL "mimo-v2.5-tts"
  set_backend_env MIMO_TTS_AUDIO_FORMAT "wav"
  set_backend_env MIMO_TTS_TIMEOUT_SECONDS "60"
  set_backend_env INTERVIEW_MAX_FOLLOW_UPS_PER_QUESTION "1"
  set_backend_env INTERVIEW_SHORT_ROUNDS_MAX_FOLLOW_UPS "0"
}

ensure_judge0() {
  local judge_root="$remote_root/shared/judge0"
  local project_name="interviewecho-judge0"
  local release_dir_name="judge0-v1.13.1"
  local release_url="https://github.com/judge0/judge0/releases/download/v1.13.1/judge0-v1.13.1.zip"

  apply_judge0_limits() {
    update_container_limit() {
      local service="$1"
      local cpus="$2"
      local memory="$3"
      local swap="$4"
      container_id="$(cd "$judge_root" && compose -p "$project_name" ps -q "$service" 2>/dev/null || true)"
      if [ -n "$container_id" ]; then
        docker update --cpus "$cpus" --memory "$memory" --memory-swap "$swap" "$container_id" >/dev/null 2>&1 || true
      fi
    }

    update_container_limit server 1.5 768m 1024m
    update_container_limit worker 8.0 6144m 7168m
    update_container_limit workers 8.0 6144m 7168m
    update_container_limit db 1.5 1536m 2048m
    update_container_limit redis 0.5 256m 384m
  }

  if curl -fsS http://127.0.0.1:2358/system_info >/dev/null 2>&1; then
    local judge_conf_changed="0"
    ensure_conf_value() {
      local key="$1"
      local value="$2"
      local current=""
      if [ -f "$judge_root/judge0.conf" ]; then
        current="$(grep "^${key}=" "$judge_root/judge0.conf" | tail -n 1 | cut -d= -f2- || true)"
      fi
      if [ "$current" != "$value" ]; then
        if grep -q "^${key}=" "$judge_root/judge0.conf"; then
          sed -i "s|^${key}=.*|${key}=${value}|" "$judge_root/judge0.conf"
        else
          echo "${key}=${value}" >> "$judge_root/judge0.conf"
        fi
        judge_conf_changed="1"
      fi
    }
    if [ -f "$judge_root/judge0.conf" ]; then
      ensure_conf_value COUNT "8"
      ensure_conf_value MAX_QUEUE_SIZE "128"
      ensure_conf_value MAX_CPU_TIME_LIMIT "64"
      ensure_conf_value MAX_WALL_TIME_LIMIT "160"
      ensure_conf_value MAX_MEMORY_LIMIT "1024000"
    fi
    if [ "$judge_conf_changed" = "1" ]; then
      echo "Judge0 config changed; restarting Judge0 server and workers..."
      for service in server worker workers; do
        if [ -n "$(cd "$judge_root" && compose -p "$project_name" ps -q "$service" 2>/dev/null || true)" ]; then
          (cd "$judge_root" && compose -p "$project_name" restart "$service")
        fi
      done
      judge_healthy="0"
      for _ in $(seq 1 45); do
        if curl -fsS http://127.0.0.1:2358/system_info >/dev/null 2>&1; then
          judge_healthy="1"
          break
        fi
        sleep 2
      done
      if [ "$judge_healthy" != "1" ]; then
        echo "Judge0 health check failed after config restart." >&2
        exit 1
      fi
    fi
    echo "Judge0 is already healthy on 127.0.0.1:2358."
    apply_judge0_limits
    return
  fi

  if [ "$(stat -fc %T /sys/fs/cgroup 2>/dev/null || true)" = "cgroup2fs" ]; then
    echo "Judge0 CE v1.13.1 requires the host to boot with cgroup v1/hybrid mode." >&2
    echo "Add systemd.unified_cgroup_hierarchy=0 cgroup_enable=memory swapaccount=1 to GRUB, run update-grub, then reboot." >&2
    exit 1
  fi

  if ss -ltn | awk '{print $4}' | grep -E '(^|:)2358$' >/dev/null 2>&1; then
    echo "Port 2358 is already in use but Judge0 health check failed. Refusing to continue." >&2
    exit 1
  fi

  mkdir -p "$judge_root"
  local needs_download="0"
  if [ ! -f "$judge_root/docker-compose.yml" ] || [ ! -f "$judge_root/judge0.conf" ]; then
    needs_download="1"
  elif ! grep -q 'judge0/judge0:1\.13\.1' "$judge_root/docker-compose.yml"; then
    echo "Existing Judge0 files are not v1.13.1; refreshing Judge0 CE bundle..."
    needs_download="1"
  fi

  if [ "$needs_download" = "1" ]; then
    echo "Downloading Judge0 CE v1.13.1..."
    local tmp_dir
    tmp_dir="$(mktemp -d)"
    curl -fsSL "$release_url" -o "$tmp_dir/judge0.zip"
    python3 - "$tmp_dir/judge0.zip" "$tmp_dir" <<'PY'
import sys
import zipfile

zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])
PY
    cp -a "$tmp_dir"/"$release_dir_name"/. "$judge_root/"
    rm -rf "$tmp_dir"
  fi

  sed -i -E "s/\"2358:2358\"/\"127.0.0.1:2358:2358\"/g" "$judge_root/docker-compose.yml"
  sed -i -E "s/'2358:2358'/'127.0.0.1:2358:2358'/g" "$judge_root/docker-compose.yml"

  set_conf() {
    local key="$1"
    local value="$2"
    if grep -q "^${key}=" "$judge_root/judge0.conf"; then
      sed -i "s|^${key}=.*|${key}=${value}|" "$judge_root/judge0.conf"
    else
      echo "${key}=${value}" >> "$judge_root/judge0.conf"
    fi
  }

  make_secret() {
    if command -v openssl >/dev/null 2>&1; then
      openssl rand -hex 24
    else
      date +%s%N | sha256sum | awk '{print $1}'
    fi
  }

  if ! grep -q '^REDIS_PASSWORD=.\+' "$judge_root/judge0.conf"; then
    set_conf REDIS_PASSWORD "$(make_secret)"
  fi
  if ! grep -q '^POSTGRES_PASSWORD=.\+' "$judge_root/judge0.conf"; then
    set_conf POSTGRES_PASSWORD "$(make_secret)"
  fi
  set_conf ALLOW_IP ""
  set_conf COUNT "8"
  set_conf MAX_QUEUE_SIZE "128"
  set_conf CPU_TIME_LIMIT "2"
  set_conf MAX_CPU_TIME_LIMIT "64"
  set_conf WALL_TIME_LIMIT "6"
  set_conf MAX_WALL_TIME_LIMIT "160"
  set_conf MEMORY_LIMIT "128000"
  set_conf MAX_MEMORY_LIMIT "1024000"
  set_conf MAX_PROCESSES_AND_OR_THREADS "64"
  set_conf MAX_MAX_PROCESSES_AND_OR_THREADS "96"
  set_conf ENABLE_NETWORK "false"
  set_conf ALLOW_ENABLE_NETWORK "false"
  set_conf USE_DOCS_AS_HOMEPAGE "false"

  echo "Starting Judge0 Docker Compose..."
  (cd "$judge_root" && compose -p "$project_name" up -d db redis)
  sleep 10
  (cd "$judge_root" && compose -p "$project_name" up -d)

  apply_judge0_limits

  if ss -ltn | awk '{print $4}' | grep -E '(^0\.0\.0\.0:2358$|^\[::\]:2358$)' >/dev/null 2>&1; then
    echo "Judge0 is listening publicly on 2358; expected localhost-only binding." >&2
    exit 1
  fi

  judge_healthy="0"
  for _ in $(seq 1 45); do
    if curl -fsS http://127.0.0.1:2358/system_info >/dev/null 2>&1; then
      judge_healthy="1"
      break
    fi
    sleep 2
  done
  if [ "$judge_healthy" != "1" ]; then
    echo "Judge0 health check failed after startup." >&2
    (cd "$judge_root" && compose -p "$project_name" ps || true)
    exit 1
  fi
}

if [ "$skip_deps" != "1" ]; then
  echo "Installing backend dependencies..."
  tr -d '\r' < "$release_dir/backend/requirements.txt" | sed 's/^numpy==2\.4\.3$/numpy==2.2.6/' > "$remote_root/shared/requirements.deploy.txt"
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

ensure_backend_env_judge0
ensure_judge0

echo "Refreshing database schema and Hot100 seed data..."
cd "$release_dir/backend"
if [ -f "$remote_root/shared/backend.env" ]; then
  set -a
  # shellcheck disable=SC1091
  . "$remote_root/shared/backend.env"
  set +a
fi
"$remote_root/shared/venv/bin/python" - <<'PY'
from db import models
from db.database import SessionLocal, engine
from db.seed_code_problems import seed_code_problems

models.Base.metadata.create_all(bind=engine)
db = SessionLocal()
try:
    seed_code_problems(db)
finally:
    db.close()
PY

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
    && curl -fsS http://127.0.0.1:18080/api/interview/roles >/dev/null 2>&1 \
    && curl -fsS http://127.0.0.1:2358/system_info >/dev/null 2>&1; then
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

#!/usr/bin/env bash
# ============================================================
# AI-Me 云服务器一键部署脚本（Ubuntu 22.04 / Debian 11+）
# 适用：阿里云 ECS / 腾讯云 CVM / AWS Lightsail 等
#
# 安全设计：
#   - 代码从 GitHub 公开仓库拉取（不含敏感数据）
#   - 服务器上独立维护真实 .env / profile.yaml / resume.md
#   - 修改资料：本地改 → 手动上传到服务器（不进 git）
# ============================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# 0. 检查 root
[[ $EUID -ne 0 ]] && fail "请用 root 运行：sudo bash deploy.sh"

# 1. 安装 Docker（优先从 apt/docker.io 走，避开 get.docker.com 443 阻断）
if ! command -v docker &>/dev/null; then
  log "安装 Docker..."
  # 1.1 优先尝试阿里云 apt 镜像（国内 ECS 最快）
  if grep -q "mirrors.aliyun.com" /etc/apt/sources.list 2>/dev/null \
     || [ -d /etc/apt/sources.list.d ] && grep -rq "mirrors.aliyun.com" /etc/apt/sources.list.d/ 2>/dev/null; then
    log "  - 检测到阿里云 apt 镜像，跳过 sources.list 替换"
  else
    log "  - 把 apt 源切到阿里云镜像"
    cp /etc/apt/sources.list /etc/apt/sources.list.bak 2>/dev/null || true
    sed -i 's|http://archive.ubuntu.com|https://mirrors.aliyun.com|g' /etc/apt/sources.list
    sed -i 's|http://security.ubuntu.com|https://mirrors.aliyun.com|g' /etc/apt/sources.list
  fi

  apt-get update -o Acquire::Retries=2
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
      ca-certificates curl gnupg docker.io docker-compose-plugin

  systemctl enable docker
  systemctl start docker || true
fi

# 1.bis 补一次验证（apt 装的 "docker.io" 提供 docker，但 "docker compose" 子命令可能还没生效）
if ! docker compose version &>/dev/null; then
  log "  - 补装 docker-compose"
  apt-get install -y --no-install-recommends docker-compose-plugin || true
fi

# 2. 克隆/更新代码（公开仓库）
REPO_URL="${REPO_URL:-https://github.com/TXC05-25/ai-me.git}"
APP_DIR="/opt/ai-me"

if [[ ! -d $APP_DIR ]]; then
  log "克隆项目到 $APP_DIR..."
  git clone "$REPO_URL" "$APP_DIR"
else
  log "更新已有代码..."
  cd "$APP_DIR" && git pull
fi

cd "$APP_DIR"

# 3. 检查 .env（真实 API Key）
if [[ ! -f .env ]]; then
  warn "=========================================================="
  warn "首次部署：需要配置 .env"
  warn "=========================================================="
  cp .env.example .env
  chmod 600 .env
  warn "已从 .env.example 复制生成 .env，请用 nano 编辑填入真实 Key："
  warn "  nano .env"
  fail "填好 Key 后重新运行本脚本：bash deploy.sh"
fi

# 4. 检查个人资料文件（从 .sample 复制）
declare -A DATA_FILES=(
  ["backend/data/profile.yaml"]="backend/data/profile.yaml.sample"
  ["backend/data/resume.md"]="backend/data/resume.md.sample"
  ["backend/data/qa_pairs.jsonl"]="backend/data/qa_pairs.jsonl.sample"
)
for target in "${!DATA_FILES[@]}"; do
  sample="${DATA_FILES[$target]}"
  if [[ ! -f "$target" && -f "$sample" ]]; then
    warn "$target 缺失，正在从 $sample 复制..."
    cp "$sample" "$target"
    warn "请编辑 $target 填入真实信息后重新运行本脚本"
    fail "初始化数据文件后重新运行：bash deploy.sh"
  fi
done

# 5. 检查项目资料（每个 *.md.sample 对应一个 *.md）
for sample in backend/data/projects/*.md.sample; do
  [[ ! -f "$sample" ]] && continue
  target="${sample%.sample}"
  if [[ ! -f "$target" ]]; then
    warn "$target 缺失，正在从 $sample 复制..."
    cp "$sample" "$target"
    warn "请编辑 $target 填入真实项目内容"
  fi
done

# 6. 开放防火墙
if command -v ufw &>/dev/null && ufw status 2>/dev/null | grep -q "active"; then
  log "配置 ufw 开放 80/443..."
  ufw allow 80/tcp
  ufw allow 443/tcp
fi

# 7. 启动服务
log "构建并启动 Docker 服务..."
docker compose down || true
docker compose up -d --build

# 8. 等待启动
log "等待后端启动（首次启动会重建向量库，可能需要 1-3 分钟）..."
for i in {1..60}; do
  if curl -sf http://localhost:8000/health &>/dev/null; then
    log "后端已就绪"
    break
  fi
  sleep 3
  [[ $i -eq 60 ]] && warn "后端未在 3 分钟内就绪，请查看 docker compose logs"
done

# 9. 显示状态
docker compose ps

PUBLIC_IP=$(curl -sf http://ipv4.icanhazip.com 2>/dev/null || echo "<你的服务器公网IP>")
log "============================================================"
log " 部署完成！"
log " - 🌐 主访问入口（推荐给面试官的链接）：  http://$PUBLIC_IP:5500"
log " - 📖 后端 API 文档（Swagger）：          http://$PUBLIC_IP:8000/docs"
log ""
log " 💡 推荐做法：只把 5500 端口给别人用，8000 端口可以收紧到只允许你自己的 IP 访问"
log " 💡 如果希望直接 80 端口：进阿里云安全组把 5500 替换成 80，并把前端 compose 端口改成 80:80 重启"
log "============================================================"
log ""
log "📌 后续修改代码：本地改完 git push，服务器跑：bash deploy.sh"
log "📌 修改个人资料：直接编辑 /opt/ai-me/backend/data/*.yaml/md 后"
log "   docker compose restart backend"
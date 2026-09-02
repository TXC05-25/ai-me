#!/usr/bin/env bash
# ============================================================
# AI-Me 云服务器一键部署脚本（Ubuntu 22.04 / Debian 11+）
# 适用：阿里云 ECS / 腾讯云 CVM / AWS Lightsail 等
# ============================================================
set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log()   { echo -e "${GREEN}[$(date +%H:%M:%S)]${NC} $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()  { echo -e "${RED}[FAIL]${NC} $*"; exit 1; }

# 1. 检查 root
[[ $EUID -ne 0 ]] && fail "请用 root 运行：sudo bash deploy.sh"

# 2. 安装 Docker
if ! command -v docker &>/dev/null; then
  log "安装 Docker..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  systemctl enable docker
  rm get-docker.sh
fi

if ! command -v docker compose &>/dev/null && ! docker compose version &>/dev/null; then
  log "安装 docker-compose plugin..."
  apt-get install -y docker-compose-plugin || pip install docker-compose
fi

# 3. 配置 git（用你自己的仓库）
REPO_URL="${REPO_URL:-git@github.com:TanXiuCheng/ai-me.git}"
APP_DIR="/opt/ai-me"

if [[ ! -d $APP_DIR ]]; then
  log "克隆项目到 $APP_DIR..."
  git clone "$REPO_URL" "$APP_DIR"
else
  log "更新已有代码..."
  cd "$APP_DIR" && git pull
fi

cd "$APP_DIR"

# 4. 检查 .env
if [[ ! -f .env ]]; then
  warn ".env 不存在，从 .env.example 复制，请编辑后再运行本脚本"
  cp .env.example .env
  fail "请先 vim .env 填入真实 API Key，然后重新运行 bash deploy.sh"
fi

# 5. 开放防火墙（ufw / iptables 简化）
if command -v ufw &>/dev/null && ufw status | grep -q "active"; then
  log "配置 ufw 开放 80/443..."
  ufw allow 80/tcp
  ufw allow 443/tcp
fi

# 6. 启动服务
log "构建并启动 Docker 服务..."
docker compose down || true
docker compose up -d --build

# 7. 等待启动
log "等待后端启动（首次启动会重建向量库，可能需要 1-3 分钟）..."
for i in {1..60}; do
  if curl -sf http://localhost:8000/health &>/dev/null; then
    log "后端已就绪"
    break
  fi
  sleep 3
  [[ $i -eq 60 ]] && warn "后端未在 3 分钟内就绪，请查看 docker compose logs"
done

# 8. 显示状态
docker compose ps

PUBLIC_IP=$(curl -sf http://ipv4.icanhazip.com 2>/dev/null || echo "<你的服务器公网IP>")
log "============================================================"
log " 部署完成！"
log "  - 前端访问：  http://$PUBLIC_IP"
log "  - 后端 API：  http://$PUBLIC_IP:8000/docs"
log "  - 如需 HTTPS，请运行：bash deploy-https.sh your-domain.com"
log "============================================================"
#!/usr/bin/env bash
# ============================================================
# AI-Me 一键配置 HTTPS（使用 Let's Encrypt 免费证书）
# 用法：sudo bash deploy-https.sh your-domain.com your@email.com
# ============================================================
set -e

DOMAIN="${1:?用法: sudo bash deploy-https.sh your-domain.com your@email.com}"
EMAIL="${2:-admin@$DOMAIN}"

[[ $EUID -ne 0 ]] && { echo "请用 root 运行"; exit 1; }

cd /opt/ai-me

# 1. 安装 certbot
if ! command -v certbot &>/dev/null; then
  apt-get update
  apt-get install -y certbot python3-certbot-nginx
fi

# 2. 临时关闭 80 端口的 docker nginx（certbot 需要独立占用）
# 改为用 certbot 的 standalone 模式申请证书
docker compose stop frontend

# 3. 申请证书
certbot certonly --standalone \
  --preferred-challenges http \
  --email "$EMAIL" \
  --agree-tos --no-eff-email \
  -d "$DOMAIN"

# 4. 生成新版 nginx 配置（HTTPS）
mkdir -p /opt/ai-me/frontend
cat > /opt/ai-me/frontend/nginx-ssl.conf <<EOF
server {
    listen 80;
    server_name $DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl http2;
    server_name $DOMAIN;

    ssl_certificate /etc/letsencrypt/live/$DOMAIN/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/$DOMAIN/privkey.pem;

    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /chat/ {
        proxy_pass http://backend:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 300s;
    }

    location ~ ^/(profile|projects|recommend|export|reset|health|metrics) {
        proxy_pass http://backend:8000;
    }

    location ~* \.(js|css|png|jpg|svg|ico)$ {
        expires 7d;
        add_header Cache-Control "public, max-age=604800, immutable";
    }

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml;
}
EOF

# 5. 更新 docker-compose 挂载新配置
sed -i 's|./frontend/nginx.conf:/etc/nginx/conf.d/default.conf:ro|./frontend/nginx-ssl.conf:/etc/nginx/conf.d/default.conf:ro\n      - /etc/letsencrypt:/etc/letsencrypt:ro|' docker-compose.yml

# 6. 重新构建并启动
docker compose up -d --build

# 7. 配置证书自动续期
(crontab -l 2>/dev/null; echo "0 3 * * * certbot renew --quiet && docker compose -f /opt/ai-me/docker-compose.yml restart frontend") | crontab -

echo "============================================================"
echo " HTTPS 配置完成！"
echo " 访问：https://$DOMAIN"
echo " 证书自动续期已配置（每天 3 点检查）"
echo "============================================================"
#!/usr/bin/env bash
# 把 sshd_config 改成只监听 Port 2222，移除 Port 22
set -e

cp /etc/ssh/sshd_config /etc/ssh/sshd_config.bak.with-both

# 删 Port 22 行，保留 Port 2222
grep -v "^Port 22$" /etc/ssh/sshd_config > /tmp/sshd_config.new
echo "Port 2222" >> /tmp/sshd_config.new
mv /tmp/sshd_config.new /etc/ssh/sshd_config

systemctl restart sshd
sleep 2

echo "=== 当前 SSH 监听端口 ==="
ss -tln | grep -E ":(22|2222)" || echo "(无匹配)"

echo ""
echo "=== sshd_config 中的 Port 行 ==="
grep -n "^Port " /etc/ssh/sshd_config

echo ""
echo "=== 验证 22 端口已关闭 ==="
if timeout 3 bash -c "echo > /dev/tcp/127.0.0.1/22" 2>/dev/null; then
    echo "❌ 22 还在监听"
else
    echo "✅ 22 已不监听（SSH 只剩 2222）"
fi

#!/usr/bin/env bash
# 救援脚本：让 sshd 同时听 22 + 2222，并把指定 IP 加入 fail2ban 白名单
# 这样 Workbench 也能通过 22 进，PC 通过 2222 也能进，且不会被 ban

set -e

# 1. 把 sshd_config 改成同时听 22 + 2222
#    先删掉可能重复的 Port 行，写入干净的版本
grep -v "^Port " /etc/ssh/sshd_config > /tmp/sshd_new
echo "Port 22" >> /tmp/sshd_new
echo "Port 2222" >> /tmp/sshd_new
echo "UseDNS no" >> /tmp/sshd_new
cp /tmp/sshd_new /etc/ssh/sshd_config

# 2. 重启 sshd
systemctl restart sshd
sleep 2

# 3. 加 fail2ban 白名单
WHITELIST="127.0.0.1/8 220.184.37.252"
mkdir -p /etc/fail2ban
cat > /etc/fail2ban/jail.local <<EOF
[DEFAULT]
ignoreip = $WHITELIST

[sshd]
enabled  = true
port     = ssh
filter   = sshd
logpath  = /var/log/auth.log
maxretry = 5
findtime = 600
bantime  = 3600
EOF

systemctl restart fail2ban
sleep 2

# 4. 报告
echo "============================="
echo "sshd 监听情况："
ss -tln | grep -E ":(22|2222)\b" || echo "(无 SSH 监听)"
echo ""
echo "fail2ban 白名单："
fail2ban-client get sshd ignoreip 2>/dev/null || cat /etc/fail2ban/jail.local | grep -i ignore
echo ""
echo "已 unban 所有 IP："
fail2ban-client unban --all 2>&1 | head -3
echo ""
echo "DONE"

# 🚀 AI-Me · 云服务器部署完全指南（阿里云 / 腾讯云）

> 把 AI-Me 部署到阿里云 ECS / 腾讯云 CVM，让面试官通过公网 IP 或域名直接访问。
> 整套方案：Docker Compose 一键起，Nginx 反向代理，可选 Let's Encrypt 免费 HTTPS。

---

## 📐 架构

```
访问者浏览器
   │  https://your-domain.com
   ↓
┌──────────────────────────────┐
│  云服务器（Ubuntu 22.04）      │
│                              │
│  Docker Compose              │
│   ├─ frontend (nginx:80/443) │  ← 反代 + 静态页
│   └─ backend  (FastAPI:8000) │  ← AI 推理服务
│         ├─ Milvus Lite       │  ← 嵌入式向量库
│         ├─ ChromaDB 备份      │
│         └─ 调用 MiniMax / SiliconFlow API │
└──────────────────────────────┘
```

---

## 🛒 Step 1：购买云服务器

### 推荐配置（学生机 / 校招 demo 够用）

| 项 | 配置 |
| --- | --- |
| 厂商 | **阿里云**（[ecs.aliyuncs.com](https://ecs.aliyuncs.com)） 或 **腾讯云**（[cloud.tencent.com](https://cloud.tencent.com)） |
| 规格 | 2 vCPU / 4 GB 内存 / 5 Mbps 带宽（最低）<br>推荐 **2 vCPU / 4 GB / 5 Mbps** |
| 镜像 | **Ubuntu Server 22.04 LTS 64位** |
| 系统盘 | 40 GB 高效云盘（够用） |
| 带宽 | **按使用流量**（5 Mbps 峰值），校招 demo 一个月几十块 |
| 时长 | 1 个月起，建议先买 1 个月测试，稳定后改 **包年**（便宜一半以上） |
| 地域 | 选择最近的：**华南/华东/华北** 看你客户端在哪 |

### 阿里云学生优惠
- 「云翼计划」：24 岁以下免认证可领一个月 ECS（2C2G 免费）
- 「高校计划」：学生 9.5 元/月 1C2G

### 腾讯云学生优惠
- 「云+校园」：25 岁以下 1 元/月 1C2G
- 「学生认证套餐」：10 元/月 2C4G

---

## 🔐 Step 2：配置安全组（关键！）

买完 ECS 后，**最重要**的一步是开放端口：

### 阿里云
1. 进入 ECS 控制台 → 实例 → **安全组** → 配置规则
2. 入方向添加：
   - `80/80` → `0.0.0.0/0`（HTTP，网页必须）
   - `443/443` → `0.0.0.0/0`（HTTPS，可选）
   - `22/22` → `你的办公IP/32`（SSH，**不要对全网开放**）
   - `8000/8000` → `127.0.0.1/32`（后端 API，仅本地调试用，不对公网开放）

### 腾讯云
1. CVM 控制台 → 实例 → **安全组** → 入站规则
2. 同样添加 `80/443/22`，22 限制 IP

> ⚠️ **8000 端口不要对公网开放**，只走 nginx 反代。否则别人能直接绕过前端调你的 API 浪费 Key。

---

## 🔑 Step 3：登录服务器并初始化

### 3.1 SSH 登录（Windows PowerShell / Mac Terminal）

```bash
ssh root@你的公网IP
# 首次登录输入 yes，再粘贴密码
```

### 3.2 创建普通用户（生产环境不要直接用 root）

```bash
adduser aiadmin
usermod -aG sudo aiadmin
# 后续用 aiadmin 登录，sudo 提权
```

### 3.3 系统基础配置

```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y git curl ufw

# 开启防火墙
sudo ufw allow OpenSSH
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

---

## 📥 Step 4：上传代码（两种方式任选）

### 方式 A：Git 拉取（推荐）

```bash
sudo -iu aiadmin
cd /opt
sudo git clone https://github.com/TanXiuCheng/ai-me.git
sudo chown -R aiadmin:aiadmin ai-me
cd ai-me
```

### 方式 B：本地 scp 上传（没推到 GitHub 时用）

在**你本地 Windows PowerShell**：

```powershell
scp -r C:\Users\谭修诚\Desktop\ai-me aiadmin@你的公网IP:/home/aiadmin/
# 然后在服务器上：
ssh aiadmin@你的公网IP
sudo mv /home/aiadmin/ai-me /opt/
sudo chown -R aiadmin:aiadmin /opt/ai-me
cd /opt/ai-me
```

---

## 🔧 Step 5：配置环境变量

```bash
cd /opt/ai-me
cp .env.example .env
nano .env  # 或 vim .env
```

填写你的 API Key（你已经有 MiniMax / SiliconFlow Key）：

```env
LLM_API_KEY=sk-cp-你的真实Key
EMBEDDING_API_KEY=sk-cp-你的真实Key（同上）
RERANK_API_KEY=sk-你的SiliconFlowKey
LANGCHAIN_API_KEY=lsv2_pt_xxx   # 可选，不填就关掉
```

**保存**：`Ctrl+O` → 回车 → `Ctrl+X` 退出 nano。

---

## 🚀 Step 6：一键部署

```bash
# 给脚本可执行权限
chmod +x deploy.sh

# 跑部署脚本（需要 sudo，因为要装 Docker）
sudo bash deploy.sh
```

脚本会自动：

1. 装 Docker + Docker Compose
2. 拉取/更新代码
3. 配置防火墙
4. `docker compose up -d --build` 启动两个容器
5. 等待 `/health` 通，**首次启动会重建向量库约 1-3 分钟**

### 查看进度

```bash
cd /opt/ai-me
sudo docker compose ps           # 看容器状态
sudo docker compose logs -f backend  # 看后端日志（Ctrl+C 退出）
```

### 验证部署

```bash
# 后端健康检查
curl http://localhost:8000/health
# 期望：{"status":"ok",...}

# 前端首页
curl -I http://localhost/
# 期望：HTTP/1.1 200 OK
```

---

## 🌐 Step 7：访问与调试

### 通过公网 IP 访问

打开浏览器，访问：

```
http://你的公网IP
```

### 遇到问题的排查清单

| 现象 | 排查 |
| --- | --- |
| 打不开网页 | 安全组 80 端口没开；ufw 没 allow 80；docker compose ps 看 frontend 是否 running |
| 页面打开了但聊天没反应 | 看后端 logs：`docker compose logs backend`；检查 .env 的 API Key |
| AI 一直转圈 | 多半是 LLM API Key 错了或欠费，去 MiniMax 后台查余额 |
| 报 CORS 错误 | 后端 FastAPI 默认允许所有 CORS；如还有，看 nginx.conf proxy_set_header |
| 中文乱码 | 服务器 locale 不对：`sudo locale-gen zh_CN.UTF-8` |

---

## 🔒 Step 9：配置 HTTPS（强烈建议）

面试官用 HTTP 浏览器会提示「不安全」。**免费方案**：Let's Encrypt + 自己的域名。

### 9.1 准备域名

- 万网/阿里云买一个 `.com` 约 55 元/年，`.cn` 35 元/年
- 或用 **eu.org** / **pp.ua** 等免费二级域名
- 在域名 DNS 把 `www` 和 `@` 都解析到你的公网 IP（A 记录）

### 9.2 一键申请 HTTPS 证书

```bash
cd /opt/ai-me
chmod +x deploy-https.sh
sudo bash deploy-https.sh your-domain.com your@email.com
```

脚本会自动：
1. 装 certbot
2. 申请 Let's Encrypt 证书
3. 生成 HTTPS 版 nginx 配置
4. 重启服务
5. 配置 cron 每天自动续期（证书 90 天有效）

### 9.3 验证

```
https://your-domain.com
```

---

## 🔄 日常运维

### 修改资料后重启（不用重启整个服务）

```bash
cd /opt/ai-me
# 修改 profile.yaml / resume.md / projects/*.md 后
sudo docker compose restart backend
```

### 重建向量库（改了资料且改了 chunk 结构才需要）

```bash
sudo docker compose exec backend python scripts/init_kb.py
sudo docker compose restart backend
```

### 查看日志

```bash
# 实时日志
sudo docker compose logs -f

# 最近 100 行
sudo docker compose logs --tail=100 backend

# 业务日志（在容器内）
sudo docker compose exec backend tail -f /app/backend/logs/app.log
```

### 更新代码

```bash
cd /opt/ai-me
sudo git pull
sudo docker compose up -d --build
```

### 备份

```bash
# 备份向量库和个人资料
tar czf ai-me-backup-$(date +%Y%m%d).tar.gz backend/data backend/vector_db

# 备份到本地
scp aiadmin@你的公网IP:/opt/ai-me/ai-me-backup-*.tar.gz ./
```

---

## 💰 成本估算（学生 / 校招 demo）

| 项 | 费用 |
| --- | --- |
| 2C2G ECS（包月） | 阿里云 ¥50-100，腾讯云 ¥10-50（学生） |
| 5 Mbps 流量 | 校招 demo 几乎不动，¥10-30/月 |
| 域名（可选） | ¥35-55/年 |
| HTTPS 证书 | **¥0**（Let's Encrypt 免费） |
| MiniMax LLM | 校招 demo 月 ¥5-10 |
| **合计** | **¥20-80/月** |

---

## 🆘 终极排错

如果还是不行，按顺序收集信息：

```bash
# 1. 系统信息
uname -a && cat /etc/os-release

# 2. Docker 状态
sudo docker compose ps
sudo docker compose logs --tail=200 backend

# 3. 网络连通性
curl -v http://localhost:8000/health
sudo netstat -tlnp | grep -E '80|443|8000'

# 4. 磁盘 / 内存
df -h
free -h

# 5. 进程
ps aux | grep -E 'python|nginx'
```

把上面输出保存到文本文件，发给我（你的 AI 助手），我可以帮你远程诊断。

---

> 💡 **Tips**：
> 1. 第一次部署先在按量付费机器上跑通，再换包年。
> 2. API Key 别提交到 Git 公开仓库，会被盗刷。
> 3. 面试官访问前，先自己在浏览器点 5 个高频问题验证一遍。
> 4. 服务器时间要同步：`sudo timedatectl set-timezone Asia/Shanghai`。
# 🚀 AI-Me · 云服务器部署完全指南（阿里云 / 腾讯云）

> 把 AI-Me 部署到阿里云 ECS / 腾讯云 CVM，让面试官通过公网 IP 或域名直接访问。
> 整套方案：Docker Compose 一键起，Nginx 反向代理，可选 Let's Encrypt 免费 HTTPS。

> ✅ 本文档基于真实部署经验 —— 部署 AI-Me 到 218.244.140.70（阿里云 ECS）后整理。
> 你把里面的 IP 替换成你自己的就行。

---

## 📐 架构

```
访问者浏览器
    │  http://218.244.140.70:5500
    ↓
┌────────────────────────────────────┐
│  云服务器（Ubuntu 22.04）           │
│                                    │
│  Docker Compose                    │
│    ├─ frontend (nginx: 5500→80)   │ ← 反代 + 静态页（index.html）
│    │     │                         │
│    │     └ 反代 /chat、/profile、   │
│    │       /projects、/recommend   │
│    │       → backend               │
│    │                               │
│    └─ backend  (FastAPI: 8000)    │ ← AI 推理服务
│          ├─ ChromaDB（嵌入式）      │ ← 向量库持久化在 volume
│          └─ 调用 DeepSeek/         │
│              SiliconFlow API       │
└────────────────────────────────────┘
```

---

## 🛒 Step 1：购买云服务器

### 推荐配置（学生机 / 校招 demo 够用）

| 项 | 配置 |
| --- | --- |
| 厂商 | **阿里云**（[ecs.aliyuncs.com](https://ecs.console.aliyun.com)） 或 **腾讯云**（[cloud.tencent.com](https://cloud.tencent.com)） |
| 规格 | 2 vCPU / 4 GB 内存 / 5 Mbps 带宽（最低）<br>推荐 **2 vCPU / 4 GB / 5 Mbps** |
| 镜像 | **Ubuntu Server 22.04 LTS 64位** |
| 系统盘 | 40 GB 高效云盘（够用） |
| 带宽 | **按使用流量**（5 Mbps 峰值），校招 demo 一个月几十块 |
| 时长 | 1 个月起，建议先买 1 个月测试，稳定后改 **包年**（便宜一半以上） |
| 地域 | 选择最近的：**华南 / 华东 / 华北** 看你客户端在哪 |

### 学生优惠

- **阿里云**「高校计划」：9.5 元/月 1C2G
- **腾讯云**「学生认证套餐」：10 元/月 2C4G

> 💡 ECS 一定要绑定 **SSH 密钥对**，避免只能密码登录的麻烦（密钥对是国内 ECS 的最佳实践）。

---

## 🔐 Step 2：配置安全组（关键！）

买完 ECS 后，**最重要**的一步是开放端口。

### 阿里云操作路径

ECS 控制台 → 实例 → 顶部「**安全组**」 → 「**安全组规则**」 → 「**入方向**」 → 「**手动添加**」

| 端口 | 协议 | 授权对象 | 描述 |
|------|------|---------|------|
| **22/22** | SSH(TCP) | `你的公网IP/32` | SSH（**只对你**） |
| **5500/5500** | TCP | `0.0.0.0/0` | AI-Me 前端 |
| **8000/8000** | TCP | `你的公网IP/32` | Swagger 文档（**只对你**） |

### 腾讯云

CVM 控制台 → 实例 → **安全组** → 入站规则，同样添加 `22 / 5500 / 8000`，22 限制 IP。

> ⚠️ **为什么 8000 端口要限制 IP**：Swagger 文档里能看到你所有的 API，泄漏 API 路径对安全不利。面试官只需要 5500 端口的前端页面就行。
>
> ⚠️ **怎么查自己公网 IP**：访问 <https://ifconfig.me> 或 <https://ip.cn>（手机 4G 关 WiFi 时访问能得到家用宽带 IP）

---

## 🔑 Step 3：登录服务器（SSH 密钥对）

**最关键的一步 —— 配置好免密登录**，后面所有运维都不用再输密码。

### 3.1 本地生成 SSH 密钥对（如果没有）

```powershell
# 在你 Windows PowerShell 上
ssh-keygen -t ed25519 -f $env:USERPROFILE\.ssh\id_ed25519 -N '""'
# 会在 C:\Users\<你>\.ssh\ 下面生成 id_ed25519 和 id_ed25519.pub
```

### 3.2 把公钥加到阿里云 ECS

路径：ECS 控制台 → 实例 → 顶部「**更多**」 → 「**密码/密钥**」 → 「**绑定 SSH 密钥对**」 → 「**新建并绑定**」 → 把 `id_ed25519.pub` 完整内容（含末尾邮箱）粘贴到 Key 框 → 保存 → **重启实例**

### 3.3 测试免密登录

```powershell
ssh root@你的公网IP "echo OK_$(whoami)_at_$(hostname)"
# 应该直接输出，不再问密码
```

---

## 📦 Step 4：拉取代码

服务器上：

```bash
# 切到阿里云 apt 镜像（国内 ECS 出厂就用这个，但保险起见确认下）
ls /etc/apt/sources.list.d/
# 或 google 看 ECS 镜像默认源

# 装基础工具
apt-get update -o Acquire::Retries=2
apt-get install -y git curl

# 拉项目
mkdir -p /opt
cd /opt
git clone https://github.com/TXC05-25/ai-me.git
cd ai-me
```

---

## 🔧 Step 5：配置环境变量 + 上传个人资料

`.env` 包含真实 API Key，**不进 git**，服务器上独立维护。

### 方式 A：在服务器上 nano 编辑（推荐）

```bash
cd /opt/ai-me
cp .env.example .env
nano .env
```

填好后保存退出。注意容器内的**绝对路径**：

```bash
sed -i 's|CHROMA_DB_PATH=./backend/vector_db/chroma|CHROMA_DB_PATH=/app/backend/vector_db/chroma|' .env
sed -i 's|MILVUS_DB_PATH=./backend/vector_db/milvus.db|MILVUS_DB_PATH=/app/backend/vector_db/milvus.db|' .env
```

### 方式 B：从本地 scp 上传（更稳）

在你**本地 Windows PowerShell**：

```powershell
$IP = "你的公网IP"
$L = "C:\你的\项目\根\目录"  # 比如 C:\Users\<你>\Desktop\ai-me

# 上传 .env
scp "$L\.env" root@${IP}:/opt/ai-me/.env

# 上传 5 份个人资料
ssh root@${IP} "mkdir -p /opt/ai-me/backend/data/projects /opt/ai-me/frontend/public"
scp "$L\backend\data\profile.yaml"   root@${IP}:/opt/ai-me/backend/data/profile.yaml
scp "$L\backend\data\resume.md"      root@${IP}:/opt/ai-me/backend/data/resume.md
scp "$L\backend\data\qa_pairs.jsonl" root@${IP}:/opt/ai-me/backend/data/qa_pairs.jsonl
scp "$L\frontend\public\resume.pdf"  root@${IP}:/opt/ai-me/frontend/public/resume.pdf

# 2 个项目 .md 文件
scp "$L\backend\data\projects\ai_me.md"   root@${IP}:/opt/ai-me/backend/data/projects/
scp "$L\backend\data\projects\rag_graph.md" root@${IP}:/opt/ai-me/backend/data/projects/

# 服务器侧给 .env 收紧权限
ssh root@${IP} "chmod 600 /opt/ai-me/.env"
```

---

## 🚀 Step 6：一键部署

```bash
cd /opt/ai-me
chmod +x deploy.sh
sudo bash deploy.sh
```

脚本会自动：

1. 切换 apt 源到阿里云镜像（GFW 友好）
2. 用 apt 装 Docker（避开 `get.docker.com` 国内被墙）
3. 拉取/更新代码
4. 配置 `daemon.json` 镜像源 + 启动 dockerd
5. 检查 `.env` / 个人资料完整
6. `docker compose up -d --build` 启动两个容器
7. 轮询 `/health` 等启动（首次启动会重建向量库约 1-3 分钟）

### 查看进度

```bash
cd /opt/ai-me
docker compose ps                    # 看容器状态
docker compose logs -f backend       # 看后端日志（Ctrl+C 退出）
tail -f /tmp/deploy.log              # 看 deploy.sh 完整日志
```

### 验证部署

```bash
curl http://localhost:8000/health
# 期望：{"status":"ok",...}

curl -I http://localhost:5500
# 期望：HTTP/1.1 200 OK
```

### 部署成功后的访问入口

```
[hh:mm:ss]  部署完成！
 - 🌐 主访问入口（推荐给面试官的链接）：  http://你的公网IP:5500
 - 📖 后端 API 文档（Swagger）：          http://你的公网IP:8000/docs
```

---

## 🌐 Step 7：通过公网 IP 访问

打开浏览器，访问：

```
http://你的公网IP:5500
```

### 遇到问题的排查清单

| 现象 | 排查 |
| --- | --- |
| 打不开网页 | 安全组 5500 端口没开；`docker compose ps` 看 frontend 是否 running |
| 页面打开了但聊天没反应 | 看后端 logs：`docker compose logs backend`；检查 .env 的 API Key |
| AI 一直转圈 | 多半是 LLM API Key 错了或欠费，去 DeepSeek 后台查余额 |
| 报 CORS 错误 | 后端 FastAPI 默认允许所有 CORS；如还有，看 nginx.conf proxy_set_header |
| 中文乱码 | 服务器 locale：`sudo locale-gen zh_CN.UTF-8` |
| 后端起不来 | 看 `docker logs ai-me-backend \| tail -100`，多半是 config 路径错（CHROMA_DB_PATH 要绝对路径）|

---

## 🔒 Step 8：HTTPS（强烈建议）

面试官用 HTTP 浏览器会提示「不安全」。**免费方案**：Let's Encrypt + 自己的域名。

### 8.1 准备域名

- 万网/阿里云买一个 `.com` 约 55 元/年，`.cn` 35 元/年
- 在域名 DNS 把 `www` 和 `@` 都解析到你的公网 IP（A 记录）

### 8.2 一键申请 HTTPS 证书

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

---

## 🔄 日常运维

### 修改资料后重启（不用重启整个服务）

```bash
cd /opt/ai-me
# 修改 profile.yaml / resume.md / projects/*.md 后
docker compose restart backend
```

> ⚠️ **重启后向量化要 1-2 分钟**，因为 ChromaDB 会读取最新的 .md / .yaml 重建索引。第一次提问时会触发重建。

### 重建向量库（改了资料且改了 chunk 结构才需要）

```bash
docker compose exec backend python -m utils.loader
docker compose restart backend
```

### 查看日志

```bash
# 实时日志
docker compose logs -f

# 最近 100 行
docker compose logs --tail=100 backend

# 业务日志（在容器内）
docker compose exec backend tail -f /app/backend/logs/app.log
```

### 更新代码

```bash
# 本地 (Windows PowerShell)
git add .
git commit -m "fix: ..."
git push

# 服务器
ssh root@<IP> "cd /opt/ai-me && bash deploy.sh"
```

> `bash deploy.sh` 自动 `git pull` + `docker compose up -d --build`，**一条命令完成更新 + 重启**。

### 备份

```bash
# 备份向量库和个人资料
tar czf ai-me-backup-$(date +%Y%m%d).tar.gz backend/data backend/vector_db

# 备份到本地
scp root@<IP>:/opt/ai-me/ai-me-backup-*.tar.gz ./
```

---

## 💰 成本估算（学生 / 校招 demo）

| 项 | 费用 |
| --- | --- |
| 2C2G ECS（包月） | 阿里云 ¥50-100，腾讯云 ¥10-50（学生） |
| 5 Mbps 流量 | 校招 demo 几乎不动，¥10-30/月 |
| 域名（可选） | ¥35-55/年 |
| HTTPS 证书 | **¥0**（Let's Encrypt 免费） |
| DeepSeek LLM | 校招 demo 月 ¥5-10 |
| **合计** | **¥20-80/月** |

---

## ⚠️ 国内 ECS 部署常踩的两个坑（v1.3 已修复）

### 坑 1：`get.docker.com:443` 被墙

deploy.sh 默认从 `get.docker.com -o get-docker.sh` 装 docker，**国内访问失败**。
**解决**：deploy.sh 改为 `apt-get install -y docker.io`，从阿里云镜像装。

### 坑 2：`registry-1.docker.io` 拉镜像失败

`docker pull nginx:alpine` 直接 timeout。
**解决**：deploy.sh 自动写 `/etc/docker/daemon.json` 加 `docker.m.daocloud.io` 镜像源。

> 这两个坑在 `deploy.sh` 里都已经处理过了，**新部署不用管**。

---

## 🆘 终极排错

如果还是不行，按顺序收集信息：

```bash
# 1. 系统信息
uname -a && cat /etc/os-release

# 2. Docker 状态
docker compose ps
docker compose logs --tail=200 backend

# 3. 网络连通性
curl -v http://localhost:8000/health
ss -tlnp | grep -E '5500|8000'

# 4. 磁盘 / 内存
df -h
free -h

# 5. 进程
ps aux | grep -E 'python|nginx'
```

把上面输出保存到文本文件，可以远程发出来诊断。

---

> 💡 **Tips**：
> 1. 第一次部署先在按量付费机器上跑通，再换包年。
> 2. API Key 别提交到 Git 公开仓库，会被盗刷。
> 3. 面试官访问前，先自己在浏览器点 5 个高频问题验证一遍。
> 4. 服务器时间要同步：`sudo timedatectl set-timezone Asia/Shanghai`。
> 5. 22 端口限制到你的 IP，但如果你家宽带 IP 总变，用 0.0.0.0/0 + 装 fail2ban (`apt install fail2ban`)。

# 跟台端侧离线部署 POC

## 环境要求

- Python 3.12+
- SQLite3（Python 自带）
- 2GB RAM
- Linux / macOS

## 安装步骤

```bash
# 1. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 2. 安装精简依赖
pip install -r deploy/offline-assistant/requirements-offline.txt

# 3. 初始化数据库
python -c "from assistant.app.database import init_db; init_db()"
```

## 离线启动命令

```bash
source venv/bin/activate
export CLOUD_API_URL="http://<cloud-host>:8000"   # 可选，默认 localhost:8000
uvicorn assistant.app.main:app --host 0.0.0.0 --port 8080
```

## 首次同步流程

1. 启动服务后，调用 `POST /offline/enable` 进入离线模式
2. 本地写操作会自动记录到 `offline_sync_log` 表
3. 网络恢复后，调用 `POST /offline/sync` 触发同步
4. 调用 `POST /offline/disable` 切回在线模式

### API 端点

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/offline/status` | 查看在线状态、未同步数、本地数据统计 |
| POST | `/offline/sync` | 触发未同步数据上传 |
| POST | `/offline/enable` | 切换离线模式 |
| POST | `/offline/disable` | 切换在线模式（自动触发全量同步） |
| POST | `/offline/queue` | 手动加入同步队列 |

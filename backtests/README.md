# FinTools Backtests

`backtests` 现在只保留远程 agent 回测链路，不再包含或支持本地 agent。

## 目录

```text
backtests/
├── backend/              # FastAPI 后端
│   ├── remote_agents_a2a/  # 远程 A2A agent 客户端
│   ├── end_points/         # API 路由与执行逻辑
│   ├── db/                 # 数据模型与初始化脚本
│   └── scripts/            # 数据库辅助脚本
└── frontend/             # React 前端
```

## 当前行为

- Rule 只支持 `remote_agent`
- `Rule.info` 只接受远程 A2A URL，或包含 `base_url` / `access_token` 的 JSON 字符串
- Rules 和 Simulators 页面都只展示 remote agents
- `remote_agents_a2a/trading_agent_server.py` 和 `streaming_agent_executor.py` 保留为占位文件，不再提供本地 server 模式

## 启动前提

- Python 3.11+
- Node.js 16+
- 可用的远程 A2A agent URL
- `FINTOOLS_ACCESS_TOKEN`

## 后端启动

```bash
cd backtests/backend
pip install -r requirements.txt
python manage.py
```

默认地址：`http://localhost:8888`

如果使用 `uv`：

```bash
cd backtests/backend
uv sync
uv run python manage.py
```

## 前端启动

```bash
cd backtests/frontend
npm install
npm run dev
```

默认地址：`http://localhost:8000`

## 环境变量

建议在 `backtests/backend/.env` 中至少配置：

```bash
FINTOOLS_ACCESS_TOKEN=your-fintools-access-token
TUSHARE_TOKEN=your-tushare-token
```

数据库配置现在分两层：

- `backtests/backend/service.conf` 只管服务启动参数，并指向根目录数据库配置
- 根目录 [config.json](/Users/lu/development/fintools_all/fintools_skills/fintools-client-backtests-skill%20%20/config.json) 决定数据库后端，数据库设置都放在 `database` 下

默认 `database.backend="sqlite"`，数据库文件在 `database.sqlite.path`。如果要切换 MySQL，只改 `database.backend="mysql"`，并填写 `database.mysql` 下面的连接参数；SQLite 和 MySQL 配置是分开的。

## 初始化数据库

```bash
cd backtests/backend
./scripts/init_db.sh
```

脚本会按根目录 `config.json` 的配置初始化数据库。默认是创建 `.runtime/database/backtests.sqlite3` 并自动导入当前后端所需的内置备份数据。

## 使用方式

1. 启动后端和前端。
2. 在 Rules 页面创建 `remote_agent` rule。
3. 在 `A2A URL` 中填入远程 agent 地址，例如：

```text
http://8.153.13.5:8000/api/v1/agents/62/a2a/
```

4. 将股票池绑定到 rule。
5. 在 Rules 页面执行当日 agent。
6. 在 Simulators 页面基于该 rule 创建并运行回测。

## 已知限制

- 当前未提供内置 mock remote agent；必须接入真实远程 A2A 服务。
- 若依赖未安装完整，后端会在 import 阶段失败；首个已确认缺失项通常是 `sqlalchemy`。
- `backups/` 中仍保留了历史数据快照，里面可能包含旧的 `local_agent` 记录；代码不会再执行这些类型。

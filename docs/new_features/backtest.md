# Backtests 功能需求

## 目标

本文档用于记录这个 skill 仓库中 `backtests` 集成的目标需求行为。

核心目标有两个：

- 保持 `backtests` 展示层和上层调用方式稳定
- 让数据库后端选择与 agent 结果同步逻辑明确、可配置、可重复执行

## 总体架构

这个 skill 目前有两个主要功能，它们需要协同工作：

1. `agentclient`
2. `backtests`

### agentclient 功能

`agentclient` 负责调用远程 agent，并把原始执行结果写入：

- `.runtime/database/trading_agent_runs.db`

这个数据库是上游 agent 结果的运行时存储。

### backtests 功能

`backtests` 负责展示回测侧的数据。

每次 `backtests` 被唤醒、初始化，或者被要求展示数据时，都必须先把：

- `.runtime/database/trading_agent_runs.db`

里的数据同步到 `backtests` 自己数据库中的：

- `agent_trading`

这不是一次性的迁移动作，而是 `backtests` 每次被唤醒时都要执行的运行时同步行为。

## 数据库后端要求

### 配置驱动的后端选择

`backtests` 的上层业务逻辑不能硬绑定 MySQL 或 SQLite。

数据库后端必须通过 skill 根目录配置文件控制：

- `config.json`

同时，配置文件需要为未来的其他配置预留空间，不能只为数据库单独平铺。

### 配置结构要求

数据库配置必须统一收在：

- `database`

下面。

在 `database` 下，SQLite 和 MySQL 的配置必须分开存放：

- `database.backend`
- `database.common`
- `database.sqlite`
- `database.mysql`

当前选择的数据库后端由以下字段决定：

- `database.backend`

### 默认后端

默认数据库后端必须是：

- `sqlite`

### SQLite 要求

当 `database.backend = "sqlite"` 时：

- `backtests` 必须使用本地 SQLite 数据库
- 数据库文件必须放在 `.runtime/database` 下面
- 当前默认路径是 `.runtime/database/backtests.sqlite3`

### MySQL 要求

当 `database.backend = "mysql"` 时：

- `backtests` 必须通过配置切换到 MySQL
- 从 SQLite 切换到 MySQL 时，不允许改上层业务逻辑
- MySQL 所需连接信息必须全部来自 `config.json`

## Backtests 唤醒时的同步要求

每次 `backtests` 被唤醒时，在展示任何回测数据之前，都必须先执行一次同步。

这一步同步必须完成以下事情：

1. 从 `.runtime/database/trading_agent_runs.db` 读取数据
2. 把数据转换成 `backtests` 需要的格式
3. 将转换后的结果追加写入 `backtests` 数据库的 `agent_trading` 表

这一步属于 `backtests` 的正常初始化/展示前置流程，不是人工手动维护任务。

## 数据转换规则

从 `trading_agent_runs.db` 转换到 `backtests.agent_trading` 时，交易结果映射规则必须是：

- `buy` 映射为 `indicating`
- 其他任何结果一律映射为 `not_indicating`

这个映射发生在同步过程中，在写入 `backtests.agent_trading` 之前完成。

## 去重与“每个 agent 当天最后一条”规则

`trading_agent_runs.db` 中，同一天可能会有多次运行结果。

但 `backtests.agent_trading` 的目标不是把所有 agent 混在一起只保留一条，而是：

- 每个 agent
- 每只股票
- 每个交易日

各自只保留一条有效记录。

因此，同步逻辑必须满足以下规则：

- 对于同一个 agent 在同一只股票、同一个交易日内的重复运行结果，只取当天最后一条记录进行转换并写入 `backtests.agent_trading`

换句话说：

- 如果同一个上游 agent 在同一天对同一只股票运行了多次，`backtests` 在同步时必须忽略当天较早的记录，只使用该 agent 当天最后一次运行结果
- 如果是不同 agent，即使它们在同一天对同一只股票都产生了结果，也必须分别保留各自当天最后一条

## 数据归属边界

数据职责划分应该是：

- `trading_agent_runs.db` 保存上游 agent 的原始运行结果
- `backtests.agent_trading` 保存面向回测展示的、已经归一化后的日级信号记录

因此，从 `backtests` 的视角看，`agent_trading` 是一个派生表，它的内容应该在每次 `backtests` 唤醒时，通过同步上游运行时数据库来更新。

## 当前归属策略

同步到 `agent_trading` 时，仍然需要确定这些记录属于哪一条 `rule_id`。

当前实现约定是：

- 将 `trading_agent_runs.db` 同步结果归属到 `backtests` 中的 `remote_agent` 规则
- 如果当前只有一条 `remote_agent` 规则，则直接写入该规则
- 如果当前存在多条 `remote_agent` 规则，则默认使用 `id` 最小的那一条，并记录告警日志

这个策略保证当前 skill 可以直接运行，同时不影响后续继续把归属逻辑配置化。

## Rule 自动补全要求

`trading_agent_runs.db` 里的数据来源于上游 agent。

因此，在把数据同步到 `backtests.agent_trading` 之前，还必须保证对应 agent 在 `backtests.rule` 中已经存在。

如果上游 `trading_agent` 对应的 agent 在 `rules` 里不存在，则系统需要先自动补一条 `remote_agent` 规则，再继续同步交易记录。

### 自动补全的 rule 类型

自动创建的 rule 必须是：

- `type = remote_agent`

### 自动补全的 rule 字段

自动创建 rule 时，至少要补齐以下信息：

- `id`
- `name`
- `description`
- `info`
- `agent_id`

其中：

- `id` 是 `backtests.rule` 的内部主键
- `info` 用来保存该 agent 对应的远程访问地址
- `agent_id` 用来保存上游 agent 的唯一标识，并且必须唯一

也就是说：

- 如果上游 agent 的 `agent_id = 105`
- 那么自动补建出来的 `backtests.rule.agent_id` 应该保存 `105`
- 但 `backtests.rule.id` 仍然保持系统内部自增主键语义

### 自动补全触发时机

这一步不是人工维护，而是 `backtests` 在每次被唤醒并执行同步前，都需要自动检查：

1. 上游 `trading_agent_runs.db` 中涉及哪些 agent
2. 这些 agent 是否已经存在于 `backtests.rule`
3. 对缺失的 agent 自动补建 `remote_agent` rule
4. 再把对应交易结果同步到 `agent_trading`

### 自动补全目标

最终效果应该是：

- `trading_agent_runs.db` 中出现的新 agent，不需要人工先去 Rules 页面建 rule
- `backtests` 被唤醒时可以自动把缺失 rule 补齐
- 补齐后的 rule 具备展示和后续回测所需的最少元信息
- 自动补齐时，通过唯一的 `agent_id` 把上游 agent 和 `backtests.rule` 建立一一对应
- 随后的 `agent_trading` 同步可以正确归属到对应的 `rule_id`

## Pool 处理原则

`trading_agent_runs.db` 同步到 `backtests` 时，不应该自动创建任何 pool，也不应该自动修改 `rule_pool`、`pool`、`pool_stock`。

也就是说：

- `backtests` 唤醒时只负责补齐缺失的 `remote_agent rule`
- `backtests` 唤醒时只负责把交易结果同步到 `agent_trading`
- 不允许在这条同步链路里自动补股票池

### agent 尚未设置 pool 时的正确处理方式

如果用户还没有给某个 agent 设置股票池，这不应阻塞：

- `agentclient` 调用远程 agent
- `trading_agent_runs.db` 写入原始结果
- `backtests` / `simulator` 基于已有信号继续运行

正确逻辑是：

1. 在用户主动调用该 agent 时，系统检查这个 agent 是否已经设置 pool
2. 如果没有设置 pool，则询问用户是否要为这个 agent 设定股票池
3. 只有在用户确认后，才进入股票池配置流程
4. 如果用户不设置 pool，系统也不能自动代替用户创建任何临时 pool

### Pool 处理目标

最终效果应该是：

- pool 由用户显式配置，而不是由同步程序隐式创建
- `backtests` 同步链路和 pool 管理链路分离
- agent 没有固定股票池时，`simulator` 仍然可以运行
- `backtests` 的 `agent_trading` 同步不依赖 pool 是否存在

## Backtests 调用 Agent 的复用要求

当 `backtests` 主动去执行 remote agent 时，不允许再维护一套独立的 A2A 调用实现。

也就是说，`backtests` 不应该自己单独处理以下逻辑：

- agent card 获取
- access token 获取
- access token 缓存
- Authorization header 组装
- trading agent 的底层请求流程

### 必须复用的现有调用链

`backtests` 执行 remote agent 时，必须复用 skill 里已经存在的调用流程，至少包括：

- `scripts/run_agent_client.py` 中现有的 token 解析 / 缓存逻辑
- `scripts/run_agent_client.py` 中现有的 trading agent 调用入口
- skill 当前已经在使用的 streaming / polling 调用实现

`backtests` 在这条链路里的职责，只应该是：

- 决定要跑哪些股票
- 把股票代码和 agent URL 交给现有 skill 调用链
- 读取调用结果并更新 `agent_trading`

### UI 指定股票范围的执行规则

`backtests` 执行 remote agent 时，股票范围由 UI 操作决定：

- 在 Agents 页面点击 `Run Today` 时，执行当前 agent 所关联 pool 中的全部股票
- 在 Agents 页面点击某一只股票的 `Run` 时，只执行该股票

也就是说：

- UI 决定“跑哪些股票”
- skill 现有调用链决定“怎么调 agent”

### Access Token 规则

获取 access token 的方式必须复用 skill 里现有逻辑。

不允许 `backtests` 再自己新增另一套 token 来源或缓存方式。

对于 `backtests` 这条适配链路，token 来源必须遵循以下收敛规则：

- 优先使用显式传入的 token
- 如果没有显式传入，则只读取 skill 运行目录下已经缓存好的 `.runtime/runs/.fintools_access_token`
- 不允许 `backtests` 为了执行 agent 再去读取 `.env`
- 不允许 `backtests` 再从环境变量回退读取 `FINTOOLS_ACCESS_TOKEN`
- 如果缓存文件里仍然是示例值或占位 token，必须直接报明确错误，而不是继续请求远端后再得到 `401`

### 适配边界

为了把 `backtests` 接到 skill 现有调用链上，可以新增适配层。

但是：

- 不允许修改 `agents_client/` 目录下的现有实现
- 如果需要适配，适配代码必须放在 `backtests` 自己的调用层或单独 adapter 层

### Streaming 输出要求

当 `backtests` 在页面中执行 remote agent 并通过 SSE 展示日志时，report / status 文本必须实时增量输出。

不允许采用“先把 skill stdout 全部缓存，等远端执行完成后再一次性吐给前端”的方式。

正确行为应该是：

- skill 调用链中一旦产生新的 stdout / stderr 文本
- `backtests` 适配层就要立即把这一行增量转发到 SSE
- 前端日志面板要边运行边看到 report 持续追加
- 最终 `remote_result` 只能在远端执行真正结束后再输出

如果需要实现这件事，允许在 `backtests` adapter 层增加“stdout/stderr -> async queue -> SSE”的流式桥接层。

但仍然：

- 不允许修改 `agents_client/`
- 不允许重新实现另一套 remote agent 协议调用
- 只能复用 skill 现有调用链，并把它的增量输出实时透传出来

## 目标实现流程

目标稳定行为应该是：

1. 远程 agent 通过 `agentclient` 运行
2. 原始结果写入 `trading_agent_runs.db`
3. `backtests` 被唤醒
4. `backtests` 先检查上游 agent 是否已经存在对应的 `remote_agent` rule
5. 缺失的 rule 自动补齐，并写入 agent 地址、名称、说明、agent_id 等信息
6. `backtests` 再从 `trading_agent_runs.db` 执行同步
7. 同一个 agent 的同日重复结果按“每个 agent 当天最后一条”规则折叠
8. `buy` 映射为 `indicating`
9. 其他结果映射为 `not_indicating`
10. 归一化后的记录追加写入 `backtests.agent_trading`
11. `backtests` 基于自己的数据库进行展示
12. 如果用户后续主动调用某个尚未设置 pool 的 agent，系统单独询问是否配置股票池
13. 如果用户在 `backtests` 中主动运行 agent，则由 UI 指定股票范围，并复用 skill 现有 agent 调用链执行

## 验收要求

只有当以下条件全部满足时，这个需求才算完成：

- `backtests` 的数据库后端选择完全由配置驱动
- 默认后端是 SQLite
- SQLite 和 MySQL 配置在 `config.json` 的 `database` 下分开存放
- 切换到 MySQL 时只需要改配置，不需要改业务代码
- 如果上游出现新的 agent，而 `rules` 中不存在对应项，系统会自动补齐 `remote_agent` rule
- 自动补齐的 rule 会包含 `id`、远程地址、`name`、`description`、`info`、`agent_id` 等必要字段
- `rule.id` 保持内部自增，`agent_id` 作为外部 agent 唯一标识
- `backtests` 在每次唤醒/初始化/展示前都会执行 `trading_agent_runs.db` 同步
- 同步结果写入 `backtests.agent_trading`
- `buy -> indicating` 的转换规则被严格执行
- 非 `buy` 结果统一映射为 `not_indicating`
- 对于同一个 agent 在同一天的多次运行，只导入该 agent 当天最后一条记录进入 `agent_trading`
- 不同 agent 在同一天对同一只股票的结果需要分别保留
- `backtests` 唤醒时不会自动创建任何 pool，也不会自动修改 agent 的 pool 关联
- 如果 agent 尚未设置 pool，应该在用户调用该 agent 时询问是否配置股票池
- agent 没有 pool 时，不影响 `simulator` 和 `agent_trading` 的同步链路
- `backtests` 主动执行 remote agent 时，必须复用 skill 现有调用链，而不是维护独立的 A2A 调用实现
- `backtests` 只负责根据 UI 决定股票范围：`Run Today` 跑 pool 全量，单股 `Run` 只跑该股票
- 获取 access token 的方式必须复用 skill 现有逻辑
- `backtests` 适配层只允许读取显式传入 token 或 skill 已缓存的 `.runtime/runs/.fintools_access_token`，不能回退到 `.env` 或环境变量
- `backtests` 执行 remote agent 时，SSE 必须实时增量透传 skill 输出，不能等全部完成后再一次性输出
- 不允许修改 `agents_client/` 目录下的现有实现；如需接入，只能新增适配层

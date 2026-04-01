# Polling 模式数据库写入失败 - 返回格式不一致

**日期**: 2026-04-01
**严重程度**: 高
**状态**: 已解决

## 问题现象

### 用户报告
```
❌ 测试失败，数据库没有新增记录
```

### 错误特征
- Streaming 模式：✓ 正常写入数据库
- Polling 模式：❌ 数据库写入失败
- 错误信息： misleading 的 `UnboundLocalError`，掩盖了真正的问题

## 根本原因

### 返回格式不一致

**Streaming 模式返回**：
```python
{
    "status": "completed",
    "result": {"action": "buy"},  # 字典格式
    "error": None,
    "artifacts": [...]
}
```

**Polling 模式返回**：
```python
{
    "status": "completed",
    "result": "BUY",  # 纯字符串格式
    "error": None,
    "artifacts": [...]
}
```

### 数据库写入代码期望统一格式

`scripts/run_agent_client.py` 中的数据库写入代码：
```python
# 原始代码 - 期望 result 是字典
action = result.get("result", {}).get("action", "unknown")
```

当 polling 模式返回字符串时：
- `result.get("result", {})` 返回 `"BUY"`（字符串）
- `"BUY".get("action", "unknown")` → `AttributeError: 'str' object has no attribute 'get'`
- 异常处理逻辑跳过了 action 赋值
- 最终导致 `UnboundLocalError: cannot access local variable 'action'`

## 解决方案

### 方案选择

**方案 A**: 在 agents_client 层统一返回格式 ✓ **采用**
- 在 `agents_client/db_polling/db_client.py` 中标准化结果
- 下游代码无需修改
- 统一接口契约

**方案 B**: 在 scripts 层处理两种格式 ✗ 未采用
- 需要修改数据库写入逻辑
- 增加复杂度和维护成本

### 实施细节

#### 修改 1: `agents_client/db_polling/db_client.py`

在 `wait_for_task` 方法的所有返回点添加格式标准化：

```python
async def wait_for_task(self, task_id: str) -> dict[str, Any]:
    # ... 轮询逻辑 ...

    if task.get("status") in {"completed", "failed"}:
        # 标准化result格式，与streaming模式对齐
        if isinstance(task.get("result"), str):
            raw_result = task.get("result", "")
            # 将 "BUY"/"SELL"/"HOLD" 等字符串转换为统一格式
            task["result"] = {"action": raw_result.lower()}
        self._print_final_result(task)
        return task

    # ... 其他返回点同样处理 ...
```

**关键点**：
- 在 **所有返回路径** 应用标准化（success, failed, timeout）
- 将字符串转换为小写，与 streaming 模式一致
- 保持 downstream 代码不变

#### 修改 2: `scripts/run_agent_client.py`

简化数据库写入逻辑，移除模式特定的解析代码：

```python
# 修改前：复杂的模式特定解析
if mode == "streaming":
    action = result.get("result", {}).get("action", "unknown")
elif mode == "polling":
    # 尝试解析字符串格式的结果
    try:
        parsed = json.loads(result.get("result", "{}"))
        action = parsed.get("action", "unknown")
    except:
        action = "unknown"

# 修改后：统一处理
action = result.get("result", {}).get("action", "unknown")
action = str(action).lower()
```

## 验证

### 测试 Streaming 模式
```bash
python3 scripts/run_agent_client.py \
  --agent-type trading \
  --mode streaming \
  --stock-code 600519 \
  --agent-url http://8.153.13.5:8000/api/v1/agents/105/a2a/ \
  --access-token <token>
```

✓ 结果：`[status] SSOT: Recorded action 'buy' into trading_agent_runs.db`

### 测试 Polling 模式
```bash
python3 scripts/run_agent_client.py \
  --agent-type trading \
  --mode polling \
  --stock-code 600519 \
  --agent-url http://8.153.13.5:8000/api/v1/agents/105/a2a/ \
  --access-token <token>
```

✓ 结果：`[status] SSOT: Recorded action 'buy' into trading_agent_runs.db`

### 数据库验证

```sql
SELECT id, run_id, stock_code, action, result, mode
FROM trading_agent_runs
ORDER BY id DESC LIMIT 3;
```

| ID | Stock | Action | Result Format | Mode |
|----|-------|--------|---------------|------|
| 15 | 600519 | buy | `{"action": "buy"}` | polling ✓ |
| 14 | 600519 | buy | `{"action": "buy"}` | streaming ✓ |
| 13 | 600519 | buy | `{"action": "buy"}` | streaming ✓ |

两种模式现在都返回统一的字典格式。

## 经验教训

### 1. 统一接口契约的重要性

**教训**：当 SDK 支持多种执行模式时，**必须在最上层统一返回格式**，而不是让下游代码处理多种格式。

**最佳实践**：
- 在 client 层（agents_client）做标准化
- 确保 streaming/polling/sync/async 等所有模式返回相同的数据结构
- 在文档中明确说明返回格式

### 2. 错误信息的误导性

**教训**：`UnboundLocalError` 是一个误导性的错误，真正的问题是类型不匹配（字符串 vs 字典）。

**调试建议**：
- 当遇到 `UnboundLocalError` 时，检查变量是否在异常发生前被正确赋值
- 添加日志打印实际的数据类型和内容
- 不要只看异常信息，要追溯数据流

### 3. 在所有返回路径应用修复

**教训**：修复只应用在 success 路径是不够的，failed 和 timeout 路径也需要相同的处理。

**检查清单**：
```python
# ✓ 正确：所有返回路径都标准化
if status == "completed":
    normalize_result(result)
    return result
elif status == "failed":
    normalize_result(result)  # 不要忘记这里
    return result
else:
    normalize_result(result)  # 以及 timeout 等其他路径
    return result

# ✗ 错误：只在成功路径标准化
if status == "completed":
    normalize_result(result)
    return result
else:
    return result  # 这里会返回非标准化格式
```

### 4. 类型提示和文档的重要性

**教训**：如果代码有明确的类型提示和文档，这种问题可以在静态分析阶段发现。

**改进建议**：
```python
from typing import TypedDict, Literal

class AgentResult(TypedDict):
    status: Literal["completed", "failed", "timeout"]
    result: dict[str, Any]  # 明确说明 result 必须是字典
    error: str | None
    artifacts: list[dict[str, Any]]

def wait_for_task(self, task_id: str) -> AgentResult:
    """返回标准化的 agent 执行结果

    Returns:
        AgentResult: result 字段始终是字典格式，包含 'action' 键
    """
```

### 5. 测试覆盖多种模式

**教训**：必须测试所有执行模式，不能只测试一种模式就认为没有问题。

**测试策略**：
- 为每种模式（streaming, polling, sync, async）编写单独的测试用例
- 验证返回格式的类型和结构
- 确保下游处理代码对每种模式都有效

## 防止复发

### 代码审查检查点

当审查涉及多模式 SDK 的代码时，检查：

- [ ] 所有执行模式是否返回相同的数据结构？
- [ ] 是否在 client 层做了格式标准化？
- [ ] 下游代码是否假设了特定的数据类型？
- [ ] 所有返回路径（success, failed, timeout）是否都应用了标准化？
- [ ] 是否有类型提示或文档说明返回格式？

### 测试检查点

- [ ] 测试了所有执行模式？
- [ ] 验证了数据库写入对每种模式都有效？
- [ ] 检查了错误路径（failed, timeout）的处理？
- [ ] 有集成测试覆盖端到端流程？

## 相关文件

- `agents_client/db_polling/db_client.py` - Polling 模式客户端
- `scripts/run_agent_client.py` - Agent 运行脚本
- `docs/error_notes/polling_streaming_format_mismatch.md` - 本文档

## 参考

- [API Client Return Format Normalization - 如果需要通用解决方案](../../.claude/skills/api-client-format-normalization/SKILL.md) (已删除，不作为通用 skill)

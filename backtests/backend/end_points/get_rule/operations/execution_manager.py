import asyncio
import logging
from datetime import datetime
from typing import Dict, Optional
from enum import Enum

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class Execution:
    def __init__(self, execution_id: str, rule_id: int, stock_code: Optional[str] = None):
        self.execution_id = execution_id
        self.rule_id = rule_id
        self.stock_code = stock_code  # None means all stocks
        self.status = ExecutionStatus.PENDING
        self.created_at = datetime.now()
        self.logs = []  # Store logs here
        self.generator = None  # Async generator for the execution

    def add_log(self, log: dict):
        """Add a log entry"""
        log['timestamp'] = datetime.now().isoformat()
        self.logs.append(log)
        logger.info(f"[{self.execution_id}] {log.get('type', 'unknown')}: {log.get('message', '')[:100]}")

    def set_generator(self, generator):
        """Set the async generator for this execution"""
        self.generator = generator


class ExecutionManager:
    """Manages ongoing and completed executions"""

    def __init__(self):
        self.executions: Dict[str, Execution] = {}
        self.cleanup_interval = 3600  # 1 hour
        self.retention_time = 7200  # 2 hours

    def create_execution(self, rule_id: int, stock_code: Optional[str] = None) -> Execution:
        """Create a new execution"""
        import uuid
        execution_id = str(uuid.uuid4())[:8]

        execution = Execution(execution_id, rule_id, stock_code)
        self.executions[execution_id] = execution

        logger.info(f"Created execution {execution_id} for rule {rule_id}, stock {stock_code}")
        return execution

    def get_execution(self, execution_id: str) -> Optional[Execution]:
        """Get an execution by ID"""
        return self.executions.get(execution_id)

    async def execute_and_capture(self, execution: Execution, stream_func, *args):
        """Run the execution and capture logs"""
        execution.status = ExecutionStatus.RUNNING
        execution.add_log({
            "type": "start",
            "message": f"Execution started for rule {execution.rule_id}"
        })

        try:
            async for log in stream_func(*args):
                execution.add_log(log)

            execution.status = ExecutionStatus.COMPLETED
            execution.add_log({
                "type": "complete",
                "message": "Execution completed"
            })

        except Exception as e:
            execution.status = ExecutionStatus.FAILED
            execution.add_log({
                "type": "error",
                "message": f"Execution failed: {str(e)}"
            })
            logger.error(f"Execution {execution.execution_id} failed: {e}")

    async def stream_execution_logs(self, execution_id: str):
        """Stream logs from an execution"""
        execution = self.get_execution(execution_id)

        if not execution:
            yield {
                "type": "error",
                "message": f"Execution {execution_id} not found"
            }
            return

        # Stream existing logs first
        for log in execution.logs:
            yield log

        # If execution is still running, stream new logs as they arrive
        if execution.status == ExecutionStatus.RUNNING:
            last_log_count = len(execution.logs)
            while execution.status == ExecutionStatus.RUNNING:
                await asyncio.sleep(0.1)  # Poll for new logs

                # Yield new logs
                new_logs = execution.logs[last_log_count:]
                for log in new_logs:
                    yield log
                last_log_count = len(execution.logs)

        # Execution completed
        yield {
            "type": "stream_complete",
            "message": f"Execution {execution.status.value}",
            "status": execution.status.value
        }

    def cleanup_old_executions(self):
        """Remove old executions to free memory"""
        import time
        current_time = time.time()

        to_remove = []
        for exec_id, execution in self.executions.items():
            age = (datetime.now() - execution.created_at).total_seconds()
            if age > self.retention_time:
                to_remove.append(exec_id)

        for exec_id in to_remove:
            del self.executions[exec_id]
            logger.info(f"Cleaned up execution {exec_id}")


# Global execution manager instance
execution_manager = ExecutionManager()

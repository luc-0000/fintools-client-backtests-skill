"""
A2A Agent Client 公共工具

提供通用的客户端功能：
- 报告下载（可被 streaming 和 db_polling 模式共用）
"""

import logging
import os
import sys
from pathlib import Path
from datetime import datetime

import httpx

logger = logging.getLogger(__name__)


def normalize_agent_base_url(agent_url: str) -> str:
    """标准化 agent 基础地址：去掉末尾斜杠和 /a2a。"""
    normalized = agent_url.rstrip("/")
    if normalized.endswith("/a2a"):
        normalized = normalized[:-4]
    return normalized


def require_access_token(env_var: str = "FINTOOLS_ACCESS_TOKEN") -> str:
    """读取并校验访问 token，不存在则打印提示并退出。"""
    token = os.getenv(env_var)
    if token:
        return token
    print(f"❌ 错误: 未设置 {env_var} 环境变量")
    print("\n请在 .env 文件中设置:")
    print(f"  {env_var}=your-token-here")
    print("\n或通过命令行设置:")
    print(f"  export {env_var}=your-token-here")
    sys.exit(1)


class ReportDownloader:
    """报告下载器（通用，可被 streaming 和 db_polling 模式共用）"""

    def __init__(
        self,
        agent_url: str,
        a2a_token: str = None,
        timeout: float = 60.0,
        reports_zip_path: str = "api/reports/zip",
    ):
        """
        初始化报告下载器

        Args:
            agent_url: Agent Server 地址（如 http://localhost:9999）
            a2a_token: 认证 token
            timeout: HTTP 请求超时时间
            reports_zip_path: ZIP 下载路径（默认 api/reports/zip）
        """
        if not agent_url:
            raise ValueError("agent_url is required")

        self.agent_url = agent_url.rstrip("/")
        self.a2a_token = a2a_token or ""
        self.timeout = timeout

        # 构造报告下载 URL
        self.reports_zip_url = f"{self.agent_url}/{reports_zip_path}"

    def _auth_headers(self) -> dict:
        if not self.a2a_token:
            return {}
        return {"Authorization": f"Bearer {self.a2a_token}"}

    async def download_zip(self, output_dir: str | None = None) -> str | None:
        """
        打包下载所有报告为 ZIP 文件

        Args:
            output_dir: 输出目录（默认 relative path "downloaded_reports"）

        Returns:
            下载后的文件路径，失败返回 None
        """
        if output_dir is None:
            output_dir = "downloaded_reports"

        Path(output_dir).mkdir(parents=True, exist_ok=True)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            print(f"正在下载 ZIP 包...")
            print(f"  URL: {self.reports_zip_url}")

            try:
                response = await client.get(self.reports_zip_url, headers=self._auth_headers())
                
                # 处理特定的错误状态码
                if response.status_code == 410:
                    print(f"✗ Server has been shut down. Reports are no longer available.")
                    return None
                elif response.status_code == 404:
                    print(f"✗ No reports available yet. Task may still be running or reports have expired.")
                    return None
                
                response.raise_for_status()

                # 从响应头获取文件名
                content_disposition = response.headers.get("content-disposition", "")
                if "filename=" in content_disposition:
                    filename = content_disposition.split("filename=")[1].strip('"')
                else:
                    filename = f"reports_{datetime.now().strftime('%Y-%m-%d_%H%M%S')}.zip"

                output_path = Path(output_dir) / filename
                output_path.write_bytes(response.content)

                print(f"✓ 成功下载: {output_path}")
                print(f"  大小: {len(response.content) / 1024:.1f} KB")
                return str(output_path)
                
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 410:
                    print(f"✗ Server has been shut down. Reports are no longer available.")
                elif e.response.status_code == 404:
                    print(f"✗ No reports available yet. Task may still be running or reports have expired.")
                else:
                    logger.error(f"下载失败: {e}")
                    print(f"✗ 下载失败: {e}")
                return None
            except Exception as e:
                logger.error(f"下载失败: {e}")
                print(f"✗ 下载失败: {e}")
                return None

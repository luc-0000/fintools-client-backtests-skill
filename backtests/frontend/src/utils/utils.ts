// 添加时间戳防止缓存
export function buildUrlWithTs(baseUrl: string, params: Record<string, any> = {}): string {
  // 移除域名部分，只返回路径 + 查询参数
  const url = new URL(baseUrl, 'http://localhost')
  Object.keys(params).forEach((key) => {
    if (params[key] !== undefined && params[key] !== null) {
      url.searchParams.append(key, String(params[key]))
    }
  })
  url.searchParams.append('_t', String(Date.now()))
  return url.pathname + url.search
}

// 获取域名
export function getDomain(): string {
  return window.location.hostname
}

import axios from 'axios'
import type { AxiosError, AxiosRequestConfig, AxiosResponse } from 'axios'
import { message } from 'antd'

// 基础配置 - 使用相对路径，让 Vite proxy 处理
const baseURL = '/api'

const request = axios.create({
  baseURL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
request.interceptors.request.use(
  (config) => {
    // 可以在这里添加 token
    // const token = localStorage.getItem('token')
    // if (token) {
    //   config.headers.Authorization = `Bearer ${token}`
    // }

    // 添加时间戳防止缓存
    if (config.method === 'get') {
      config.params = {
        ...config.params,
        _t: Date.now(),
      }
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
request.interceptors.response.use(
  (response: AxiosResponse) => {
    const { data } = response

    // 根据实际后端响应结构调整
    // 成功的响应: code === 'SUCCESS' 或 code === 200 或 code === 0
    if (data.code !== undefined && data.code !== 'SUCCESS' && data.code !== 200 && data.code !== 0) {
      message.error(data.message || data.errMsg || '请求失败')
      return Promise.reject(new Error(data.message || data.errMsg || '请求失败'))
    }

    return data
  },
  (error: AxiosError) => {
    const { response } = error

    if (response) {
      switch (response.status) {
        case 401:
          message.error('未授权，请重新登录')
          // 可以在这里跳转到登录页
          break
        case 403:
          message.error('拒绝访问')
          break
        case 404:
          message.error('请求地址不存在')
          break
        case 500:
          message.error('服务器错误')
          break
        default:
          message.error((response.data as any)?.message || '请求失败')
      }
    } else {
      message.error('网络连接失败')
    }

    return Promise.reject(error)
  }
)

// 导出请求方法
export const get = <T = any>(url: string, config?: AxiosRequestConfig): Promise<T> => {
  return request.get(url, config) as Promise<T>
}

export const post = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.post(url, data, config) as Promise<T>
}

export const put = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  return request.put(url, data, config) as Promise<T>
}

export const del = <T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> => {
  const requestConfig: AxiosRequestConfig = { ...config }

  // DELETE 请求的数据通常放在请求体中或作为查询参数
  if (data) {
    // 如果 data 是对象且有属性，作为请求体传递
    if (typeof data === 'object' && Object.keys(data).length > 0) {
      requestConfig.data = data
    }
  }

  return request.delete(url, requestConfig) as Promise<T>
}

export default request

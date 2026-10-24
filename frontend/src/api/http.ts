/**
 * axios 实例 + 拦截器: 前端所有 HTTP 请求的"总闸门".
 *
 * 页面组件不要直接 import axios, 统一 import 这里的 http:
 *   - baseURL 统一为 /api(由 Vite 代理转发到后端 8000 端口)
 *   - 请求拦截器: 自动把 token 塞进请求头(不用每个接口手动写)
 *   - 响应拦截器: 自动剥掉一层 .data; 401 时清 token 踢回登录页
 */
import axios, { type AxiosRequestConfig } from "axios";

// 创建 axios 实例. axios 本身是"通用 HTTP 客户端", create 出来的实例才能自定义配置
const http = axios.create({
  baseURL: "/api",   // 所有请求自动加 /api 前缀: http.get("/tasks") → GET /api/tasks
  timeout: 30000,    // 超时 30 秒(毫秒), 防止请求永远挂着
});

// ============ 请求拦截器: 发出去之前统一加工 ============
http.interceptors.request.use((config) => {
  // 登录成功后 token 存在 localStorage(浏览器本地存储, 关浏览器也不丢)
  const token = localStorage.getItem("token");
  if (token) {
    // 按 JWT 标准格式设置请求头: Authorization: Bearer <token>
    // 后端的 get_current_user 依赖就靠这个头认人
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config; // 必须把配置返回, 请求才会继续
});

// ============ 响应拦截器: 拿到响应后统一加工 ============
http.interceptors.response.use(
  // 成功分支: resp.data 是后端返回的 JSON 体.
  // 直接返回 resp.data, 页面里就少写一层 .data(比如 progress.percent 而不是 resp.data.percent)
  (resp) => resp.data,

  // 失败分支: 统一处理"登录失效"
  (error) => {
    if (error.response?.status === 401) {
      // 401 = token 过期或无效 → 清掉本地凭证, 踢回登录页
      localStorage.removeItem("token");
      window.location.href = "/login";
    }
    // 其他错误(400/404/500...)原样抛出, 由页面自己决定怎么提示
    return Promise.reject(error);
  },
);

// 响应拦截器已经把"响应体"剥出来了, 但 axios 自带类型并不知道这件事,
// 还以为返回的是完整的 AxiosResponse —— 会和实际运行时不符, 类型检查报错.
// 所以这里把实例重新声明成: get/post 的返回值直接就是 Promise<T>(即后端 JSON).
interface HttpClient {
  get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
  post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T>;
  delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T>;
}

export default http as unknown as HttpClient;

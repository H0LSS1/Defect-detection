/**
 * 认证相关接口: 注册 / 登录 / 查询当前用户.
 * 对应后端 app/api/auth.py 的三个接口.
 */
import http from "./http";
import type { Token, UserCreate, UserOut, UserUpdate } from "./types";

/** 注册新用户: POST /api/auth/register, 成功返回用户信息(不含密码) */
export function register(data: UserCreate) {
  return http.post<UserOut>("/auth/register", data);
}

/** 登录: POST /api/auth/login, 成功返回 { access_token, token_type } */
export function login(data: { username: string; password: string }) {
  return http.post<Token>("/auth/login", data);
}

/** 查询当前登录用户: GET /api/auth/me(需要 token, 拦截器自动带上) */
export function fetchMe() {
  return http.get<UserOut>("/auth/me");
}

/** 用户列表: GET /api/auth/users(仅 admin, 非 admin 返回 403) */
export function listUsers() {
  return http.get<UserOut[]>("/auth/users");
}

/** 修改用户: PUT /api/auth/users/{id}(仅 admin; 只传要改的字段) */
export function updateUser(id: number, data: UserUpdate) {
  return http.put<UserOut>(`/auth/users/${id}`, data);
}

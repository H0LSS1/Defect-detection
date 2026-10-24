/**
 * 用户仓库(Pinia): 全局唯一的"登录状态"存放点.
 *
 * 为什么需要全局仓库:
 *   token 在 localStorage, 但"当前用户是谁"很多页面都要用
 *   (工作台显示姓名、菜单按角色显示), 放在仓库里一次拉取处处可用.
 *
 * defineStore 三要素:
 *   state     : 数据(相当于组件的 data)
 *   getters   : 计算属性(相当于 computed)
 *   actions   : 方法(登录/登出/拉取用户信息)
 */
import { ref, computed } from "vue";
import { defineStore } from "pinia";
import { fetchMe, login as loginApi, register as registerApi } from "../api/auth";
import type { UserCreate, UserOut } from "../api/types";

export const useUserStore = defineStore("user", () => {
  // ===== state =====
  const token = ref<string>(localStorage.getItem("token") ?? ""); // 刷新页面后从本地存储恢复
  const userInfo = ref<UserOut | null>(null); // null = 还没拉取过用户信息

  // ===== getters(计算属性) =====
  const isLoggedIn = computed(() => token.value !== "");
  const isAdmin = computed(() => userInfo.value?.role === "admin");

  // ===== actions =====

  /** 登录: 调接口拿 token → 存仓库 + 存 localStorage(刷新不丢) */
  async function login(username: string, password: string) {
    const data = await loginApi({ username, password });
    token.value = data.access_token;
    localStorage.setItem("token", data.access_token);
  }

  /** 注册: 直接透传表单给后端 */
  async function register(data: UserCreate) {
    return registerApi(data);
  }

  /** 拉取当前用户信息(登录后调一次; 失败说明 token 无效, 会被 http.ts 拦截器踢回登录页) */
  async function fetchUserInfo() {
    userInfo.value = await fetchMe();
  }

  /** 登出: 清空仓库 + 本地存储 */
  function logout() {
    token.value = "";
    userInfo.value = null;
    localStorage.removeItem("token");
  }

  return { token, userInfo, isLoggedIn, isAdmin, login, register, fetchUserInfo, logout };
});

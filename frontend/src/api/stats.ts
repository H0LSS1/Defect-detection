/**
 * 统计接口: 看板数据(GET /api/stats/overview).
 * 对应后端 app/api/stats.py. 支持按任务/类别筛选(可选参数).
 */
import http from "./http";
import type { StatsOverview } from "./types";

/** 筛选参数: 都可省略 */
export interface OverviewParams {
  task_no?: string;    // 按任务号过滤
  class_name?: string; // 按类别过滤
}

/** 看板总览: 总量指标 + 类别分布(饼图) + 近14天趋势(折线图) */
export function getOverview(params: OverviewParams = {}) {
  // axios 的 params 选项会自动把对象拼成查询串: ?task_no=...&class_name=...
  return http.get<StatsOverview>("/stats/overview", { params });
}

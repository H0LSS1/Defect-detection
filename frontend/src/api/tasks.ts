/**
 * 任务相关接口: 创建 / 列表 / 详情 / 进度 / 报告下载.
 * 对应后端 app/api/tasks.py 的五个接口.
 */
import http from "./http";
import type { TaskDetailOut, TaskOut, TaskProgressOut } from "./types";

/** 任务列表(GET /api/tasks): admin 返回全部, 普通用户只返回自己的 */
export function listTasks() {
  return http.get<TaskOut[]>("/tasks");
}

/** 创建检测任务(POST /api/tasks, multipart 表单上传).
 *
 * @param taskName 任务名
 * @param files    用户选中的图片文件列表(File 对象来自 <input type="file">)
 * @param conf     置信度阈值, 默认 0.25
 *
 * 关键点: 上传文件必须用 FormData(浏览器会自动编码成 multipart 格式),
 * 且字段名必须叫 task_name/conf/files —— 和后端 Form/File 参数名一一对应.
 */
export function createTask(taskName: string, files: File[], conf = 0.25) {
  const form = new FormData();
  form.append("task_name", taskName);
  form.append("conf", String(conf)); // FormData 只收字符串, 数字要手动转
  files.forEach((f) => form.append("files", f));
  return http.post<TaskOut>("/tasks", form);
}

/** 任务进度(GET /api/tasks/{task_no}/progress): 轮询用它 */
export function getProgress(taskNo: string) {
  return http.get<TaskProgressOut>(`/tasks/${taskNo}/progress`);
}

/** 任务详情(GET /api/tasks/{task_no}): 含图片列表与三种图路径 */
export function getTaskDetail(taskNo: string) {
  return http.get<TaskDetailOut>(`/tasks/${taskNo}`);
}

/** 下载检测报告(GET /api/tasks/{task_no}/report).
 *
 * responseType: "blob" 让 axios 把文件当二进制流接收(而不是当 JSON 解析),
 * 配合 URL.createObjectURL 触发浏览器下载(见视图层的 downloadReport).
 */
export function downloadReport(taskNo: string) {
  return http.get<Blob>(`/tasks/${taskNo}/report`, { responseType: "blob" });
}

export type UserRole = "inspector" | "admin";
export type TaskStatus = "pending" | "running" | "completed" | "failed";
export type ImageStatus = "uploaded" | "enhancing" | "detecting" | "done" | "failed";

export interface UserCreate {
  username: string;
  password: string;
  real_name?: string | null;
  email?: string | null;
}
export interface Token {
  access_token: string;
  token_type: string;
}
export interface UserOut {
  id: number;
  username: string;
  real_name: string | null;
  role: UserRole;
  status: boolean;
  created_at: string;
  last_login: string | null; // 用户管理列表展示用
}

/** 管理员修改用户的请求体(只传要改的字段) */
export interface UserUpdate {
  status?: boolean;
  role?: UserRole;
}

export interface TaskOut {
  id: number;
  task_no: string;
  task_name: string;
  status: TaskStatus;
  username: string | null; // 创建人用户名(admin 的"检测人"列)
  total_images: number;
  completed_images: number;
  confidence_threshold: number;
  error_message: string | null;
  created_at: string;
}

export interface ImageOut {
  id: number;
  filename: string;
  status: ImageStatus;
  original_path: string;
  enhanced_path: string | null;
  annotated_path: string | null;
  file_size: number;
  inference_time_ms: number | null;
}

export interface TaskProgressOut {
  task_no: string;
  status: TaskStatus;
  completed: number;
  total: number;
  percent: number;
}

export interface TaskDetailOut extends Omit<TaskOut, never> {
  started_at: string | null;
  finished_at: string | null;
  images: ImageOut[];
}

export interface ClassDistributionItem {
  class_name: string;
  display_name: string;
  color: string | null;
  count: number;
}
export interface TrendItem {
  date: string;
  tasks: number;
  images: number;
}
export interface StatsOverview {
  total_tasks: number;
  total_images: number;
  done_images: number;
  total_detections: number;
  avg_inference_ms: number | null;
  class_distribution: ClassDistributionItem[];
  trend: TrendItem[];
}

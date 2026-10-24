<!-- 任务详情: 任务元信息 + 逐图三图对比(原图/增强图/标注图) + 报告下载. -->
<script setup lang="ts">
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { ElMessage } from "element-plus";
import { downloadReport, getTaskDetail } from "../api/tasks";
import type { ImageOut, TaskDetailOut } from "../api/types";

const route = useRoute();
const taskNo = route.params.taskNo as string; // 从 URL 取任务号(见路由 :taskNo)

const task = ref<TaskDetailOut | null>(null);
const current = ref<ImageOut | null>(null); // 当前选中查看的图片
const loading = ref(false);
const exporting = ref(false);

const statusText: Record<string, string> = {
  pending: "排队中", running: "检测中", completed: "已完成", failed: "失败",
};

async function load() {
  loading.value = true;
  try {
    task.value = await getTaskDetail(taskNo);
    current.value = task.value.images[0] ?? null; // 默认选中第一张
  } finally {
    loading.value = false;
  }
}

/** 拼静态图片直链: 数据库存的是相对路径, main.py 挂载在 /media 下 */
function mediaUrl(path: string | null): string | undefined {
  return path ? `/media/${path}` : undefined;
}

/** 下载报告: 拿到二进制 → 生成临时 URL → 模拟 <a download> 点击 */
async function exportReport() {
  exporting.value = true;
  try {
    const blob = await downloadReport(taskNo);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${taskNo}.docx`;
    a.click();
    URL.revokeObjectURL(url); // 用完释放内存
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail ?? "导出失败");
  } finally {
    exporting.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div v-loading="loading">
    <el-card v-if="task" class="mb">
      <template #header>
        <div class="card-header">
          <span>{{ task.task_name }} ({{ task.task_no }})</span>
          <el-button type="primary" :loading="exporting" @click="exportReport">
            导出检测报告(docx)
          </el-button>
        </div>
      </template>
      <el-descriptions :column="4" border>
        <el-descriptions-item label="状态">{{ statusText[task.status] }}</el-descriptions-item>
        <el-descriptions-item label="进度">{{ task.completed_images }} / {{ task.total_images }}</el-descriptions-item>
        <el-descriptions-item label="置信度阈值">{{ task.confidence_threshold }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ task.created_at }}</el-descriptions-item>
      </el-descriptions>
      <el-alert v-if="task.error_message" type="error" :title="task.error_message" class="mb" />
    </el-card>

    <el-row :gutter="16">
      <!-- 左: 图片列表 -->
      <el-col :span="6">
        <el-card header="图片列表">
          <el-menu :default-active="current?.id.toString()">
            <el-menu-item
              v-for="img in task?.images"
              :key="img.id"
              :index="img.id.toString()"
              @click="current = img"
            >
              {{ img.filename }}
              <el-tag v-if="img.status === 'done'" type="success" size="small">done</el-tag>
              <el-tag v-else-if="img.status === 'failed'" type="danger" size="small">failed</el-tag>
            </el-menu-item>
          </el-menu>
        </el-card>
      </el-col>

      <!-- 右: 三图对比 + 检测信息 -->
      <el-col :span="18">
        <el-card v-if="current">
          <template #header>图像处理对比 — {{ current.filename }}</template>
          <el-row :gutter="12">
            <el-col :span="8" v-for="item in [
                { label: '原图', path: current.original_path },
                { label: '增强图', path: current.enhanced_path },
                { label: '标注图', path: current.annotated_path },
              ]" :key="item.label">
              <div class="img-box">
                <div class="img-label">{{ item.label }}</div>
                <el-image
                  v-if="mediaUrl(item.path)"
                  :src="mediaUrl(item.path)"
                  :preview-src-list="[mediaUrl(item.path)!]"
                  fit="contain"
                  class="img"
                >
                  <!-- 加载失败(如增强图还没生成)时的占位 -->
                  <template #error><div class="img-error">暂无</div></template>
                </el-image>
                <div v-else class="img-error">暂无</div>
              </div>
            </el-col>
          </el-row>
          <p v-if="current.inference_time_ms" class="hint">
            推理耗时: {{ current.inference_time_ms }} ms
          </p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.mb { margin-bottom: 16px; }
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.img-box { text-align: center; }
.img-label { font-weight: bold; margin-bottom: 6px; }
.img { width: 100%; height: 340px; background: #fafafa; }
.img-error {
  height: 340px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #bbb;
  background: #fafafa;
}
.hint { color: #999; font-size: 12px; }
</style>

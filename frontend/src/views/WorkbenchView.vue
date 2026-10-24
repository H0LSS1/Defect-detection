<!-- 检测工作台: 选图 → 填任务名 → 提交 → 轮询进度条 → 完成跳详情. -->
<script setup lang="ts">
import { computed, onUnmounted, ref, reactive } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { createTask, getProgress } from "../api/tasks";
import type { TaskProgressOut } from "../api/types";

const router = useRouter();

// ===== 表单状态 =====
const taskName = ref(""); // 任务名
const conf = ref(0.25); // 置信度阈值(滑块绑定)
const fileList = ref<any[]>([]); // el-upload 的文件列表(v-model:file-list 自动收集, 无需手动维护)
const submitting = ref(false); // 提交按钮转圈

// ===== 轮询状态 =====
const polling = ref(false); // 是否正在轮询
const progress = reactive<TaskProgressOut>({
  task_no: "",
  status: "running",
  completed: 0,
  total: 0,
  percent: 0,
});
let timer: number | undefined; // setInterval 的句柄, 卸载页面时必须清掉

// 提交前从 el-upload 的文件列表里取出真正的 File 对象(raw 就是原始文件)
function getFileList(): File[] {
  return fileList.value.map((f) => f.raw as File);
}

async function submit() {
  // 前端先做一层校验, 减少无效请求
  if (!taskName.value.trim()) {
    ElMessage.warning("请填写任务名称");
    return;
  }
  const files = getFileList();
  if (files.length === 0) {
    ElMessage.warning("请选择至少一张图片");
    return;
  }

  submitting.value = true;
  try {
    const task = await createTask(taskName.value, files, conf.value);
    ElMessage.success(`任务创建成功: ${task.task_no}`);
    startPolling(task.task_no); // 创建成功后立刻开始轮询进度
    resetForm();                // 清空表单, 方便连续创建下一个任务
  } catch (e: any) {
    ElMessage.error(e.response?.data?.detail ?? "创建失败");
  } finally {
    submitting.value = false;
  }
}

/** 提交成功后重置表单 */
function resetForm() {
  taskName.value = "";
  fileList.value = [];
}

/** 开启轮询: 每 1 秒查一次进度, 终态时停止 */
function startPolling(taskNo: string) {
  polling.value = true;
  pollingTaskNo.value = taskNo;
  timer = window.setInterval(async () => {
    try {
      const p = await getProgress(taskNo);
      Object.assign(progress, p); // 把返回的进度逐字段拷进响应式对象
      if (p.status === "completed" || p.status === "failed") {
        stopPolling();
        if (p.status === "completed") {
          // 完成 → 自动跳到详情页看标注图(省去手动去任务管理里翻)
          ElMessage.success("检测完成, 正在跳转结果页...");
          setTimeout(() => router.push(`/tasks/${taskNo}`), 800);
        } else {
          ElMessage.error("检测失败, 详情页可查看原因");
        }
      }
    } catch {
      stopPolling(); // 轮询出错(如网络断开)也要停止, 防止无限请求
    }
  }, 1000);
}

const pollingTaskNo = ref("");

function stopPolling() {
  polling.value = false;
  if (timer) {
    clearInterval(timer);
    timer = undefined;
  }
}

// 组件卸载(跳走/关页面)时清掉定时器, 否则定时器还活着会继续请求
onUnmounted(stopPolling);

// 步骤条走到哪一步: 0=填表 1=检测中 2=完成(驱动顶部 el-steps)
const flowStep = computed(() => {
  if (polling.value && progress.status === "completed") return 2;
  if (polling.value) return 1;
  return 0;
});
</script>

<template>
  <div>
    <!-- 步骤条: 告诉用户整个流程走到哪一步了 -->
    <el-card class="mb">
      <el-steps :active="flowStep" align-center finish-status="success">
        <el-step title="上传图片" description="选择焊缝图片并填写任务名" />
        <el-step title="自动检测" description="后台增强 + YOLO 推理" />
        <el-step title="查看结果" description="标注图与统计报告" />
      </el-steps>
    </el-card>

    <el-row :gutter="16">
    <!-- 左列: 创建任务表单 -->
    <el-col :span="14">
      <el-card header="创建检测任务">
        <el-form label-width="100px">
          <el-form-item label="任务名称">
            <el-input v-model="taskName" placeholder="例如: 3号线焊缝抽检" />
          </el-form-item>
          <el-form-item label="置信度阈值">
            <el-slider v-model="conf" :min="0.05" :max="0.95" :step="0.05" show-input />
            <div class="hint">低于此置信度的检测框会被丢弃; 越高误检越少, 漏检越多</div>
          </el-form-item>
          <el-form-item label="选择图片">
            <!-- auto-upload=false: 不让组件自己传, 由我们的 createTask 统一传.
                 文件列表完全交给 v-model:file-list 维护, 不要再绑 on-change
                 (on-change 第一个参数是单个文件对象, 曾被误当数组赋值导致整页冻结) -->
            <el-upload
              v-model:file-list="fileList"
              drag
              multiple
              accept=".jpg,.jpeg,.png,.bmp"
              :auto-upload="false"
            >
              <el-icon size="40"><UploadFilled /></el-icon>
              <div>拖拽图片到此处, 或点击选择(支持多选)</div>
              <template #tip>
                <div class="hint">支持 jpg / jpeg / png / bmp</div>
              </template>
            </el-upload>
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="submitting" @click="submit">
              创建检测任务
            </el-button>
          </el-form-item>
        </el-form>
      </el-card>
    </el-col>

    <!-- 右列: 进度卡片(有任务在跑时显示) -->
    <el-col :span="10">
      <el-card v-if="polling" header="检测进度">
        <p>任务号: {{ progress.task_no }}</p>
        <el-progress
          type="dashboard"
          :percentage="progress.percent"
          :status="progress.status === 'completed' ? 'success' : undefined"
        />
        <p class="hint">
          {{ progress.completed }} / {{ progress.total }} 张 ({{
            progress.status === "completed" ? "已完成" : "处理中..."
          }})
        </p>
        <el-button
          v-if="progress.status === 'completed'"
          type="primary"
          @click="router.push(`/tasks/${pollingTaskNo}`)"
        >
          查看检测结果
        </el-button>
      </el-card>
      <el-card v-else header="使用说明">
        <ol class="hint">
          <li>填写任务名称, 选择一张或多张焊缝图片</li>
          <li>点击"创建检测任务", 后台会自动完成增强与检测</li>
          <li>右侧实时显示进度, 完成后点击查看结果</li>
          <li>也可以在"任务管理"里查看历史任务</li>
        </ol>
      </el-card>
    </el-col>
  </el-row>
  </div>
</template>

<style scoped>
.hint {
  color: #999;
  font-size: 12px;
}
/* 加大拖拽上传区的视觉面积 */
:deep(.el-upload-dragger) {
  height: 180px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
</style>

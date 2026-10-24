<!-- 登录/注册页: 一个页面两个 Tab, 注册成功自动切回登录. -->
<script setup lang="ts">
import { reactive, ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage, type FormInstance, type FormRules } from "element-plus";
import { useUserStore } from "../stores/user";

const router = useRouter();
const userStore = useUserStore();

const activeTab = ref<"login" | "register">("login"); // 当前 Tab
const formRef = ref<FormInstance>(); // 表单实例: 用于触发校验
const loading = ref(false);          // 按钮转圈状态, 防止重复提交

// reactive: 把对象变成响应式(表单数据绑定用)
const form = reactive({
  username: "",
  password: "",
  password2: "",   // 仅注册时用于二次确认
  real_name: "",
});

// 校验规则: trigger "blur" = 输入框失焦时校验
const rules: FormRules = {
  username: [
    { required: true, message: "请输入用户名", trigger: "blur" },
    { min: 3, max: 50, message: "长度 3~50 个字符", trigger: "blur" }, // 对齐后端 UserCreate
  ],
  password: [
    { required: true, message: "请输入密码", trigger: "blur" },
    { min: 6, max: 72, message: "长度 6~72 个字符", trigger: "blur" },
  ],
};

async function submit() {
  // validate() 校验不通过会抛异常, 后面的代码自然不执行
  await formRef.value?.validate();
  loading.value = true;
  try {
    if (activeTab.value === "login") {
      // ===== 登录 =====
      await userStore.login(form.username, form.password);
      ElMessage.success("登录成功");
      router.push("/"); // 跳工作台(路由守卫此时已放行)
    } else {
      // ===== 注册 =====
      if (form.password !== form.password2) {
        ElMessage.error("两次输入的密码不一致");
        return;
      }
      await userStore.register({
        username: form.username,
        password: form.password,
        real_name: form.real_name || null,
      });
      ElMessage.success("注册成功, 请登录");
      activeTab.value = "login";
    }
  } catch (e: any) {
    // 后端错误响应格式: { detail: "用户已存在" } —— 把它显示出来
    ElMessage.error(e.response?.data?.detail ?? "操作失败");
  } finally {
    loading.value = false; // 无论成败都停止转圈
  }
}
</script>

<template>
  <div class="page">
    <el-card class="card">
      <h2 class="title">焊缝缺陷智能检测平台</h2>
      <el-tabs v-model="activeTab">
        <el-tab-pane label="登录" name="login">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="0" @submit.prevent>
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名" size="large">
                <template #prefix><el-icon><User /></el-icon></template>
              </el-input>
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码" size="large" show-password />
            </el-form-item>
            <el-button type="primary" size="large" class="btn" :loading="loading" @click="submit">
              登 录
            </el-button>
          </el-form>
        </el-tab-pane>

        <el-tab-pane label="注册" name="register">
          <el-form ref="formRef" :model="form" :rules="rules" label-width="0">
            <el-form-item prop="username">
              <el-input v-model="form.username" placeholder="用户名(3~50字符)" size="large" />
            </el-form-item>
            <el-form-item prop="password">
              <el-input v-model="form.password" type="password" placeholder="密码(6~72字符)" size="large" show-password />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.password2" type="password" placeholder="确认密码" size="large" show-password />
            </el-form-item>
            <el-form-item>
              <el-input v-model="form.real_name" placeholder="姓名(选填)" size="large" />
            </el-form-item>
            <el-button type="primary" size="large" class="btn" :loading="loading" @click="submit">
              注 册
            </el-button>
          </el-form>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>
</template>

<style scoped>
.page {
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(135deg, #1677ff22, #00152933);
}
.card {
  width: 400px;
  padding: 10px 20px;
}
.title {
  text-align: center;
  margin: 10px 0 20px;
}
.btn {
  width: 100%;
}
</style>

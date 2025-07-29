<template>
  <!-- 连接服务器对话框 -->
  <div v-if="visible && !showFileBrowser" class="dialog-overlay" @click="closeDialog">
    <div class="dialog" @click.stop>
      <div class="dialog-header">
        <h3>连接到服务器</h3>
        <button @click="closeDialog" class="close-btn">×</button>
      </div>

      <div class="dialog-body">
        <div class="form-group">
          <label>协议:</label>
          <select v-model="connectionForm.protocol">
            <option value="sftp">SFTP</option>
            <option value="ftp">FTP</option>
          </select>
        </div>

        <div class="form-group">
          <label>主机:</label>
          <input
            v-model="connectionForm.host"
            type="text"
            placeholder="服务器地址"
            @keyup.enter="connect"
          >
        </div>

        <div class="form-group">
          <label>端口:</label>
          <input
            v-model.number="connectionForm.port"
            type="number"
            placeholder="22"
            @keyup.enter="connect"
          >
        </div>

        <div class="form-group">
          <label>用户名:</label>
          <input
            v-model="connectionForm.username"
            type="text"
            placeholder="用户名"
            @keyup.enter="connect"
          >
        </div>

        <div class="form-group">
          <label>密码:</label>
          <input
            v-model="connectionForm.password"
            type="password"
            placeholder="密码"
            @keyup.enter="connect"
          >
        </div>

        <div v-if="connectionError" class="error-message">
          {{ connectionError }}
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="closeDialog" class="cancel-btn">取消</button>
        <button @click="connect" :disabled="connecting" class="connect-btn">
          {{ connecting ? '连接中...' : '连接' }}
        </button>
      </div>
    </div>
  </div>

  <!-- 文件夹选择弹窗 -->
  <div v-if="showFileBrowser" class="dialog-overlay">
    <ServerFileBrowser
      :key="'folder-browser-' + (tempConnection?.host || 'default')"
      :visible="showFileBrowser"
      :connection="tempConnection"
      mode="select-folder"
      @folder-selected="onFolderSelected"
      @processing-complete="onProcessingComplete"
      @close="onServerFileBrowserClose"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, watch, onMounted, onUnmounted } from 'vue';
import ServerFileBrowser from './ServerFileBrowser.vue';

interface ServerConnection {
  protocol: 'sftp' | 'ftp';
  host: string;
  port: number;
  username: string;
  password: string;
  remotePath: string;
}

interface Props {
  visible: boolean;
}

interface Emits {
  (e: 'close'): void;
  (e: 'connect', connection: ServerConnection): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

const connecting = ref(false);
const connectionError = ref('');
const showFileBrowser = ref(false);
let tempConnection = null as ServerConnection | null;

const connectionForm = reactive<ServerConnection>({
  protocol: 'sftp',
  host: 'sesklsasgrnprd06.emea.astrazeneca.net',
  port: 22,
  username: 'ktxv525',
  password: '',
  remotePath: '/SASDATA2/SafetyNet/root/cdar/'
});

// 监听协议变化，自���调整默认端口
watch(() => connectionForm.protocol, (newProtocol) => {
  if (newProtocol === 'sftp') {
    connectionForm.port = 22;
  } else if (newProtocol === 'ftp') {
    connectionForm.port = 21;
  }
});

const connect = async () => {
  if (!connectionForm.host || !connectionForm.username) {
    connectionError.value = '请填写主机地址和用户名';
    return;
  }
  connecting.value = true;
  connectionError.value = '';
  try {
    // 模拟连接验证
    await new Promise(resolve => setTimeout(resolve, 1000));
    // 连接成功后弹出文件夹选择窗口
    tempConnection = { ...connectionForm };
    showFileBrowser.value = true;
  } catch (error) {
    connectionError.value = '连接失败: ' + (error as Error).message;
  } finally {
    connecting.value = false;
  }
};

const onFolderSelected = (folderPath: string) => {
  console.log('=== onFolderSelected called ===');
  console.log('folderPath:', folderPath);
  console.log('调用堆栈:', new Error().stack);

  // 只保存路径，不立即关闭对话框
  connectionForm.remotePath = folderPath;
  // 不再立即关闭文件��览器，等待processing-complete事件
};

// 新增：处理进度完成事件
const onProcessingComplete = (folderPath: string) => {
  console.log('=== onProcessingComplete called ===');
  console.log('folderPath:', folderPath);

  // 只发送连接信息，不关闭文件浏览器，保持用户停留在当前文件夹
  emit('connect', { ...connectionForm });
  // 不再关闭文件浏览器和重置连接状态
  // showFileBrowser.value = false;
  // tempConnection = null;
};

const closeDialog = () => {
  emit('close');
};

// 重置表单
const resetForm = () => {
  connectionForm.host = 'sesklsasgrnprd06.emea.astrazeneca.net';
  connectionForm.username = 'ktxv525';
  connectionForm.password = ' ';
  // 删除 remotePath 重置，保留用户最后选择的文件夹
  // connectionForm.remotePath = '/SASDATA2/SafetyNet/root/cdar/';
  connectionError.value = '';
};

// 监听弹窗显示状态，只重置连接信息，保留文件夹路径
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    resetForm();
  }
});

// 添加一��监控 showFileBrowser 状态变化的 watcher
watch(() => showFileBrowser.value, (newValue, oldValue) => {
  console.log('=== showFileBrowser 状态变化 ===');
  console.log('从', oldValue, '变为', newValue);
  console.log('调用堆栈:', new Error().stack);
});

// 调试用：处理 ServerFileBrowser 关闭事件
const onServerFileBrowserClose = () => {
  console.log('=== ServerFileBrowser 关闭��件触发 ===');
  console.log('调用堆栈:', new Error().stack);
  showFileBrowser.value = false;
};

// 关闭文件夹浏览器（点击背景时）
const closeFolderBrowser = () => {
  // 点击文件夹选择窗口的背景时，返回到连接对话框
  showFileBrowser.value = false;
};
</script>

<style scoped>
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
  backdrop-filter: blur(4px);
}

.dialog {
  background: white;
  border-radius: 16px;
  min-width: 450px;
  max-width: 90vw;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 24px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.dialog-header h3 {
  margin: 0;
  color: #1f2937;
  font-size: 1.25rem;
  font-weight: 600;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  color: #6b7280;
  cursor: pointer;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.close-btn:hover {
  background: #f3f4f6;
  color: #374151;
}

.dialog-body {
  padding: 24px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.form-group input,
.form-group select {
  width: 100%;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  font-size: 14px;
  transition: border-color 0.2s ease;
  background: white;
}

.form-group input:focus,
.form-group select:focus {
  outline: none;
  border-color: #4f46e5;
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.hint {
  display: block;
  margin-top: 6px;
  color: #6b7280;
  font-size: 12px;
}

.error-message {
  color: #dc2626;
  background: #fee2e2;
  padding: 12px;
  border-radius: 8px;
  font-size: 14px;
  margin-top: 16px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 16px 24px 24px;
  border-top: 1px solid #e5e7eb;
}

.cancel-btn {
  padding: 10px 20px;
  border: 1px solid #d1d5db;
  background: white;
  color: #374151;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.cancel-btn:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}

.connect-btn {
  padding: 10px 20px;
  background: #4f46e5;
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
}

.connect-btn:hover:not(:disabled) {
  background: #3730a3;
}

.connect-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}
</style>

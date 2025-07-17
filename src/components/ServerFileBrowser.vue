<template>
  <div class="server-file-browser">
    <!-- 连接面板（仅非 select-folder 模式下显示） -->
    <div v-if="!isConnected && mode !== 'select-folder'" class="connection-panel">
      <!-- 连接中提示遮罩 -->
      <div v-if="connecting" class="connecting-overlay">
        <div class="connecting-indicator">
          <div class="connecting-spinner"></div>
          <div class="connecting-text">正在连接服务器...</div>
        </div>
      </div>

      <div class="connection-form">
        <h3>连接到服务器</h3>
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
        <div class="form-actions">
          <button @click="connect" :disabled="connecting" class="connect-btn">
            {{ connecting ? '连接中...' : '连接' }}
          </button>
        </div>
        <div v-if="connectionError" class="error-message">
          {{ connectionError }}
        </div>
      </div>
    </div>

    <!-- 文件浏览器 -->
    <div v-else class="file-browser">
      <!-- 连接中提示遮罩（在文件浏览器中显示） -->
      <div v-if="connecting" class="connecting-overlay">
        <div class="connecting-indicator">
          <div class="connecting-spinner"></div>
          <div class="connecting-text">正在连接服务器...</div>
        </div>
      </div>

      <!-- 路径显示区域 -->
      <div class="path-display">
        <div class="path-label">当前路径:</div>
        <div class="path-breadcrumb">
          <span class="path-segment root" @click="navigateToPath('/')">/</span>
          <span
            v-for="(segment, index) in pathSegments"
            :key="index"
            class="path-segment"
            @click.stop="navigateToPath(getPathUpTo(index))"
          >
            {{ segment }}
            <span v-if="index < pathSegments.length - 1" class="path-separator">/</span>
          </span>
        </div>
      </div>

      <!-- 文件列表 -->
      <div class="file-list">
        <div class="file-list-header">
          <div class="file-name">文件名</div>
          <div class="file-size">大小</div>
          <div class="file-modified">修改时间</div>
        </div>

        <div class="file-list-body">
          <!-- 加载提示 -->
          <div v-if="loading" class="loading-indicator">
            <div class="loading-spinner"></div>
            <div class="loading-text">正在加载文件...</div>
          </div>

          <!-- 当没有加载中且文件列表为空时显示 -->
          <div v-else-if="!loading && files.length === 0" class="empty-folder">
            此文件夹为空
          </div>

          <!-- 返回上级目录 -->
          <div v-else>
            <div v-if="currentPath !== '/'" class="file-item" @click="highlightItem('..')" @dblclick="navigateUp">
              <div class="file-name">
                <span class="file-icon">📁</span>
                <span class="file-text">..</span>
              </div>
              <div class="file-size">-</div>
              <div class="file-modified">-</div>
            </div>

            <!-- 文件列表 -->
            <div
              v-for="file in files"
              :key="file.path"
              class="file-item"
              :class="{ 'selected': selectedFiles.includes(file.path), 'highlighted': highlightedItem === file.path }"
              @click="handleFileClick(file, $event)"
              @dblclick="handleFileDoubleClick(file)"
            >
              <div class="file-name">
                <span class="file-icon">{{ getFileIcon(file) }}</span>
                <span class="file-text">{{ file.name }}</span>
              </div>
              <div class="file-size">{{ formatFileSize(file.size) }}</div>
              <div class="file-modified">{{ formatDate(file.lastModified) }}</div>
            </div>
          </div>
        </div>
      </div>

      <!-- 底部操作栏 -->
      <div class="bottom-toolbar">
        <div class="toolbar-actions">
          <button @click="closeDialog" class="close-btn">
            关闭
          </button>
          <button v-if="props.mode === 'select-folder'" @click="confirmFolderSelection" class="confirm-btn">
            选择此文件夹
          </button>
          <button v-else @click="createFolder" class="create-btn">
            新建文件夹
          </button>
        </div>
      </div>

      <!-- 创建文件夹对话框 -->
      <div v-if="showCreateFolderDialog" class="dialog-overlay" @click="closeCreateFolderDialog">
        <div class="dialog" @click.stop>
          <h3>创建新文件夹</h3>
          <input
            v-model="newFolderName"
            type="text"
            placeholder="文件夹名称"
            @keyup.enter="confirmCreateFolder"
            ref="folderNameInput"
          >
          <div class="dialog-actions">
            <button @click="confirmCreateFolder" class="confirm-btn">创建</button>
            <button @click="closeCreateFolderDialog" class="cancel-btn">取消</button>
          </div>
        </div>
      </div>

      <!-- 选择上传目标对话框 -->
      <div v-if="showUploadTargetDialog" class="dialog-overlay" @click="closeUploadTargetDialog">
        <div class="folder-dialog" @click.stop>
          <div class="folder-dialog-header">
            <h3>选择上传目标文件夹</h3>
            <button @click="closeUploadTargetDialog" class="close-btn">×</button>
          </div>
          <div class="folder-dialog-body">
            <div class="folder-path-display">
              <span class="path-label">当前路径:</span>
              <span class="current-path">{{ folderBrowsePath }}</span>
            </div>
            <div class="folder-navigation">
              <!-- 返回上级目录 -->
              <div v-if="folderBrowsePath !== '/home/sasuser'" class="folder-nav-item" @click="navigateToParentFolder">
                <span class="folder-icon">📁</span>
                <span class="folder-name">返回上级目录</span>
              </div>
              <!-- 当前目录选择 -->
              <div class="folder-nav-item current-folder" @click="selectCurrentFolder">
                <span class="folder-icon">📂</span>
                <span class="folder-name">选择当前目录</span>
              </div>
              <!-- 子文件夹列表 -->
              <div
                v-for="folder in availableFolders"
                :key="folder.path"
                class="folder-nav-item"
                @click="navigateToFolder(folder.path)"
              >
                <span class="folder-icon">📁</span>
                <span class="folder-name">{{ folder.name }}</span>
              </div>
            </div>
            <div v-if="folderLoading" class="folder-loading">
              正在加载文件夹...
            </div>
          </div>
          <div class="folder-dialog-footer">
            <button @click="confirmFolderSelection" class="confirm-btn" :disabled="!selectedFolderPath">
              确定选择
            </button>
            <button @click="closeUploadTargetDialog" class="cancel-btn">取消</button>
          </div>
        </div>
      </div>

      <!-- 文件夹处理进度对话框 -->
      <div v-if="processingFolderSelection" class="dialog-overlay">
        <div class="processing-dialog" @click.stop>
          <div class="processing-content">
            <div class="processing-icon">
              <div v-if="!processingComplete" class="processing-spinner"></div>
              <div v-else class="processing-complete-icon">✅</div>
            </div>
            <div class="processing-message">{{ processingMessage }}</div>
            <div class="processing-progress-container">
              <div class="processing-progress-bar" :style="{ width: processingProgress + '%' }"></div>
            </div>
            <div class="processing-progress-text">{{ processingProgress }}%</div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建文件夹对话框 -->
    <div v-if="showCreateFolderDialog" class="dialog-overlay" @click="closeCreateFolderDialog">
      <div class="dialog" @click.stop>
        <h3>创建新文件夹</h3>
        <input
          v-model="newFolderName"
          type="text"
          placeholder="文件夹名称"
          @keyup.enter="confirmCreateFolder"
          ref="folderNameInput"
        >
        <div class="dialog-actions">
          <button @click="confirmCreateFolder" class="confirm-btn">创建</button>
          <button @click="closeCreateFolderDialog" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>

    <!-- 选择上传目标对话框 -->
    <div v-if="showUploadTargetDialog" class="dialog-overlay" @click="closeUploadTargetDialog">
      <div class="folder-dialog" @click.stop>
        <div class="folder-dialog-header">
          <h3>选择上传目标文件夹</h3>
          <button @click="closeUploadTargetDialog" class="close-btn">×</button>
        </div>
        <div class="folder-dialog-body">
          <div class="folder-path-display">
            <span class="path-label">当前路径:</span>
            <span class="current-path">{{ folderBrowsePath }}</span>
          </div>
          <div class="folder-navigation">
            <!-- 返回上级�������������录 -->
            <div v-if="folderBrowsePath !== '/home/sasuser'" class="folder-nav-item" @click="navigateToParentFolder">
              <span class="folder-icon">📁</span>
              <span class="folder-name">返回上级目录</span>
            </div>
            <!-- 当前目录选择 -->
            <div class="folder-nav-item current-folder" @click="selectCurrentFolder">
              <span class="folder-icon">📂</span>
              <span class="folder-name">选择当前目录</span>
            </div>
            <!-- 子文件夹列表 -->
            <div
              v-for="folder in availableFolders"
              :key="folder.path"
              class="folder-nav-item"
              @click="navigateToFolder(folder.path)"
            >
              <span class="folder-icon">📁</span>
              <span class="folder-name">{{ folder.name }}</span>
            </div>
          </div>
          <div v-if="folderLoading" class="folder-loading">
            正在加载文件夹...
          </div>
        </div>
        <div class="folder-dialog-footer">
          <button @click="confirmFolderSelection" class="confirm-btn" :disabled="!selectedFolderPath">
            确定选择
          </button>
          <button @click="closeUploadTargetDialog" class="cancel-btn">取消</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick, defineEmits } from 'vue';
import { serverFileManager } from '../services/ServerFileManager';
import type { ServerFile, ServerConnection } from '../services/ServerFileManager';

const props = defineProps<{
  mode: string;
  connection: ServerConnection | null;
}>();

// 定义 emit 函数
const emit = defineEmits<{
  'close': [];
  'folder-selected': [path: string];
  'processing-complete': [path: string]; // 新增：处理完成事件
}>();

// 响应式数据
const isConnected = ref(false);
const connecting = ref(false);
const connectionError = ref('');
const currentPath = ref('/');
const files = ref<ServerFile[]>([]);
const loading = ref(false); // 新增：文件列表加载状态
const selectedFiles = ref<string[]>([]);
const highlightedItem = ref<string>('');
const showCreateFolderDialog = ref(false);
const newFolderName = ref('');
const showUploadTargetDialog = ref(false);
const uploadTargetPath = ref('/');

// 新增：文件夹选择后的进度状态
const processingFolderSelection = ref(false);
const processingProgress = ref(0);
const processingMessage = ref('正在处理所选文件夹...');
const processingComplete = ref(false);

// 文件夹浏览相关变量
const folderLoading = ref(false);
const availableFolders = ref<ServerFile[]>([]);

// 连接表单
const connectionForm = reactive<ServerConnection>({
  host: 'sesklsasgrnprd06.emea.astrazeneca.net',
  port: 22,
  username: 'ktxv525',
  password: '',
  protocol: 'sftp'
});

// 引用
const folderNameInput = ref<HTMLInputElement>();

// 计算属性
const pathSegments = computed(() => {
  return currentPath.value.split('/').filter(segment => segment !== '');
});
const folderBrowsePath = computed(() => {
  return uploadTargetPath.value;
});
const selectedFolderPath = computed(() => {
  // 直接返回当前浏览路径，保证按钮可用
  return folderBrowsePath.value;
});

// 方法
const connect = async () => {
  if (!connectionForm.host || !connectionForm.username) {
    connectionError.value = '请填写主机地址和用户名';
    return;
  }

  // 立即设置连接状态为true，显示连接中提示
  connecting.value = true;
  connectionError.value = '';

  try {
    // 连接过程
    console.log(`尝试连接到: ${connectionForm.username}@${connectionForm.host}:${connectionForm.port}`);

    // 确保连接过程中一直显示连接中提示
    const success = await serverFileManager.connect(connectionForm);

    if (success) {
      console.log("连接成功，正在准备加载文件列表...");

      // 连接成功后，先加载文件列表，但不切换界面
      loading.value = true;

      try {
        // 先加载文件列表
        const fileList = await serverFileManager.listFiles(currentPath.value);

        // 对文件进行排序：文件夹优先，然后按名称排序
        const sortedFiles = fileList.sort((a, b) => {
          // 文件夹优先
          if (a.type === 'directory' && b.type !== 'directory') {
            return -1;
          }
          if (a.type !== 'directory' && b.type === 'directory') {
            return 1;
          }
          // 同类型��名称排序
          return a.name.localeCompare(b.name);
        });

        files.value = sortedFiles;
        console.log(`找到 ${fileList.length} 个文件`);

        // 文件����载完成后再切换到文件浏览器界面
        isConnected.value = true;
        loading.value = false;
        connecting.value = false;
      } catch (error) {
        console.error('刷新文件列表失败:', error);
        loading.value = false;
        connecting.value = false;
        connectionError.value = '文件列表加载失败: ' + (error as Error).message;
      }
    } else {
      connectionError.value = '连接失败，请检查连接信息';
      connecting.value = false;
    }
  } catch (error) {
    connectionError.value = '连接失败: ' + (error as Error).message;
    connecting.value = false;
  }
};

const disconnect = async () => {
  await serverFileManager.disconnect();
  isConnected.value = false;
  files.value = [];
  selectedFiles.value = [];
  currentPath.value = '/';
};

const refreshFiles = async () => {
  loading.value = true; // 开始加载前设置 loading 状态为 true
  try {
    const fileList = await serverFileManager.listFiles(currentPath.value);
    // 对文件进行排序：文���夹优���，���后���名称排序
    files.value = fileList.sort((a, b) => {
      // 文件夹优先
      if (a.type === 'directory' && b.type !== 'directory') {
        return -1;
      }
      if (a.type !== 'directory' && b.type === 'directory') {
        return 1;
      }
      // 同类型按名称排序
      return a.name.localeCompare(b.name);
    });
  } catch (error) {
    console.error('��新���件列表失败:', error);
  } finally {
    loading.value = false; // 无论成功还是失败，都将 loading 状态设置为 false
  }
};

const navigateToPath = async (path: string) => {
  currentPath.value = path;
  await refreshFiles();
};

const navigateUp = async () => {
  const parentPath = currentPath.value.substring(0, currentPath.value.lastIndexOf('/')) || '/';
  await navigateToPath(parentPath);
};

const getPathUpTo = (index: number): string => {
  const segments = pathSegments.value.slice(0, index + 1);
  return '/' + segments.join('/');
};

const selectFile = (path: string) => {
  console.log('=== selectFile called ===', { path, mode: props.mode });

  // 在文件夹选择模式下，点击文件夹不应���触发选择事件
  // 只有双击才能进入文件夹
  if (props.mode === 'select-folder') {
    console.log('在文件夹选择模式下，忽略单击事件');
    // ���文件夹选择模式下，��������击文件夹不执行任何操作
    // 用户需要双击进入文件夹��点击工具栏的"选择此文件夹"按钮来确认选择
    return;
  }

  // 在普通模式下，正常处理文件选择
  const index = selectedFiles.value.indexOf(path);
  if (index > -1) {
    selectedFiles.value.splice(index, 1);
  } else {
    selectedFiles.value.push(path);
  }
  console.log('文件选择状态更新:', selectedFiles.value);
};

const handleFileDoubleClick = async (file: ServerFile) => {
  console.log('=== handleFileDoubleClick called ===', { file, mode: props.mode });

  if (file.type === 'directory') {
    console.log('双击文件��，准��导航到:', file.path);

    // 在文件夹选择模式下，双击文件夹应该进入该文件夹继续浏览
    if (props.mode === 'select-folder') {
      console.log('文件夹选择模式，导航到:', file.path);
      await navigateToPath(file.path);
    } else {
      // 在普���浏览模式下，双击文件夹进入该文件夹
      console.log('普通浏览模式，导航到:', file.path);
      await navigateToPath(file.path);
    }
  } else {
    console.log('双击的是文件，不执行任何操作');
  }
};

const handleFileClick = (file: ServerFile, event: MouseEvent) => {
  // 阻止事件冒泡，避免触发双击事件
  event.stopPropagation();

  // 设置高亮状态
  highlightedItem.value = file.path;

  // 在文件夹选择模式下，单���文件夹时更新选中状态
  if (props.mode === 'select-folder' && file.type === 'directory') {
    const index = selectedFiles.value.indexOf(file.path);
    if (index > -1) {
      selectedFiles.value.splice(index, 1);
    } else {
      selectedFiles.value.push(file.path);
    }
  }
};

// 高亮项目的方法
const highlightItem = (itemPath: string) => {
  highlightedItem.value = itemPath;
};

// 显示上传�����选择对话框
const openUploadTargetDialog = async () => {
  showUploadTargetDialog.value = true;
  uploadTargetPath.value = currentPath.value;
  await loadFoldersForDialog(currentPath.value);
};

// 关闭上传�����标选择对话框
const closeUploadTargetDialog = () => {
  // ���要emit('close')，只是关闭内部���上传目标对话框
  showUploadTargetDialog.value = false;
  availableFolders.value = [];
};

// 加载文件夹对话框���文件夹列表
const loadFoldersForDialog = async (path: string) => {
  folderLoading.value = true;
  try {
    const fileList = await serverFileManager.listFiles(path);
    availableFolders.value = fileList.filter(file => file.type === 'directory');
  } catch (error) {
    console.error('加载文件夹失败:', error);
  } finally {
    folderLoading.value = false;
  }
};

// 导航到文件夹
const navigateToFolder = async (path: string) => {
  uploadTargetPath.value = path;
  await loadFoldersForDialog(path);
};

// 导航到父文件夹
const navigateToParentFolder = async () => {
  const parentPath = uploadTargetPath.value.substring(0, uploadTargetPath.value.lastIndexOf('/')) || '/home/sasuser';
  uploadTargetPath.value = parentPath;
  await loadFoldersForDialog(parentPath);
};

// 选择���前文��夹
const selectCurrentFolder = async () => {
  console.log('=== selectCurrentFolder called ===');
  console.log('uploadTargetPath:', uploadTargetPath.value);

  // 显示进度条
  processingFolderSelection.value = true;
  processingProgress.value = 0;
  processingMessage.value = '正在准备文件夹数据...';

  // 模拟进度增长
  await simulateProcessing();

  // 处理完成后，先关闭上传目标对话框
  showUploadTargetDialog.value = false;

  // 然后发送选择事件
  emit('folder-selected', uploadTargetPath.value);
  console.log('已发送 folder-selected 事件，路径:', uploadTargetPath.value);

  // 最后发送处理��成事件
  emit('processing-complete', uploadTargetPath.value);
};

// 确认文件夹选择
const confirmFolderSelection = async () => {
  console.log('=== confirmFolderSelection called ===');
  console.log('当前路径:', currentPath.value);
  console.log('模式:', props.mode);

  // 立即显示进度条和初始状态
  processingFolderSelection.value = true;
  processingProgress.value = 10; // 立即显示一些进度
  processingMessage.value = '正在准备文件夹数据...';
  processingComplete.value = false; // 重置完成状态

  // ��用nextTick确保进度条立即显示
  await nextTick();

  // 模拟进度增长
  await simulateProcessing();

  // 处理完成后发送选择事件
  emit('folder-selected', currentPath.value);
  console.log('已发送 folder-selected 事件，路径:', currentPath.value);

  // 立即发送处理完成事件，触发上传进度显示
  emit('processing-complete', currentPath.value);
  console.log('已发送 processing-complete 事件，准备显示上传进度');

  // 处理完成后隐藏进度条
  processingFolderSelection.value = false;
};

// 模拟处理进度
const simulateProcessing = async () => {
  // 从10%开始进度（因为confirmFolderSelection已经设置了初始10%）
  processingProgress.value = 10;

  // 模拟进度增长 - 缩短每个阶段的时间
  const phases = [
    { progress: 25, message: '扫描文件夹...' },
    { progress: 45, message: '分析文件结构...' },
    { progress: 70, message: '准备数据...' },
    { progress: 90, message: '完成处理...' },
    { progress: 100, message: '处理完成！' }
  ];

  for (const phase of phases) {
    await new Promise(resolve => {
      setTimeout(() => {
        processingProgress.value = phase.progress;
        processingMessage.value = phase.message;
        resolve(null);
      }, 400); // 缩短每个阶段的时间从800ms到400ms
    });
  }

  // 完成后等待一段时间，然后标记为完成
  await new Promise(resolve => {
    setTimeout(() => {
      processingComplete.value = true;
      processingMessage.value = '处理完成！文件夹已选择。';
      resolve(null);
    }, 300); // 缩短等待时间
  });

  // 再等待一段时间后隐藏进度条
  await new Promise(resolve => {
    setTimeout(() => {
      // 不主动隐藏，交给父组件关闭整个对话框
      // processingFolderSelection.value = false;
      // processingComplete.value = false;
      resolve(null);
    }, 500); // 缩短等待时间
  });
};

// 关闭对话框
const closeDialog = () => {
  emit('close');
};

const createFolder = () => {
  showCreateFolderDialog.value = true;
  nextTick(() => {
    folderNameInput.value?.focus();
  });
};

const closeCreateFolderDialog = () => {
  showCreateFolderDialog.value = false;
  newFolderName.value = '';
};

const confirmCreateFolder = async () => {
  if (!newFolderName.value.trim()) return;

  try {
    const success = await serverFileManager.createDirectory(currentPath.value, newFolderName.value);
    if (success) {
      await refreshFiles();
      closeCreateFolderDialog();
    }
  } catch (error) {
    console.error('创建文件夹失败:', error);
  }
};

const deleteFile = async (file: ServerFile) => {
  if (confirm(`确定要删除 "${file.name}" 吗��`)) {
    try {
      const success = await serverFileManager.deleteFile(file.path);
      if (success) {
        await refreshFiles();
      }
    } catch (error) {
      console.error('����失���:', error);
    }
  }
};

const downloadFile = async (file: ServerFile) => {
  // 这里需要实现文件下载功能
  console.log('下载文件:', file.name);
};

// 辅助函数
const getFileIcon = (file: ServerFile): string => {
  if (file.type === 'directory') return '📁';

  const ext = file.name.split('.').pop()?.toLowerCase();
  switch (ext) {
    case 'sas': return '���';
    case 'txt': return '📝';
    case 'log': return '�����';
    case 'pdf': return '📕';
    case 'xlsx': case 'xls': return '📊';
    case 'zip': case 'rar': return '📦';
    default: return '📄';
  }
};

const formatFileSize = (size?: number): string => {
  if (!size) return '-';

  const units = ['B', 'KB', 'MB', 'GB'];
  let unitIndex = 0;
  let fileSize = size;

  while (fileSize >= 1024 && unitIndex < units.length - 1) {
    fileSize /= 1024;
    unitIndex++;
  }

  return `${fileSize.toFixed(1)} ${units[unitIndex]}`;
};

const formatDate = (date?: Date): string => {
  if (!date) return '-';
  return date.toLocaleDateString() + ' ' + date.toLocaleTimeString();
};

const getUploadStatusText = (status: string): string => {
  switch (status) {
    case 'uploading': return '上传中...';
    case 'completed': return '完成';
    case 'error': return '失败';
    default: return '';
  }
};

onMounted(async () => {
  // 如果是文件夹选择模式且有外部 connection，直接用该连接连接服务器
  if (props.mode === 'select-folder' && props.connection) {
    connecting.value = true;
    try {
      await serverFileManager.connect(props.connection);
      currentPath.value = props.connection.remotePath || '/SASDATA2/SafetyNet/';

      // 先加载文件列表
      const fileList = await serverFileManager.listFiles(currentPath.value);
      files.value = fileList.sort((a, b) => {
        if (a.type === 'directory' && b.type !== 'directory') return -1;
        if (a.type !== 'directory' && b.type === 'directory') return 1;
        return a.name.localeCompare(b.name);
      });

      console.log(`找�� ${fileList.length} 个文件`);

      // 文件加载完成后再切换界面
      isConnected.value = true;
      connecting.value = false;
      return;
    } catch (e) {
      connectionError.value = '服务器连接失败，无法浏览文件夹';
      connecting.value = false;
      return;
    }
  }

  // 检查是否已经连接
  if (serverFileManager.isConnectionActive()) {
    connecting.value = true;
    currentPath.value = serverFileManager.getCurrentPath();

    try {
      // 先加载文件列表
      const fileList = await serverFileManager.listFiles(currentPath.value);
      files.value = fileList.sort((a, b) => {
        if (a.type === 'directory' && b.type !== 'directory') return -1;
        if (a.type !== 'directory' && b.type === 'directory') return 1;
        return a.name.localeCompare(b.name);
      });

      console.log(`找到 ${fileList.length} 个文件`);

      // 文件加载完成后再切换界面
      isConnected.value = true;
      connecting.value = false;
    } catch (error) {
      console.error('加载文件列表失败:', error);
      connecting.value = false;
    }
  }
});

// 添加一个防护方法，��保在文件夹选择模式下不会意外触��关闭事件
const preventCloseInSelectMode = () => {
  // 在文件夹选择模式下，不�����许意外关闭对话框
  if (props.mode === 'select-folder') {
    return false;
  }
  return true;
};
</script>

<style scoped>
.server-file-browser {
  font-family: Arial, sans-serif;
  background-color: #f4f4f9;
  color: #333;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  max-width: 1200px;
  width: 90vw;
  max-height: 85vh;
  height: 80vh;
  overflow-y: auto;
  margin: 0 auto;
}

.connection-panel,
.file-browser {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  margin-bottom: 20px;
  height: 100%;
}

h3 {
  margin-top: 0;
  font-size: 1.5em;
  color: #007bff;
}

.form-group {
  margin-bottom: 15px;
}

label {
  display: block;
  margin-bottom: 5px;
  font-weight: bold;
}

input[type="text"],
input[type="number"],
input[type="password"],
select {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  font-size: 1em;
}

input[type="text"]:focus,
input[type="number"]:focus,
input[type="password"]:focus,
select:focus {
  border-color: #007bff;
  outline: none;
}

button {
  background-color: #007bff;
  color: #fff;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

button:hover {
  background-color: #0056b3;
}

.error-message {
  color: #ff0000;
  margin-top: 10px;
}

.path-bar {
  display: flex;
  align-items: center;
  margin-bottom: 15px;
}

.path-label {
  margin-right: 10px;
  font-weight: bold;
}

.path-breadcrumb {
  display: flex;
  flex-grow: 1;
}

.path-segment {
  cursor: pointer;
  color: #007bff;
}

.path-segment:hover {
  text-decoration: underline;
}

.toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-bottom: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
}

.toolbar-actions {
  display: flex;
  gap: 10px;
}

.path-display {
  margin-bottom: 15px;
  padding: 15px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border: 1px solid #e9ecef;
}

.path-label {
  font-weight: bold;
  margin-bottom: 5px;
}

.path-breadcrumb {
  display: flex;
  flex-wrap: wrap;
}

.path-segment {
  cursor: pointer;
  color: #007bff;
  padding: 4px 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.path-segment:hover {
  background-color: #e3f2fd;
  text-decoration: none;
}

.path-separator {
  margin: 0 8px;
  color: #6c757d;
  font-weight: bold;
}

.file-list {
  width: 100%;
  border-collapse: collapse;
  margin-bottom: 15px;
  height: 350px;
  overflow: hidden;
  display: block;
  border: 1px solid #dee2e6;
  border-radius: 4px;
}

.file-list-header {
  background-color: #f1f3f4;
  font-weight: bold;
  display: table;
  width: 100%;
  position: sticky;
  top: 0;
  z-index: 1;
  table-layout: fixed;
}

.file-list-header > div {
  display: table-cell;
  padding: 12px 10px;
  border-bottom: 2px solid #dee2e6;
  text-align: left;
}

.file-list-header .file-name {
  width: 50%;
}

.file-list-header .file-size {
  width: 25%;
  text-align: center;
}

.file-list-header .file-modified {
  width: 25%;
  text-align: center;
}

.file-list-body {
  height: 300px;
  overflow-y: auto;
  display: block;
}

.file-item {
  display: table;
  width: 100%;
  cursor: pointer;
  border-bottom: 1px solid #eee;
  transition: all 0.2s ease;
  table-layout: fixed;
}

.file-item:hover {
  background-color: #f9f9f9;
}

.file-item.highlighted {
  background-color: #e3f2fd;
  box-shadow: 0 2px 8px rgba(0, 123, 255, 0.3);
}

.file-item.selected {
  background-color: #d1ecf1;
  border-color: #bee5eb;
}

.file-name {
  display: table-cell;
  padding: 10px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  width: 50%;
}

.file-size,
.file-modified {
  display: table-cell;
  padding: 10px;
  text-align: center;
  width: 25%;
}

.file-icon {
  margin-right: 5px;
}

.upload-area {
  border: 2px dashed #007bff;
  border-radius: 4px;
  padding: 20px;
  text-align: center;
  margin-top: 20px;
}

.upload-zone {
  cursor: pointer;
}

.upload-zone.drag_over {
  background-color: #e1f5fe;
}

.upload-icon {
  font-size: 2em;
  margin-bottom: 10px;
}

.upload-text {
  font-size: 1.2em;
}

.progress-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
}

.progress-info {
  flex-grow: 1;
}

.progress-bar {
  flex-grow: 2;
  height: 8px;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  position: relative;
}

.progress-fill {
  height: 100%;
  background-color: #007bff;
  transition: width 0.4s;
}

.progress-error {
  color: #ff0000;
  margin-top: 5px;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  max-width: 500px;
  width: 100%;
}

.dialog h3 {
  margin-top: 0;
  font-size: 1.5em;
  color: #007bff;
}

.dialog-actions {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 15px;
}

.folder-dialog {
  background-color: #fff;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  max-width: 800px;
  width: 100%;
  max-height: 70vh;
  overflow-y: auto;
}

.folder-dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.folder-dialog-header h3 {
  margin: 0;
  font-size: 1.5em;
  color: #007bff;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5em;
  cursor: pointer;
}

.folder-dialog-body {
  max-height: 400px;
  overflow-y: auto;
  margin-top: 10px;
}

.folder-path-display {
  padding: 10px;
  background-color: #f9f9f9;
  border-radius: 4px;
  margin-bottom: 10px;
}

.folder-navigation {
  display: flex;
  flex-direction: column;
}

.folder-nav-item {
  display: flex;
  align-items: center;
  padding: 10px;
  cursor: pointer;
}

.folder-nav-item:hover {
  background-color: #f1f1f1;
}

.folder-icon {
  margin-right: 10px;
  font-size: 1.2em;
}

.current-folder {
  font-weight: bold;
  color: #007bff;
}

.folder-loading {
  text-align: center;
  padding: 10px;
  color: #666;
}

.folder-dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  margin-top: 10px;
}

.path-display {
  margin-bottom: 15px;
}

.path-label {
  font-weight: bold;
  margin-bottom: 5px;
}

.path-breadcrumb {
  display: flex;
  flex-wrap: wrap;
}

.path-segment {
  cursor: pointer;
  color: #007bff;
  margin-right: 5px;
}

.path-separator {
  margin: 0 5px;
  color: #666;
}

.bottom-toolbar {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  margin-top: 15px;
  padding: 10px;
  background-color: #f8f9fa;
  border-radius: 4px;
  border-top: 1px solid #e9ecef;
}

.bottom-toolbar .toolbar-actions {
  display: flex;
  gap: 10px;
}

.bottom-toolbar .close-btn {
  background-color: #6c757d;
  color: #fff;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

.bottom-toolbar .close-btn:hover {
  background-color: #5a6268;
}

.bottom-toolbar .confirm-btn {
  background-color: #28a745;
  color: #fff;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

.bottom-toolbar .confirm-btn:hover {
  background-color: #218838;
}

.bottom-toolbar .create-btn {
  background-color: #007bff;
  color: #fff;
  border: none;
  padding: 10px 15px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1em;
}

.bottom-toolbar .create-btn:hover {
  background-color: #0056b3;
}

/* 新��：加载状态提示样式 */
.loading-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100px;
}

.loading-spinner {
  border: 4px solid #007bff;
  border-top: 4px solid transparent;
  border-radius: 50%;
  width: 24px;
  height: 24px;
  animation: spin 1s linear infinite;
}

.loading-text {
  margin-left: 10px;
  font-size: 1.2em;
  color: #333;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* 空文件夹提示样式 */
.empty-folder {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 1.2em;
}

/* 连接中提示样式 */
.connecting-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.connecting-indicator {
  text-align: center;
}

.connecting-spinner {
  border: 4px solid #007bff;
  border-top: 4px solid transparent;
  border-radius: 50%;
  width: 48px;
  height: 48px;
  animation: spin 1s linear infinite;
}

.connecting-text {
  margin-top: 10px;
  font-size: 1.2em;
  color: #333;
}

/* 文件夹处理进度提示样式 */
.processing-dialog {
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  max-width: 400px;
  width: 100%;
  text-align: center;
}

.processing-content {
  margin-top: 10px;
}

.processing-icon {
  font-size: 2em;
  margin-bottom: 10px;
}

.processing-spinner {
  border: 4px solid #007bff;
  border-top: 4px solid transparent;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
}

.processing-complete-icon {
  color: #28a745;
}

.processing-message {
  font-size: 1.2em;
  color: #333;
  margin-bottom: 10px;
}

.processing-progress-container {
  width: 100%;
  background-color: #e0e0e0;
  border-radius: 4px;
  overflow: hidden;
  height: 8px;
  margin-top: 10px;
}

.processing-progress-bar {
  height: 100%;
  background-color: #007bff;
  transition: width 0.4s;
}

.processing-progress-text {
  font-size: 0.9em;
  color: #333;
  margin-top: 5px;
}
</style>

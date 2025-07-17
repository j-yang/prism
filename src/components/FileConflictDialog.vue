<template>
  <div v-if="visible" class="dialog-overlay" @click="closeDialog">
    <div class="dialog conflict-dialog" @click.stop>
      <div class="dialog-header">
        <h3>文件冲突</h3>
        <button @click="closeDialog" class="close-btn">×</button>
      </div>

      <div class="dialog-body">
        <div class="conflict-message">
          <p>以下文件已存在于服务器上，请选择是否覆盖：</p>
        </div>

        <div class="conflict-actions">
          <button
            @click="selectAll"
            class="select-all-btn"
            :class="{ active: allSelected }"
          >
            {{ allSelected ? '取消全选' : '全选' }}
          </button>
          <button
            @click="selectNone"
            class="select-none-btn"
          >
            取消选择
          </button>
        </div>

        <div class="conflict-list">
          <div class="conflict-list-header">
            <div class="conflict-checkbox-col">选择</div>
            <div class="conflict-filename-col">文件名</div>
            <div class="conflict-size-col">本地大小</div>
            <div class="conflict-remote-size-col">服务器大小</div>
            <div class="conflict-modified-col">服务器修改时间</div>
          </div>

          <div class="conflict-list-body">
            <div
              v-for="conflict in conflicts"
              :key="conflict.fileName"
              class="conflict-item"
            >
              <div class="conflict-checkbox-col">
                <input
                  type="checkbox"
                  v-model="conflict.shouldOverwrite"
                  @change="updateSelectAllState"
                />
              </div>
              <div class="conflict-filename-col">
                <span class="filename">{{ conflict.fileName }}</span>
              </div>
              <div class="conflict-size-col">
                {{ formatFileSize(conflict.localFile.size) }}
              </div>
              <div class="conflict-remote-size-col">
                {{ formatFileSize(conflict.remoteFile.size) }}
              </div>
              <div class="conflict-modified-col">
                {{ formatDate(conflict.remoteFile.lastModified) }}
              </div>
            </div>
          </div>
        </div>

        <div class="conflict-summary">
          <p>
            共 {{ conflicts.length }} 个冲突文件，
            已选择覆盖 {{ selectedCount }} 个文件
          </p>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="closeDialog" class="cancel-btn">取消</button>
        <button
          @click="skipSelected"
          class="skip-btn"
          :disabled="conflicts.length === 0"
        >
          跳过冲突文件
        </button>
        <button
          @click="confirmOverwrite"
          class="confirm-btn"
          :disabled="selectedCount === 0"
        >
          覆盖选中文件 ({{ selectedCount }})
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue';
import type { FileConflict, ConflictResolution } from '../services/ServerFileManager';

interface Props {
  visible: boolean;
  conflicts: FileConflict[];
}

interface Emits {
  (e: 'close'): void;
  (e: 'resolve', resolution: ConflictResolution): void;
}

const props = defineProps<Props>();
const emit = defineEmits<Emits>();

// 计算选中的文件数量
const selectedCount = computed(() => {
  return props.conflicts.filter(conflict => conflict.shouldOverwrite).length;
});

// 计算是否全选
const allSelected = computed(() => {
  return props.conflicts.length > 0 && selectedCount.value === props.conflicts.length;
});

// 格式化文件大小
const formatFileSize = (size?: number): string => {
  if (!size) return '未知';

  if (size < 1024) {
    return `${size} B`;
  } else if (size < 1024 * 1024) {
    return `${(size / 1024).toFixed(1)} KB`;
  } else {
    return `${(size / (1024 * 1024)).toFixed(1)} MB`;
  }
};

// 格式化日期
const formatDate = (date?: Date): string => {
  if (!date) return '未知';

  return new Date(date).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  });
};

// 全选
const selectAll = () => {
  const shouldSelect = !allSelected.value;
  console.log('全选操作:', shouldSelect ? '选中所有' : '取消全选');
  props.conflicts.forEach(conflict => {
    conflict.shouldOverwrite = shouldSelect;
  });
};

// 取消选择
const selectNone = () => {
  console.log('取消选择所有��件');
  props.conflicts.forEach(conflict => {
    conflict.shouldOverwrite = false;
  });
};

// 更新全选状态
const updateSelectAllState = () => {
  // 这个方法主要用于触发computed属性的重新计算
  // Vue 3的响应式系统会自动处理
  console.log('更新选择状态，已选择:', selectedCount.value, '个文件');
};

// 确认覆盖
const confirmOverwrite = () => {
  console.log('确认覆盖，选中的文件:', props.conflicts.filter(c => c.shouldOverwrite).map(c => c.fileName));

  const resolution: ConflictResolution = {
    conflicts: props.conflicts,
    overwriteAll: false,
    skipAll: false
  };

  emit('resolve', resolution);
};

// 跳过选中的文件
const skipSelected = () => {
  console.log('跳过冲突文件');

  const resolution: ConflictResolution = {
    conflicts: props.conflicts,
    overwriteAll: false,
    skipAll: true
  };

  emit('resolve', resolution);
};

// 关闭对话框
const closeDialog = () => {
  console.log('关闭冲突对话框');
  emit('close');
};

// 监听冲突列表变化，重置选择状态
watch(() => props.conflicts, (newConflicts) => {
  console.log('冲突列表更新，重置选择状态');
  newConflicts.forEach(conflict => {
    if (conflict.shouldOverwrite === undefined) {
      conflict.shouldOverwrite = false;
    }
  });
}, { deep: true, immediate: true });
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
}

.conflict-dialog {
  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
  width: 90%;
  max-width: 800px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #e0e0e0;
}

.dialog-header h3 {
  margin: 0;
  color: #333;
}

.close-btn {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: #666;
  padding: 0;
  width: 30px;
  height: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.close-btn:hover {
  color: #333;
}

.dialog-body {
  flex: 1;
  padding: 20px;
  overflow-y: auto;
}

.conflict-message {
  margin-bottom: 16px;
}

.conflict-message p {
  margin: 0;
  color: #666;
}

.conflict-actions {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.select-all-btn, .select-none-btn {
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.select-all-btn:hover, .select-none-btn:hover {
  background: #f5f5f5;
}

.select-all-btn.active {
  background: #007bff;
  color: white;
  border-color: #007bff;
}

.conflict-list {
  border: 1px solid #ddd;
  border-radius: 4px;
  overflow: hidden;
}

.conflict-list-header, .conflict-item {
  display: grid;
  grid-template-columns: 60px 1fr 100px 100px 150px;
  gap: 10px;
  padding: 8px 12px;
  align-items: center;
}

.conflict-list-header {
  background: #f8f9fa;
  font-weight: 600;
  color: #333;
  border-bottom: 1px solid #ddd;
}

.conflict-item {
  border-bottom: 1px solid #eee;
}

.conflict-item:last-child {
  border-bottom: none;
}

.conflict-item:hover {
  background: #f8f9fa;
}

.conflict-checkbox-col {
  display: flex;
  justify-content: center;
}

.conflict-filename-col {
  font-weight: 500;
  color: #333;
}

.conflict-size-col, .conflict-remote-size-col {
  font-size: 12px;
  color: #666;
  text-align: center;
}

.conflict-modified-col {
  font-size: 12px;
  color: #666;
}

.conflict-summary {
  margin-top: 16px;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 4px;
}

.conflict-summary p {
  margin: 0;
  font-size: 14px;
  color: #666;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px;
  border-top: 1px solid #e0e0e0;
}

.cancel-btn, .skip-btn, .confirm-btn {
  padding: 8px 16px;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.cancel-btn {
  background: white;
  color: #666;
}

.cancel-btn:hover {
  background: #f5f5f5;
}

.skip-btn {
  background: #ffc107;
  color: white;
  border-color: #ffc107;
}

.skip-btn:hover {
  background: #e0a800;
}

.skip-btn:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.confirm-btn {
  background: #dc3545;
  color: white;
  border-color: #dc3545;
}

.confirm-btn:hover {
  background: #c82333;
}

.confirm-btn:disabled {
  background: #ccc;
  border-color: #ccc;
  cursor: not-allowed;
}

.filename {
  word-break: break-all;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .conflict-dialog {
    width: 95%;
    max-height: 90vh;
  }

  .conflict-list-header, .conflict-item {
    grid-template-columns: 50px 1fr 80px 80px 120px;
    gap: 5px;
    padding: 6px 8px;
    font-size: 12px;
  }

  .dialog-footer {
    flex-direction: column;
    gap: 8px;
  }

  .cancel-btn, .skip-btn, .confirm-btn {
    width: 100%;
  }
}
</style>

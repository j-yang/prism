<template>
  <div class="sas-code-editor">
    <textarea
      ref="textareaRef"
      v-model="localContent"
      @input="onInput"
      @keydown="onKeyDown"
      @keyup="onKeyUp"
      class="code-textarea"
      :placeholder="placeholder"
      spellcheck="false"
    ></textarea>

    <!-- 代码信息面板 -->
    <div class="code-info">
      <span class="line-count">{{ lineCount }} 行</span>
      <span class="char-count">{{ charCount }} 字符</span>
      <span v-if="hasSASCode" class="sas-indicator">📄 SAS</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue';

interface Props {
  modelValue: string;
  placeholder?: string;
}

interface Emits {
  (e: 'update:modelValue', value: string): void;
}

const props = withDefaults(defineProps<Props>(), {
  placeholder: '在此编写SAS代码模板...'
});

const emit = defineEmits<Emits>();

// 响应式数据
const localContent = ref(props.modelValue);
const textareaRef = ref<HTMLTextAreaElement>();

// 计算属性
const lineCount = computed(() => {
  return localContent.value.split('\n').length;
});

const charCount = computed(() => {
  return localContent.value.length;
});

const hasSASCode = computed(() => {
  const content = localContent.value.toLowerCase();
  return content.includes('data ') ||
         content.includes('proc ') ||
         content.includes('%macro') ||
         content.includes('run;') ||
         content.includes('quit;');
});

// 事件处理
const onInput = () => {
  emit('update:modelValue', localContent.value);
};

const onKeyDown = (event: KeyboardEvent) => {
  // Tab键缩进
  if (event.key === 'Tab') {
    event.preventDefault();
    insertText('    '); // 4个空格
  }

  // Enter键自动缩进
  else if (event.key === 'Enter') {
    event.preventDefault(); // 阻止默认的Enter行为
    const textarea = textareaRef.value!;
    const cursorPos = textarea.selectionStart;
    const textBeforeCursor = localContent.value.substring(0, cursorPos);
    const currentLineStart = textBeforeCursor.lastIndexOf('\n') + 1;
    const currentLine = textBeforeCursor.substring(currentLineStart);
    const indentMatch = currentLine.match(/^(\s*)/);
    const currentIndent = indentMatch ? indentMatch[1] : '';

    // 如果当前行以某些关键字结尾，增加缩进
    const needsExtraIndent = /\b(data|proc|do|if|then|%macro)\s*;?\s*$/i.test(currentLine.trim());
    const extraIndent = needsExtraIndent ? '    ' : '';

    // 直接插入，不使用setTimeout
    insertText('\n' + currentIndent + extraIndent);
  }

  // Ctrl+/ 注释/取消注释
  else if (event.ctrlKey && event.key === '/') {
    event.preventDefault();
    toggleComment();
  }
};

const onKeyUp = (event: KeyboardEvent) => {
  // 自动补全
  if (event.key === ' ' || event.key === ';') {
    autoComplete();
  }
};

// 插入文��
const insertText = (text: string) => {
  const textarea = textareaRef.value!;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  localContent.value = localContent.value.substring(0, start) + text + localContent.value.substring(end);

  nextTick(() => {
    const newPos = start + text.length;
    textarea.selectionStart = textarea.selectionEnd = newPos;
    textarea.focus();
    emit('update:modelValue', localContent.value);
  });
};

// 切换注释
const toggleComment = () => {
  const textarea = textareaRef.value!;
  const start = textarea.selectionStart;
  const end = textarea.selectionEnd;

  if (start === end) {
    // 单行注释
    const lineStart = localContent.value.lastIndexOf('\n', start) + 1;
    const lineEnd = localContent.value.indexOf('\n', start);
    const lineEndPos = lineEnd === -1 ? localContent.value.length : lineEnd;
    const line = localContent.value.substring(lineStart, lineEndPos);

    if (line.trim().startsWith('*') && line.trim().endsWith(';')) {
      // 取消注释
      const uncommented = line.replace(/^\s*\*\s?/, '').replace(/\s*;\s*$/, '');
      localContent.value = localContent.value.substring(0, lineStart) + uncommented + localContent.value.substring(lineEndPos);
    } else if (line.trim()) {
      // 添加注释
      const commented = `* ${line.trim()};`;
      localContent.value = localContent.value.substring(0, lineStart) + commented + localContent.value.substring(lineEndPos);
    }
  } else {
    // 多行注释
    const selectedText = localContent.value.substring(start, end);
    if (selectedText.startsWith('/*') && selectedText.endsWith('*/')) {
      // 取消注释
      const uncommented = selectedText.substring(2, selectedText.length - 2);
      localContent.value = localContent.value.substring(0, start) + uncommented + localContent.value.substring(end);
    } else {
      // 添加注释
      const commented = `/*${selectedText}*/`;
      localContent.value = localContent.value.substring(0, start) + commented + localContent.value.substring(end);
    }
  }

  emit('update:modelValue', localContent.value);
};

// 简单的自动补全
const autoComplete = () => {
  const textarea = textareaRef.value!;
  const cursorPos = textarea.selectionStart;
  const textBeforeCursor = localContent.value.substring(0, cursorPos);
  const words = textBeforeCursor.split(/\s+/);
  const lastWord = words[words.length - 1]?.toLowerCase();

  // 简单的自动补全规则
  const completions: Record<string, string> = {
    'data': ' work.',
    'proc': ' print',
    'set': ' work.',
    '%macro': ' ',
    'libname': ' ',
    'filename': ' '
  };

  if (lastWord && completions[lastWord] && !textBeforeCursor.endsWith(completions[lastWord])) {
    insertText(completions[lastWord]);
  }
};

// 监听props变化
watch(() => props.modelValue, (newValue) => {
  if (newValue !== localContent.value) {
    localContent.value = newValue;
  }
});
</script>

<style scoped>
.sas-code-editor {
  position: relative;
  width: 100%;
  height: 100%;
  background: var(--glass-bg-medium);
  border-radius: 16px;
  border: 1px solid var(--glass-border-bright);
  overflow: hidden;
  box-shadow: var(--glass-shadow-strong);
  backdrop-filter: blur(25px);
  -webkit-backdrop-filter: blur(25px);
  transition: all 0.3s ease;
}

.sas-code-editor::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--rainbow-gradient);
  opacity: 0.8;
  z-index: 1;
  border-radius: 16px 16px 0 0;
}

.sas-code-editor::after {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(139, 92, 246, 0.1),
    rgba(99, 102, 241, 0.12),
    rgba(59, 130, 246, 0.1),
    rgba(6, 182, 212, 0.12),
    rgba(20, 184, 166, 0.1),
    transparent);
  transition: left 1s ease;
  z-index: 1;
  pointer-events: none;
}

.sas-code-editor:hover {
  border-color: rgba(99, 102, 241, 0.4);
  box-shadow:
    var(--glass-shadow-strong),
    0 0 30px rgba(99, 102, 241, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.sas-code-editor:hover::after {
  left: 100%;
}

.code-textarea {
  width: 100%;
  height: calc(100% - 50px);
  border: none;
  outline: none;
  padding: 20px;
  font-family: 'JetBrains Mono', 'Consolas', 'Monaco', 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  background: rgba(0, 0, 0, 0.2);
  color: var(--text-primary);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  resize: none;
  tab-size: 4;
  white-space: pre-wrap;
  word-wrap: break-word;
  transition: all 0.3s ease;
  position: relative;
  z-index: 2;
  border-radius: 0 0 16px 16px;
  font-weight: 500;
  letter-spacing: 0.3px;
}

.code-textarea:focus {
  background: rgba(0, 0, 0, 0.3);
  box-shadow:
    inset 0 0 0 2px rgba(99, 102, 241, 0.4),
    inset 0 4px 8px rgba(0, 0, 0, 0.3),
    0 0 20px rgba(99, 102, 241, 0.2);
  color: var(--text-light);
  text-shadow:
    0 1px 3px rgba(0, 0, 0, 0.9),
    0 0 10px rgba(99, 102, 241, 0.3);
}

.code-textarea::placeholder {
  color: var(--text-muted);
  opacity: 0.7;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
  font-style: italic;
}

.code-textarea::selection {
  background: rgba(99, 102, 241, 0.3);
  color: var(--text-light);
}

.code-info {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 50px;
  background: var(--surface-3);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border-top: 1px solid var(--border-glass-bright);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 20px;
  z-index: 3;
  border-radius: 0 0 16px 16px;
}

.code-info::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--accent-gradient);
  opacity: 0.6;
}

.line-count,
.char-count {
  font-size: 0.85rem;
  color: var(--text-secondary);
  font-weight: 600;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  text-shadow: var(--text-shadow-light);
  transition: all 0.3s ease;
}

.line-count:hover,
.char-count:hover {
  background: rgba(255, 255, 255, 0.1);
  color: var(--text-light);
  transform: scale(1.05);
}

.sas-indicator {
  font-size: 0.85rem;
  color: var(--text-light);
  font-weight: 700;
  padding: 8px 16px;
  background: var(--accent-gradient);
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  box-shadow:
    0 4px 12px rgba(6, 182, 212, 0.3),
    inset 0 1px 0 rgba(255, 255, 255, 0.2);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  animation: pulse 2s ease-in-out infinite;
  position: relative;
  overflow: hidden;
}

.sas-indicator::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(255, 255, 255, 0.2),
    transparent);
  animation: shimmer 2s ease-in-out infinite;
}

/* SAS语法高亮效果 */
.code-textarea:focus {
  /* 模拟基本的SAS关键词高亮 */
  background:
    linear-gradient(transparent, transparent),
    rgba(0, 0, 0, 0.3);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .code-textarea {
    font-size: 13px;
    padding: 16px;
  }

  .code-info {
    height: 45px;
    padding: 0 16px;
  }

  .line-count,
  .char-count,
  .sas-indicator {
    font-size: 0.8rem;
    padding: 6px 10px;
  }
}

/* 暗色主题专属优化 */
@media (prefers-color-scheme: dark) {
  .code-textarea {
    background: rgba(0, 0, 0, 0.4);
    color: #f8fafc;
  }

  .code-textarea:focus {
    background: rgba(0, 0, 0, 0.5);
    color: #ffffff;
  }
}

/* 键盘导航优化 */
.code-textarea:focus-visible {
  outline: 3px solid rgba(99, 102, 241, 0.6);
  outline-offset: 2px;
}

/* 滚动条样式 - Webkit */
.code-textarea::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.code-textarea::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.code-textarea::-webkit-scrollbar-thumb {
  background: var(--accent-gradient);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.code-textarea::-webkit-scrollbar-thumb:hover {
  background: var(--primary-gradient);
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
}

/* Firefox滚动条 */
.code-textarea {
  scrollbar-width: thin;
  scrollbar-color: rgba(6, 182, 212, 0.6) rgba(0, 0, 0, 0.2);
}
</style>

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

// 插入文本
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
  font-family: 'Courier New', 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  line-height: 1.5;
  border-radius: 8px;
  overflow: hidden;
  background: #fafafa;
}

.code-textarea {
  width: 100%;
  height: 100%;
  padding: 20px;
  margin: 0;
  border: none;
  outline: none;
  resize: none;
  background: #fafafa;
  color: #2d3748;
  font-family: inherit;
  font-size: inherit;
  line-height: inherit;
  white-space: pre;
  word-wrap: break-word;
  overflow: auto;
  box-sizing: border-box;
  tab-size: 4;
  -moz-tab-size: 4;
}

.code-textarea:focus {
  background: #ffffff;
  box-shadow: inset 0 0 0 2px rgba(102, 126, 234, 0.2);
}

/* 代码信息面板 */
.code-info {
  position: absolute;
  bottom: 10px;
  left: 10px;
  right: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: rgba(255, 255, 255, 0.95);
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  font-size: 12px;
  z-index: 10;
}

.line-count,
.char-count {
  color: #4a5568;
}

.sas-indicator {
  font-weight: 500;
  color: #007bff;
}

/* 滚动条样式 */
.code-textarea::-webkit-scrollbar {
  width: 8px;
  height: 8px;
}

.code-textarea::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
}

.code-textarea::-webkit-scrollbar-thumb {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.code-textarea::-webkit-scrollbar-thumb:hover {
  background: rgba(0, 0, 0, 0.3);
}

.code-textarea::placeholder {
  color: #a0aec0;
  font-style: italic;
}

/* 选中文本样式 */
.code-textarea::selection {
  background: rgba(102, 126, 234, 0.3);
}

/* 微妙的网格背景 */
.code-textarea {
  background-image:
    linear-gradient(rgba(102, 126, 234, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(102, 126, 234, 0.03) 1px, transparent 1px);
  background-size: 20px 20px;
  background-position: 19px 19px;
}

.code-textarea:focus {
  background-image: none;
}
</style>

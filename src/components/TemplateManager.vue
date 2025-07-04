<template>
  <div class="template-manager">
    <div class="templates-layout">
      <!-- 左侧模板列表 -->
      <div class="templates-sidebar">
        <div class="section-card">
          <div class="section-header">
            <h3><i class="icon">📝</i> Template List</h3>
            <div class="header-actions">
              <button @click="createNewTemplate" class="btn-primary btn-small">
                <span class="btn-icon">➕</span> New
              </button>
              <button @click="exportSelectedTemplate" :disabled="!editingTemplate" class="btn-primary btn-small">
                <span class="btn-icon">⬇️</span> Export
              </button>
              <button @click="importTemplates" class="btn-primary btn-small">
                <span class="btn-icon">⬆️</span> Import
              </button>
            </div>
          </div>
          <div class="template-list">
            <div
              v-for="template in templates"
              :key="template.id"
              :class="['template-item', { active: editingTemplate?.id === template.id }]"
              @click="editTemplate(template)"
            >
              <div class="template-icon">📄</div>
              <div class="template-info">
                <div class="template-name">
                  {{ template.name }}
                  <span v-if="template.isDefault" class="default-badge">Default</span>
                </div>
                <div class="template-desc">{{ template.description }}</div>
                <div class="template-meta">
                  <span class="template-type">{{ template.type }}</span>
                  <span class="template-date">{{ formatDate(template.updated) }}</span>
                </div>
              </div>
              <button
                @click.stop="deleteTemplate(template)"
                :class="['delete-btn', { 'disabled': template.isDefault }]"
                :disabled="template.isDefault"
                :title="template.isDefault ? 'Default templates cannot be deleted' : 'Delete template'"
              >
                🗑️
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧编辑器 -->
      <div class="template-editor-area">
        <div class="section-card editor-card">
          <div v-if="!editingTemplate" class="no-template-selected">
            <div class="placeholder-content">
              <div class="placeholder-icon">📝</div>
              <h3>Select a template to start editing</h3>
              <p>Choose a template from the left panel or create a new one</p>
            </div>
          </div>

          <div v-else class="editor-container">
            <div class="editor-toolbar">
              <div class="file-info">
                <span>{{ editingTemplate.filename }}</span>
                <span v-if="templateChanged" class="unsaved-indicator">• Unsaved</span>
              </div>
              <div class="editor-actions">
                <button @click="saveTemplate" :disabled="!templateChanged" class="btn-primary btn-small">
                  <span class="btn-icon">💾</span> Save
                </button>
                <button @click="cancelEdit" class="btn-secondary btn-small">
                  <span class="btn-icon">❌</span> Cancel
                </button>
              </div>
            </div>
            <SASCodeEditor
              v-model="templateContent"
              class="code-editor"
              placeholder="Write your SAS code template here..."
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 新建模板弹窗 -->
    <div v-if="showCreateDialog" class="modal-overlay" @click.self="showCreateDialog = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>📝 Create New Template</h4>
          <button @click="showCreateDialog = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Template Name</label>
            <input
              v-model="newTemplate.name"
              type="text"
              class="form-input"
              placeholder="Enter template name"
              @keyup.enter="confirmCreateTemplate"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Description</label>
            <input
              v-model="newTemplate.description"
              type="text"
              class="form-input"
              placeholder="Enter template description"
            />
          </div>
          <div class="form-group">
            <label class="form-label">Type</label>
            <select v-model="newTemplate.type" class="form-select">
              <option value="Production">Production Template</option>
              <option value="Validation">Validation Template</option>
              <option value="Custom">Custom Template</option>
            </select>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showCreateDialog = false" class="btn-secondary">
            <span class="btn-icon">❌</span> Cancel
          </button>
          <button @click="confirmCreateTemplate" :disabled="!newTemplate.name" class="btn-primary">
            <span class="btn-icon">✅</span> Create
          </button>
        </div>
      </div>
    </div>

    <!-- 导入模板弹窗 -->
    <div v-if="showImportDialog" class="modal-overlay" @click.self="showImportDialog = false">
      <div class="modal-content">
        <div class="modal-header">
          <h4>📤 Import Templates</h4>
          <button @click="showImportDialog = false" class="modal-close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label class="form-label">Template Data</label>
            <textarea
              v-model="importData"
              class="form-textarea"
              placeholder="Paste template data here"
              rows="10"
            ></textarea>
          </div>
        </div>
        <div class="modal-footer">
          <button @click="showImportDialog = false" class="btn-secondary">
            <span class="btn-icon">❌</span> Cancel
          </button>
          <button @click="confirmImport" class="btn-primary">
            <span class="btn-icon">✅</span> Import
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue';
import SASCodeEditor from './SASCodeEditor.vue';
import { templateStorage, type Template } from '../services/TemplateStorageService';

// 状态管理
const templates = ref<Template[]>([]);
const editingTemplate = ref<Template | null>(null);
const templateContent = ref('');
const templateChanged = ref(false);
const originalContent = ref('');
const showCreateDialog = ref(false);
const showImportDialog = ref(false);
const importData = ref('');
const newTemplate = ref({
  name: '',
  description: '',
  type: 'Production' as const
});

// 加载模板数据
async function loadTemplates() {
  try {
    templates.value = await templateStorage.getAllTemplates();
    console.log(`✅ Loaded ${templates.value.length} templates`);
  } catch (error) {
    console.error('Failed to load templates:', error);
    alert('Failed to load templates: ' + (error as Error).message);
  }
}

// 监听模板内容变化 - 只有与原始内容不同时才标记为已修改
watch(templateContent, (newContent) => {
  templateChanged.value = newContent !== originalContent.value;
});

// 方法
function editTemplate(template: Template) {
  if (templateChanged.value && !confirmDiscardChanges()) {
    return;
  }

  editingTemplate.value = template;
  templateContent.value = template.content;
  originalContent.value = template.content;
  templateChanged.value = false;
}

function saveTemplate() {
  if (!editingTemplate.value) return;

  try {
    const updatedTemplate = {
      ...editingTemplate.value,
      content: templateContent.value
    };

    templateStorage.saveTemplate(updatedTemplate);
    originalContent.value = templateContent.value;
    templateChanged.value = false;

    // Reload template list
    loadTemplates();

    console.log('Saving template:', updatedTemplate);
    alert(`Template "${updatedTemplate.name}" saved successfully!`);
  } catch (error) {
    console.error('Failed to save template:', error);
    alert('Save failed: ' + (error as Error).message);
  }
}

function cancelEdit() {
  if (templateChanged.value && !confirmDiscardChanges()) {
    return;
  }

  editingTemplate.value = null;
  templateContent.value = '';
  originalContent.value = '';
  templateChanged.value = false;
}

function createNewTemplate() {
  if (templateChanged.value && !confirmDiscardChanges()) {
    return;
  }

  newTemplate.value = {
    name: '',
    description: '',
    type: 'Production'
  };
  showCreateDialog.value = true;
}

function confirmCreateTemplate() {
  if (!newTemplate.value.name.trim()) {
    alert('Please enter template name');
    return;
  }

  try {
    const template: Template = {
      id: `custom-${Date.now()}`,
      name: newTemplate.value.name,
      description: newTemplate.value.description || 'Custom template',
      type: newTemplate.value.type,
      filename: `${newTemplate.value.name.toLowerCase().replace(/\s+/g, '_')}.sas`,
      content: `/*******************************************************************************
* Program Name: {PROGRAM_NAME}
* Purpose: ${newTemplate.value.description || newTemplate.value.name}
* Programmer: {PROGRAMMER}
* Date: {DATE}
*******************************************************************************/

/* ${newTemplate.value.name} */

/* Add your SAS code here */
`,
      created: new Date(),
      updated: new Date(),
      isDefault: false
    };

    templateStorage.saveTemplate(template);
    loadTemplates();
    showCreateDialog.value = false;

    // Edit new template immediately
    editTemplate(template);
  } catch (error) {
    console.error('Failed to create template:', error);
    alert('Create failed: ' + (error as Error).message);
  }
}

function deleteTemplate(template: Template) {
  if (template.isDefault) {
    alert('Cannot delete default templates');
    return;
  }

  if (!confirm(`Are you sure you want to delete template "${template.name}"?`)) {
    return;
  }

  try {
    templateStorage.deleteTemplate(template.id);
    loadTemplates();

    // Clear editor if deleting current template
    if (editingTemplate.value?.id === template.id) {
      editingTemplate.value = null;
      templateContent.value = '';
      originalContent.value = '';
      templateChanged.value = false;
    }
  } catch (error) {
    console.error('Failed to delete template:', error);
    alert('Delete failed: ' + (error as Error).message);
  }
}

// 新增：导出模板
function exportTemplates() {
  try {
    const data = templateStorage.exportTemplates();
    const blob = new Blob([data], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sas-templates-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error('Export failed:', error);
    alert('Export failed: ' + (error as Error).message);
  }
}

// 新增：导入模板
function importTemplates() {
  showImportDialog.value = true;
}

function confirmImport() {
  if (!importData.value.trim()) {
    alert('Please enter template data');
    return;
  }

  try {
    templateStorage.importTemplates(importData.value);
    loadTemplates();
    showImportDialog.value = false;
    importData.value = '';
    alert('Templates imported successfully!');
  } catch (error) {
    console.error('Import failed:', error);
    alert('Import failed: ' + (error as Error).message);
  }
}

function exportSelectedTemplate() {
  if (!editingTemplate.value) {
    alert('Please select a template first');
    return;
  }

  try {
    const template = editingTemplate.value;
    const blob = new Blob([template.content], { type: 'application/octet-stream' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = template.filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    console.log('Exported template:', template);
  } catch (error) {
    console.error('Export failed:', error);
    alert('Export failed: ' + (error as Error).message);
  }
}

// 新增：重置模板
function resetTemplates() {
  if (!confirm('Are you sure you want to reset to default templates? This will delete all custom templates!')) {
    return;
  }

  try {
    templateStorage.resetToDefault();
    loadTemplates();
    editingTemplate.value = null;
    templateContent.value = '';
    originalContent.value = '';
    templateChanged.value = false;
    alert('Reset to default templates');
  } catch (error) {
    console.error('Reset failed:', error);
    alert('Reset failed: ' + (error as Error).message);
  }
}

function confirmDiscardChanges(): boolean {
  return confirm('You have unsaved changes. Are you sure you want to discard them?');
}

function formatDate(date: Date): string {
  const now = new Date();
  const diffTime = Math.abs(now.getTime() - date.getTime());
  const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

  if (diffDays === 1) {
    return 'Today';
  } else if (diffDays === 2) {
    return 'Yesterday';
  } else if (diffDays <= 7) {
    return `${diffDays - 1} days ago`;
  } else {
    return date.toLocaleDateString('en-US');
  }
}

// 组件挂载时加载模板
onMounted(() => {
  loadTemplates();
});
</script>

<style scoped>
.template-manager {
  height: 100%;
  padding: 20px;
}

.templates-layout {
  display: grid;
  grid-template-columns: 450px 1fr; /* 从350px增加到450px，让模板列表更宽 */
  gap: 30px; /* 从20px增加到30px */
  height: calc(100vh - 120px);
  max-width: 1600px; /* 添加最大宽度限制 */
  margin: 0 auto; /* 居中显示 */
}

.templates-sidebar {
  overflow-y: auto;
}

.section-card {
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  height: 100%;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.section-header h3 {
  margin: 0;
  font-size: 18px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.icon {
  font-size: 20px;
}

.template-list {
  padding: 15px;
  overflow-y: auto;
  max-height: calc(100vh - 200px);
}

.template-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.2s ease;
  background: white;
}

.template-item:hover {
  border-color: #667eea;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.15);
  transform: translateY(-1px);
}

.template-item.active {
  border-color: #667eea;
  background: #f8f9ff;
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
}

.template-icon {
  font-size: 24px;
  color: #667eea;
}

.template-info {
  flex: 1;
}

.template-name {
  font-weight: 600;
  color: #2d3748;
  margin-bottom: 4px;
}

.template-desc {
  font-size: 14px;
  color: #718096;
  margin-bottom: 6px;
}

.template-meta {
  display: flex;
  gap: 12px;
  font-size: 12px;
}

.template-type {
  background: #667eea;
  color: white;
  padding: 2px 8px;
  border-radius: 4px;
}

.template-date {
  color: #a0aec0;
}

.delete-btn {
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.delete-btn:hover {
  opacity: 1;
  color: #e53e3e;
}

.delete-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
  color: #a0aec0;
}

.delete-btn.disabled:hover {
  opacity: 0.3;
  color: #a0aec0;
}

.template-editor-area {
  overflow: hidden;
}

.editor-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.no-template-selected {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  color: #718096;
}

.placeholder-content {
  padding: 40px;
}

.placeholder-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.placeholder-content h3 {
  margin: 0 0 8px 0;
  color: #2d3748;
}

.placeholder-content p {
  margin: 0;
  font-size: 14px;
}

.editor-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  border-bottom: 1px solid #eee;
  background: #f8f9fa;
}

.file-info {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  color: #2d3748;
}

.unsaved-indicator {
  color: #e53e3e;
  font-weight: bold;
}

.editor-actions {
  display: flex;
  gap: 8px;
}

.code-editor {
  flex: 1;
  background: #fafafa;
  border-radius: 8px;
  overflow: hidden;
  min-height: 500px;
  max-height: calc(100vh - 200px);
}

.code-editor:focus {
  background: white;
}

/* 按钮样式 */
.btn-primary, .btn-secondary {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  text-decoration: none;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #e2e8f0;
  color: #4a5568;
}

.btn-secondary:hover {
  background: #cbd5e0;
  transform: translateY(-1px);
}

.btn-small {
  padding: 6px 12px;
  font-size: 13px;
}

.btn-icon {
  font-size: 12px;
}

/* 弹窗样式 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow: hidden;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #eee;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.modal-header h4 {
  margin: 0;
  font-size: 18px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 24px;
  cursor: pointer;
  color: white;
  opacity: 0.8;
}

.modal-close:hover {
  opacity: 1;
}

.modal-body {
  padding: 20px;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 20px;
  border-top: 1px solid #eee;
  background: #f8f9fa;
}

/* 表单样式 */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  margin-bottom: 6px;
  font-weight: 500;
  color: #2d3748;
}

.form-input, .form-select {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  transition: border-color 0.2s ease;
}

.form-input:focus, .form-select:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.form-textarea {
  width: 100%;
  padding: 10px 12px;
  border: 1px solid #e2e8f0;
  border-radius: 6px;
  font-size: 14px;
  resize: vertical;
  transition: border-color 0.2s ease;
}

.form-textarea:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

/* 默认模板标识 */
.default-badge {
  background: #f56565;
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 10px;
  font-weight: 500;
  margin-left: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .templates-layout {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }

  .templates-sidebar {
    height: 300px;
  }
}
</style>

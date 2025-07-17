<template>
  <div class="template-manager">
    <!-- 页面头部 - 与Smart Manufacturing Hub保持一致的设计 -->
    <div class="page-header glass-effect">
      <h2 class="page-title glow-text">
        <svg class="page-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
        </svg>
        <span class="sparkle-text">Template Management Center</span>
      </h2>
      <p class="page-description">Create, edit, and manage SAS program templates for automated code generation</p>
    </div>

    <!-- 内容网格布局 -->
    <div class="content-grid">
      <!-- 左侧模板列表 -->
      <div class="left-column">
        <div class="section-card glass-effect">
          <div class="section-header">
            <h3 class="section-title glow-text">
              <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M12,4A8,8 0 0,1 20,12A8,8 0 0,1 12,20A8,8 0 0,1 4,12A8,8 0 0,1 12,4M11,17H13V11H11M11,9H13V7H11" fill="currentColor"/>
                <circle cx="12" cy="12" r="2" fill="currentColor"/>
              </svg>
              <span class="sparkle-text">Template Library</span>
            </h3>
          </div>
          <div class="section-body">
            <div class="template-actions">
              <button @click="createNewTemplate" class="action-btn new-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="currentColor"/>
                </svg>
                <span>New</span>
              </button>
              <button @click="importTemplates" class="action-btn import-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                </svg>
                <span>Import</span>
              </button>
              <button @click="exportSelectedTemplate" :disabled="!editingTemplate" class="action-btn export-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z" fill="currentColor"/>
                </svg>
                <span>Export</span>
              </button>
            </div>

            <div class="template-list">
              <div
                v-for="template in templates"
                :key="template.id"
                :class="['template-item', { active: editingTemplate?.id === template.id }]"
                @click="editTemplate(template)"
              >
                <div class="template-icon">
                  <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                  </svg>
                </div>
                <div class="template-info">
                  <div class="template-name">
                    <span class="template-title">{{ template.name }}</span>
                  </div>
                  <div class="template-desc">{{ template.description }}</div>
                  <div class="template-meta">
                    <span class="template-type-badge">{{ template.type }}</span>
                    <span class="template-date">{{ formatDate(template.updated) }}</span>
                  </div>
                </div>
                <button
                  @click.stop="deleteTemplate(template)"
                  :class="['delete-btn', { 'disabled': template.isDefault }]"
                  :disabled="template.isDefault"
                  :title="template.isDefault ? 'Default templates cannot be deleted' : 'Delete template'"
                >
                  <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                    <path d="M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z M8,9H16V19H8V9Z M15.5,4L14.5,3H9.5L8.5,4H5V6H19V4H15.5Z" fill="currentColor"/>
                  </svg>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧编辑器 -->
      <div class="right-column">
        <div v-if="!editingTemplate" class="section-card no-template-card glass-effect">
          <div class="section-body">
            <div class="no-data">
              <svg class="no-data-icon" width="64" height="64" viewBox="0 0 24 24" fill="none">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
              </svg>
              <h3>No Template Selected</h3>
              <p>Select a template from the library to edit, or create a new one</p>
              <button @click="createNewTemplate" class="generate-btn">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="currentColor"/>
                </svg>
                <span>Create New Template</span>
              </button>
            </div>
          </div>
        </div>

        <div v-else class="section-card editor-section glass-effect">
          <div class="section-header">
            <h3 class="section-title">
              <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z" fill="currentColor"/>
              </svg>
              <span>Template Editor</span>
            </h3>
            <div class="editor-actions">
              <button @click="saveTemplate" :disabled="!hasChanges" class="generate-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z" fill="currentColor"/>
                </svg>
                <span>Save Changes</span>
              </button>
            </div>
          </div>

          <div class="section-body">
            <div class="editor-form">
              <div class="form-group">
                <label class="form-label">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M9,7H15L11,11L15,15H9V13H5V9H9V7Z" fill="currentColor"/>
                  </svg>
                  Template Name
                </label>
                <input
                  v-model="editingTemplate.name"
                  type="text"
                  class="form-select"
                  placeholder="Enter template name..."
                  @input="markAsChanged"
                />
              </div>

              <div class="form-group">
                <label class="form-label">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z" fill="currentColor"/>
                  </svg>
                  Description
                </label>
                <input
                  v-model="editingTemplate.description"
                  type="text"
                  class="form-select"
                  placeholder="Enter template description..."
                  @input="markAsChanged"
                />
              </div>

              <div class="form-group">
                <label class="form-label">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
                  </svg>
                  Type
                </label>
                <select
                  v-model="editingTemplate.type"
                  class="form-select"
                  @change="markAsChanged"
                >
                  <option value="">Select type...</option>
                  <option value="Production">Production</option>
                  <option value="Validation">Validation</option>
                  <option value="Custom">Custom</option>
                </select>
              </div>

              <div class="form-group">
                <label class="form-label">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                  </svg>
                  SAS Code Template
                  <span class="label-hint">Use placeholders like {DATASET_NAME}, {PROGRAM_NAME}, etc.</span>
                </label>
                <SASCodeEditor
                  v-model="editingTemplate.content"
                  class="code-editor glass-effect"
                  @change="markAsChanged"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 创建新模板对话框 -->
    <div v-if="showCreateDialog" class="dialog-overlay" @click="cancelCreateTemplate">
      <div class="dialog-content glass-effect" @click.stop>
        <div class="dialog-header">
          <h3 class="dialog-title glow-text">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="currentColor"/>
            </svg>
            <span class="sparkle-text">Create New Template</span>
          </h3>
          <button @click="cancelCreateTemplate" class="dialog-close-btn">
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" fill="currentColor"/>
            </svg>
          </button>
        </div>

        <div class="dialog-body">
          <div class="form-group">
            <label class="form-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M9,7H15L11,11L15,15H9V13H5V9H9V7Z" fill="currentColor"/>
              </svg>
              Template Name
            </label>
            <input
              v-model="newTemplateName"
              type="text"
              class="form-select"
              placeholder="Enter template name..."
              @keydown.enter="confirmCreateTemplate"
              ref="templateNameInput"
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M14,3V5H17.59L7.76,14.83L9.17,16.24L19,6.41V10H21V3M19,19H5V5H12V3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19Z" fill="currentColor"/>
              </svg>
              Description
            </label>
            <input
              v-model="newTemplateDescription"
              type="text"
              class="form-select"
              placeholder="Enter template description..."
              @keydown.enter="confirmCreateTemplate"
            />
          </div>

          <div class="form-group">
            <label class="form-label">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
              </svg>
              Type
            </label>
            <select v-model="newTemplateType" class="form-select">
              <option value="Custom">Custom</option>
              <option value="Production">Production</option>
              <option value="Validation">Validation</option>
            </select>
          </div>
        </div>

        <div class="dialog-footer">
          <button @click="cancelCreateTemplate" class="cancel-btn">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M19,6.41L17.59,5L12,10.59L6.41,5L5,6.41L10.59,12L5,17.59L6.41,19L12,13.41L17.59,19L19,17.59L13.41,12L19,6.41Z" fill="currentColor"/>
            </svg>
            <span>Cancel</span>
          </button>
          <button @click="confirmCreateTemplate" class="confirm-btn" :disabled="!newTemplateName.trim()">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
              <path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z" fill="currentColor"/>
            </svg>
            <span>Create Template</span>
          </button>
        </div>
      </div>
    </div>

    <!-- 文件输入（隐藏） -->
    <input
      ref="fileInput"
      type="file"
      accept=".json,.sas"
      multiple
      style="display: none"
      @change="handleFileImport"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, computed, nextTick } from 'vue';
import SASCodeEditor from './SASCodeEditor.vue';
import { templateStorage, type Template } from '../services/TemplateStorageService';

// 状态管理
const templates = ref<Template[]>([]);
const editingTemplate = ref<Template | null>(null);
const templateContent = ref('');
const templateChanged = ref(false);
const originalContent = ref('');
const fileInput = ref<HTMLInputElement>();

// 创建模板对话框状态
const showCreateDialog = ref(false);
const newTemplateName = ref('');
const newTemplateDescription = ref('');
const newTemplateType = ref('Custom');

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

// 计算属性：检查是否有未保存的更改
const hasChanges = computed(() => {
  if (!editingTemplate.value) return false;
  return templateChanged.value;
});

// 方法
function editTemplate(template: Template) {
  if (templateChanged.value && !confirmDiscardChanges()) {
    return;
  }

  editingTemplate.value = { ...template }; // 创建副本以避免直接修改原对象
  templateContent.value = template.content;
  originalContent.value = template.content;
  templateChanged.value = false;
}

function markAsChanged() {
  templateChanged.value = true;
}

function saveTemplate() {
  if (!editingTemplate.value) return;

  try {
    const updatedTemplate = {
      ...editingTemplate.value,
      content: editingTemplate.value.content,
      updated: new Date()
    };

    templateStorage.saveTemplate(updatedTemplate);
    originalContent.value = editingTemplate.value.content;
    templateChanged.value = false;

    // 重新加载模板列表
    loadTemplates();

    console.log('✅ 模板保存成功:', updatedTemplate.name);
    alert(`Template "${updatedTemplate.name}" saved successfully!`);
  } catch (error) {
    console.error('❌ 模板保存失败:', error);
    alert('Save failed: ' + (error as Error).message);
  }
}

function createNewTemplate() {
  if (templateChanged.value && !confirmDiscardChanges()) {
    return;
  }

  // 打开创建模板对话框
  showCreateDialog.value = true;
  nextTick(() => {
    if (fileInput.value) {
      fileInput.value.value = '';
    }
  });
}

function confirmCreateTemplate() {
  if (!newTemplateName.value.trim()) {
    return;
  }

  // 创建新模板
  const template: Template = {
    id: `custom-${Date.now()}`,
    name: newTemplateName.value.trim(),
    description: newTemplateDescription.value || 'Custom template',
    type: newTemplateType.value,
    filename: `${newTemplateName.value.toLowerCase().replace(/\s+/g, '_')}.sas`,
    content: `**************************************************************************;
* Program name      : @@program_name
*
* Program path      : root/cdar/d693/d6935c00003/ar/dr1/adam/dev/program
*
* Type              : SAS program
*jimmy
* Purpose           : @@purpose
*
* Author            : @@author
*
* Date created      : @@date
*
* Input datasets    :

* Macros used       : %setup, %localsetup, %m_adam_attrib
*
* Output files      : @@output
*
* Usage notes       :
**************************************************************************;

%setup(version=260,
	   localsetup=root/cdar/%scan(&_exec_programpath.,3,/)/%scan(&_exec_programpath.,4,/)/ar/%scan(&_exec_programpath.,6,/)/common/dev/macro/localsetup.sas);

%localsetup;

proc datasets lib=work kill nowarn nodetails nolist mt=data;
quit;

%let PGMNAME=%scan(&_EXEC_PROGRAMNAME,1, ".");
%let domain = %upcase(&pgmname.);
%procprint_indi;
`,
    created: new Date(),
    updated: new Date(),
    isDefault: false
  };

  try {
    templateStorage.saveTemplate(template);
    loadTemplates();
    console.log('✅ 新模板创建成功:', template.name);
    alert(`Template "${template.name}" created successfully!`);

    // 立即编辑新创建的模板
    editTemplate(template);
  } catch (error) {
    console.error('❌ 创建模板失败:', error);
    alert('Create failed: ' + (error as Error).message);
  } finally {
    // 关闭对话框
    showCreateDialog.value = false;
    newTemplateName.value = '';
    newTemplateDescription.value = '';
    newTemplateType.value = 'Custom';
  }
}

function cancelCreateTemplate() {
  showCreateDialog.value = false;
  newTemplateName.value = '';
  newTemplateDescription.value = '';
  newTemplateType.value = 'Custom';
}

function deleteTemplate(template: Template) {
  if (template.isDefault) {
    alert('Default templates cannot be deleted');
    return;
  }

  if (confirm(`Are you sure you want to delete "${template.name}"?`)) {
    try {
      templateStorage.deleteTemplate(template.id);
      loadTemplates();

      if (editingTemplate.value?.id === template.id) {
        editingTemplate.value = null;
        templateContent.value = '';
        originalContent.value = '';
        templateChanged.value = false;
      }

      console.log('Template deleted:', template.name);
    } catch (error) {
      console.error('Failed to delete template:', error);
      alert('Delete failed: ' + (error as Error).message);
    }
  }
}

function exportSelectedTemplate() {
  if (!editingTemplate.value) return;

  try {
    const dataStr = JSON.stringify(editingTemplate.value, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);

    const link = document.createElement('a');
    link.href = url;
    link.download = `${editingTemplate.value.name}.json`;
    link.click();

    URL.revokeObjectURL(url);
    console.log('Template exported:', editingTemplate.value.name);
  } catch (error) {
    console.error('Failed to export template:', error);
    alert('Export failed: ' + (error as Error).message);
  }
}

function importTemplates() {
  // 使用正确的ref引用
  if (fileInput.value) {
    fileInput.value.click();
  }
}

function handleFileImport(event: Event) {
  const target = event.target as HTMLInputElement;
  const files = target.files;

  if (!files || files.length === 0) return;

  Array.from(files).forEach(file => {
    const reader = new FileReader();
    reader.onload = (e) => {
      try {
        const content = e.target?.result as string;
        let template: Template;

        if (file.name.endsWith('.json')) {
          template = JSON.parse(content);
        } else if (file.name.endsWith('.sas')) {
          template = {
            id: `imported-${Date.now()}-${Math.random()}`,
            name: file.name.replace('.sas', ''),
            description: 'Imported template',
            type: 'Custom' as const,
            filename: file.name,
            content: content,
            created: new Date(),
            updated: new Date(),
            isDefault: false
          };
        } else {
          throw new Error('Unsupported file type');
        }

        templateStorage.saveTemplate(template);
        loadTemplates();
        console.log('Template imported:', template.name);
      } catch (error) {
        console.error('Failed to import template:', error);
        alert(`Failed to import ${file.name}: ` + (error as Error).message);
      }
    };
    reader.readAsText(file);
  });

  // Reset input
  target.value = '';
}

function confirmDiscardChanges(): boolean {
  return confirm('You have unsaved changes. Are you sure you want to discard them?');
}

function formatDate(date: Date): string {
  return new Date(date).toLocaleDateString();
}

// 初始化
onMounted(() => {
  loadTemplates();
});
</script>

<style scoped>
.template-manager {
  width: 100%;
  height: 100%;
  animation: fadeInUp 0.6s ease;
}

/* 页面头部 - 增强文字对比度 */
.page-header {
  text-align: center;
  margin-bottom: 40px;
  padding: 30px 20px;
  background: var(--glass-bg-strong);
  backdrop-filter: blur(20px);
  border-radius: 16px;
  border: 1px solid var(--border-glass-bright);
  box-shadow: var(--shadow-md);
  position: relative;
  overflow: hidden;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 1px;
  background: var(--border-glass-bright);
  opacity: 0.6;
}

.page-title {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin: 0 0 12px 0;
  font-size: 1.8rem;
  font-weight: 700;
  color: var(--text-dark);
  text-shadow: none;
}

.page-title .sparkle-text {
  color: var(--text-dark);
  font-weight: 700;
  text-shadow: none;
  background: none;
  -webkit-background-clip: unset;
  -webkit-text-fill-color: unset;
  background-clip: unset;
}

.page-icon {
  color: var(--prism-primary);
  opacity: 1;
}

/* 网格布局 */
.content-grid {
  display: grid;
  grid-template-columns: 380px 1fr; /* Slightly smaller left column */
  gap: 30px;
  align-items: start;
}

@media (max-width: 1200px) {
  .content-grid {
    grid-template-columns: 1fr;
    gap: 20px;
  }
}

/* 卡片样式 - 简约设计 */
.section-card {
  background: var(--glass-bg-medium);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid var(--glass-border);
  box-shadow: var(--shadow-sm);
  border-radius: 12px;
  position: relative;
  overflow: hidden;
  margin-bottom: 24px;
  transition: all 0.2s ease;
}

.section-card::before {
  display: none; /* 移除动画效果 */
}

.section-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: var(--glass-border-bright);
}

.section-header {
  padding: 24px 28px 20px;
  border-bottom: 1px solid var(--border-glass);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface-1);
  position: relative;
}

.section-header::after {
  display: none;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-dark);
  text-shadow: none;
}

.section-title .sparkle-text {
  color: var(--text-dark);
  font-weight: 700;
  text-shadow: none;
  background: none;
  -webkit-background-clip: unset;
  -webkit-text-fill-color: unset;
  background-clip: unset;
}

.section-icon {
  color: var(--prism-primary);
  opacity: 1;
}

.section-body {
  padding: 28px;
}

/* 模板操作按钮 - 优化间距 */
.template-actions {
  display: flex;
  gap: 16px;
  margin-bottom: 24px;
  padding: 4px;
}

/* 模板列表 - 优化布局和间距 */
.template-list {
  max-height: 600px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: var(--border-glass) transparent;
  padding: 4px;
}

/* 模板项目 - 优化间距 */
.template-item {
  background: var(--glass-bg-light);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border: 1px solid var(--border-glass);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  position: relative;
  overflow: hidden;
}

.template-item.active {
  border-color: var(--prism-primary);
  background: var(--glass-bg-strong);
}

.template-item::before {
  display: none;
}

.template-item:hover {
  transform: translateY(-1px);
  background: var(--glass-bg-medium);
  border-color: var(--glass-border-bright);
  box-shadow: var(--shadow-sm);
}

.template-item.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--prism-primary);
  opacity: 0.8;
  z-index: 2;
}

.template-icon {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--prism-primary);
  color: #fff;
  margin-right: 12px;
}

.template-info {
  flex: 1;
  min-width: 0;
}

.template-name {
  font-size: 1rem;
  font-weight: 500;
  color: var(--text-dark);
  margin: 0 0 4px 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.template-title {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-dark);
  text-shadow: none;
}

.template-desc {
  color: var(--text-secondary);
  font-size: 0.8rem;
  margin-bottom: 6px;
  font-weight: 400;
  text-shadow: none;
}

.template-meta {
  display: flex;
  align-items: center;
  gap: 8px;
}

.template-type-badge {
  background: var(--glass-bg-medium);
  color: var(--text-primary);
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 0.7rem;
  font-weight: 500;
  border: 1px solid var(--border-glass);
  text-shadow: none;
}

.template-date {
  color: var(--text-tertiary);
  font-size: 0.7rem;
  font-weight: 400;
  text-shadow: none;
}

.delete-btn {
  background: rgba(220, 38, 38, 0.1);
  border: 1px solid rgba(220, 38, 38, 0.3);
  color: var(--prism-danger);
  padding: 8px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  backdrop-filter: blur(5px);
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.delete-btn:hover {
  background: rgba(220, 38, 38, 0.2);
  border-color: rgba(220, 38, 38, 0.5);
  transform: scale(1.05);
}

.delete-btn.disabled {
  opacity: 0.3;
  cursor: not-allowed;
  transform: none;
  background: rgba(156, 163, 175, 0.1);
  border-color: rgba(156, 163, 175, 0.2);
  color: rgba(156, 163, 175, 0.5);
}

/* 按钮样式 */
.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 8px 12px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #fff;
  background: var(--prism-primary);
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.action-btn svg {
  margin-right: 4px;
}

.action-btn:disabled {
  background: var(--glass-bg-medium);
  cursor: not-allowed;
}

.generate-btn {
  background: var(--prism-green);
}

.new-btn {
  background: var(--prism-blue);
}

.import-btn {
  background: var(--prism-blue);
}

.export-btn {
  background: var(--prism-blue);
}

/* 编辑器样式 */
.editor-form {
  height: 100%;
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.editor-form .form-group:last-child {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.editor-form .form-group:last-child .code-editor {
  flex: 1;
  min-height: 400px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: var(--text-primary);
  margin-bottom: 8px;
  font-size: 0.9rem;
  text-shadow: none;
}

.form-select {
  padding: 12px 16px;
  border-radius: 8px;
  border: 1px solid var(--border-glass);
  background: var(--surface-2);
  font-size: 0.875rem;
  color: var(--text-dark);
  transition: all 0.2s ease;
}

.form-select:focus {
  border-color: var(--prism-primary);
  outline: none;
  box-shadow: 0 0 0 2px rgba(0, 123, 255, 0.25);
}

.label-hint {
  font-size: 0.75rem;
  color: var(--text-muted);
  font-weight: 400;
  font-style: italic;
  text-shadow: none;
}

/* 对话框样式 */
.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog-content {
  width: 90%;
  max-width: 500px;
  background: var(--glass-bg-strong);
  border-radius: 12px;
  box-shadow: var(--shadow-lg);
  overflow: hidden;
  position: relative;
}

.dialog-header {
  padding: 16px 24px;
  border-bottom: 1px solid var(--border-glass);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: var(--surface-1);
}

.dialog-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.25rem;
  font-weight: 500;
  color: var(--text-dark);
}

.dialog-close-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: var(--prism-red);
  color: #fff;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.dialog-close-btn svg {
  width: 16px;
  height: 16px;
}

.dialog-body {
  padding: 16px 24px;
  background: var(--surface-2);
}

.dialog-footer {
  padding: 12px 24px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  background: var(--surface-1);
  border-top: 1px solid var(--border-glass);
}

.cancel-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: var(--text-dark);
  background: var(--glass-bg-medium);
  border: 1px solid var(--border-glass);
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.cancel-btn svg {
  width: 16px;
  height: 16px;
}

.confirm-btn {
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 0.875rem;
  font-weight: 500;
  color: #fff;
  background: var(--prism-primary);
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.confirm-btn svg {
  width: 16px;
  height: 16px;
}

/* 无数据时的占位样式 */
.no-data {
  text-align: center;
  padding: 40px 20px;
  color: var(--text-secondary);
}

.no-data-icon {
  width: 64px;
  height: 64px;
  margin-bottom: 16px;
}

.no-data h3 {
  font-size: 1.2rem;
  font-weight: 500;
  color: var(--text-primary);
  margin: 0 0 12px 0;
  text-shadow: none;
}

.no-data p {
  font-size: 0.95rem;
  font-weight: 400;
  margin: 0 0 20px 0;
  color: var(--text-secondary);
  text-shadow: none;
}

/* 右侧编辑器区域 - 修复滚动问题 */
.right-column {
  height: calc(100vh - 200px);
  overflow: hidden;
}

.editor-section {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-section .section-header {
  flex-shrink: 0;
}

.editor-section .section-body {
  flex: 1;
  overflow-y: auto;
  padding: 24px 28px;
}

/* 编辑器操作按钮 - 统一字体样式 */
.editor-actions .generate-btn {
  padding: 12px 20px;
  background: var(--prism-primary);
  border: none;
  border-radius: 8px;
  color: white;
  font-size: 0.9rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.2s ease;
  box-shadow: var(--shadow-sm);
  text-shadow: none;
  letter-spacing: 0.02em;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

.editor-actions .generate-btn:hover {
  transform: translateY(-1px);
  box-shadow: var(--shadow-md);
  background: var(--prism-secondary);
}

.editor-actions .generate-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 代码编辑器 - 确保正确尺寸 */
.code-editor {
  height: 100%;
  min-height: 400px;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid var(--border-glass);
}
</style>

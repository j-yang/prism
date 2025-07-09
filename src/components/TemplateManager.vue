<template>
  <div class="template-manager">
    <div class="templates-layout">
      <!-- 左侧模板列表 -->
      <div class="templates-sidebar">
        <div class="section-card glass-effect">
          <div class="section-header">
            <h3 class="section-title glow-text">
              <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
              </svg>
              <span class="sparkle-text">Template Library</span>
            </h3>
            <div class="header-actions">
              <button @click="createNewTemplate" class="btn-primary btn-small glass-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="currentColor"/>
                </svg>
                <span>New</span>
              </button>
              <button @click="exportSelectedTemplate" :disabled="!editingTemplate" class="btn-primary btn-small glass-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z" fill="currentColor"/>
                </svg>
                <span>Export</span>
              </button>
              <button @click="importTemplates" class="btn-primary btn-small glass-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                </svg>
                <span>Import</span>
              </button>
            </div>
          </div>
          <div class="template-list">
            <div
              v-for="template in templates"
              :key="template.id"
              :class="['template-item glass-card', { active: editingTemplate?.id === template.id }]"
              @click="editTemplate(template)"
            >
              <div class="template-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                  <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                </svg>
              </div>
              <div class="template-info">
                <div class="template-name">
                  <span class="sparkle-text">{{ template.name }}</span>
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
                :class="['delete-btn glass-btn-danger', { 'disabled': template.isDefault }]"
                :disabled="template.isDefault"
                :title="template.isDefault ? 'Default templates cannot be deleted' : 'Delete template'"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" fill="currentColor"/>
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- 右侧编辑器 -->
      <div class="template-editor">
        <div v-if="!editingTemplate" class="no-template glass-effect">
          <div class="no-template-content">
            <svg class="no-template-icon" width="64" height="64" viewBox="0 0 24 24" fill="none">
              <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
            </svg>
            <h3 class="glow-text">No Template Selected</h3>
            <p>Select a template from the list to edit, or create a new one</p>
            <button @click="createNewTemplate" class="btn-primary glass-btn">
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M19,13H13V19H11V13H5V11H11V5H13V11H19V13Z" fill="currentColor"/>
              </svg>
              <span>Create New Template</span>
            </button>
          </div>
        </div>

        <div v-else class="section-card editor-card glass-effect">
          <div class="section-header">
            <h3 class="section-title glow-text">
              <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z" fill="currentColor"/>
              </svg>
              <span class="sparkle-text">Template Editor</span>
            </h3>
            <div class="editor-actions">
              <button @click="saveTemplate" :disabled="!hasChanges" class="btn-primary glass-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M15,9H5V5H15M12,19A3,3 0 0,1 9,16A3,3 0 0,1 12,13A3,3 0 0,1 15,16A3,3 0 0,1 12,19M17,3H5C3.89,3 3,3.9 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V7L17,3Z" fill="currentColor"/>
                </svg>
                <span>Save Changes</span>
              </button>
              <button @click="resetTemplate" class="btn-secondary glass-btn">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                  <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z" fill="currentColor"/>
                </svg>
                <span>Reset</span>
              </button>
            </div>
          </div>

          <div class="editor-form">
            <div class="form-group">
              <label class="form-label sparkle-text">Template Name</label>
              <input
                v-model="editingTemplate.name"
                type="text"
                class="form-input glass-input"
                placeholder="Enter template name..."
                @input="markAsChanged"
              />
            </div>

            <div class="form-group">
              <label class="form-label sparkle-text">Description</label>
              <input
                v-model="editingTemplate.description"
                type="text"
                class="form-input glass-input"
                placeholder="Enter template description..."
                @input="markAsChanged"
              />
            </div>

            <div class="form-group">
              <label class="form-label sparkle-text">Type</label>
              <select
                v-model="editingTemplate.type"
                class="form-select glass-input"
                @change="markAsChanged"
              >
                <option value="Production">Production</option>
                <option value="Validation">Validation</option>
                <option value="Custom">Custom</option>
              </select>
            </div>

            <div class="form-group">
              <label class="form-label sparkle-text">
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
import { ref, watch, onMounted, computed } from 'vue';
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
const fileInput = ref<HTMLInputElement>();

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
      content: editingTemplate.value.content, // 使用编辑器中的内容
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

  // 直接创建新模板，不需要对话框
  const templateName = prompt('Enter template name:', 'New Template');
  if (!templateName?.trim()) {
    return;
  }

  const templateDescription = prompt('Enter template description:', 'Custom template');

  try {
    const template: Template = {
      id: `custom-${Date.now()}`,
      name: templateName.trim(),
      description: templateDescription || 'Custom template',
      type: 'Custom',
      filename: `${templateName.toLowerCase().replace(/\s+/g, '_')}.sas`,
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

    templateStorage.saveTemplate(template);
    loadTemplates();

    // 立即编辑新创建的模板
    editTemplate(template);
    console.log('✅ 新模板创建成功:', template.name);
  } catch (error) {
    console.error('❌ 创建模板失败:', error);
    alert('Create failed: ' + (error as Error).message);
  }
}

function resetTemplate() {
  if (!editingTemplate.value) return;

  if (confirm('Are you sure you want to reset all changes?')) {
    editingTemplate.value.content = originalContent.value;
    templateChanged.value = false;
  }
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

.templates-layout {
  display: grid;
  grid-template-columns: 400px 1fr;
  gap: 30px;
  height: calc(100vh - 200px);
  min-height: 600px;
}

@media (max-width: 1200px) {
  .templates-layout {
    grid-template-columns: 1fr;
    gap: 20px;
    height: auto;
  }
}

/* 左侧模板列表 */
.templates-sidebar {
  height: 100%;
}

.template-list {
  max-height: calc(100% - 80px);
  overflow-y: auto;
  padding: 20px;
  scrollbar-width: thin;
  scrollbar-color: rgba(6, 182, 212, 0.6) rgba(0, 0, 0, 0.2);
}

.template-list::-webkit-scrollbar {
  width: 8px;
}

.template-list::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.template-list::-webkit-scrollbar-thumb {
  background: var(--accent-gradient);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.template-list::-webkit-scrollbar-thumb:hover {
  background: var(--primary-gradient);
  box-shadow: 0 0 10px rgba(99, 102, 241, 0.3);
}

.template-item {
  background: var(--glass-bg-light);
  backdrop-filter: blur(15px);
  -webkit-backdrop-filter: blur(15px);
  border: 1px solid var(--border-glass);
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: flex-start;
  gap: 15px;
  position: relative;
  overflow: hidden;
}

.template-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg,
    transparent,
    rgba(139, 92, 246, 0.08),
    rgba(99, 102, 241, 0.1),
    rgba(59, 130, 246, 0.08),
    rgba(6, 182, 212, 0.1),
    rgba(20, 184, 166, 0.08),
    transparent);
  transition: left 0.8s ease;
  z-index: 1;
}

.template-item:hover {
  transform: translateY(-3px);
  background: var(--glass-bg-medium);
  border-color: rgba(99, 102, 241, 0.3);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
}

.template-item:hover::before {
  left: 100%;
}

.template-item.active {
  background: var(--surface-2);
  border-color: var(--prism-indigo);
  box-shadow:
    0 8px 25px rgba(0, 0, 0, 0.4),
    0 0 20px rgba(99, 102, 241, 0.3);
  transform: translateY(-2px);
}

.template-item.active::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gradient);
  opacity: 0.8;
  z-index: 2;
}

.template-icon {
  color: var(--text-accent);
  opacity: 0.8;
  filter: drop-shadow(0 2px 4px rgba(6, 182, 212, 0.3));
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.template-info {
  flex: 1;
  min-width: 0;
  position: relative;
  z-index: 2;
}

.template-name {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.template-name .sparkle-text {
  font-size: 1rem;
  font-weight: 700;
  color: var(--text-primary);
  text-shadow: var(--text-shadow-medium);
  /* Remove breathing light effect - no animation */
}

.default-badge {
  background: var(--secondary-gradient);
  color: var(--text-light);
  padding: 4px 10px;
  border-radius: 8px;
  font-size: 0.75rem;
  font-weight: 600;
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.5);
  box-shadow: 0 2px 6px rgba(244, 63, 94, 0.3);
}

.template-desc {
  color: var(--text-secondary);
  font-size: 0.9rem;
  margin-bottom: 8px;
  text-shadow: var(--text-shadow-light);
}

.template-meta {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 15px;
}

.template-type {
  background: var(--glass-bg-medium);
  color: var(--text-accent);
  padding: 4px 8px;
  border-radius: 6px;
  font-size: 0.8rem;
  font-weight: 600;
  border: 1px solid var(--border-glass);
  text-shadow: var(--text-shadow-light);
}

.template-date {
  color: var(--text-muted);
  font-size: 0.8rem;
  font-weight: 500;
  text-shadow: var(--text-shadow-light);
}

.delete-btn {
  background: rgba(239, 68, 68, 0.2);
  border: 1px solid rgba(239, 68, 68, 0.3);
  color: #fca5a5;
  padding: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
  backdrop-filter: blur(10px);
  flex-shrink: 0;
  position: relative;
  z-index: 2;
}

.delete-btn:hover {
  background: rgba(239, 68, 68, 0.3);
  border-color: rgba(239, 68, 68, 0.5);
  color: #fee2e2;
  transform: scale(1.1);
}

.delete-btn.disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none;
}

/* 右侧编辑器 */
.template-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.no-template {
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  background: var(--glass-bg-medium);
  backdrop-filter: blur(25px);
  border-radius: 20px;
  border: 1px solid var(--border-glass);
  box-shadow: var(--glass-shadow);
}

.no-template-content {
  max-width: 400px;
  padding: 40px;
}

.no-template-icon {
  color: var(--text-muted);
  opacity: 0.6;
  margin-bottom: 20px;
  filter: drop-shadow(0 4px 8px rgba(6, 182, 212, 0.2));
}

.no-template h3 {
  margin: 0 0 15px 0;
  font-size: 1.5rem;
  color: var(--text-primary);
}

.no-template p {
  color: var(--text-secondary);
  margin: 0 0 25px 0;
  line-height: 1.6;
  text-shadow: var(--text-shadow-light);
}

.editor-card {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-form {
  flex: 1;
  padding: 30px;
  overflow-y: auto;
  scrollbar-width: thin;
  scrollbar-color: rgba(6, 182, 212, 0.6) rgba(0, 0, 0, 0.2);
}

.editor-form::-webkit-scrollbar {
  width: 8px;
}

.editor-form::-webkit-scrollbar-track {
  background: rgba(0, 0, 0, 0.2);
  border-radius: 4px;
}

.editor-form::-webkit-scrollbar-thumb {
  background: var(--accent-gradient);
  border-radius: 4px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.form-group {
  margin-bottom: 25px;
}

.form-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
  font-weight: 700;
  color: var(--text-primary);
  font-size: 0.95rem;
  text-shadow: var(--text-shadow-medium);
}

.label-hint {
  font-size: 0.8rem;
  color: var(--text-muted);
  font-weight: 500;
  font-style: italic;
  text-shadow: var(--text-shadow-light);
}

.form-input {
  width: 100%;
  padding: 12px 16px;
  background: var(--glass-bg-medium);
  backdrop-filter: blur(15px);
  border: 1px solid var(--border-glass);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: all 0.3s ease;
  text-shadow: var(--text-shadow-light);
}

.form-input:focus {
  outline: none;
  border-color: var(--prism-indigo);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
  background: var(--surface-2);
  color: var(--text-light);
}

.form-input::placeholder {
  color: var(--text-muted);
  opacity: 0.7;
  text-shadow: var(--text-shadow-light);
}

.form-select {
  width: 100%;
  padding: 12px 16px;
  background: var(--glass-bg-medium);
  backdrop-filter: blur(15px);
  border: 1px solid var(--border-glass);
  border-radius: 12px;
  color: var(--text-primary);
  font-size: 0.95rem;
  transition: all 0.3s ease;
  text-shadow: var(--text-shadow-light);
  cursor: pointer;
}

.form-select:focus {
  outline: none;
  border-color: var(--prism-indigo);
  box-shadow: 0 0 0 3px rgba(99, 102, 241, 0.2);
  background: var(--surface-2);
}

.form-select option {
  background: var(--bg-surface);
  color: var(--text-primary);
  padding: 10px;
}

.code-editor {
  height: calc(100vh - 400px);
  min-height: 500px;
  border-radius: 16px;
  overflow: hidden;
}

/* 头部操作按钮 */
.header-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  align-items: center;
}

.editor-actions {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  align-items: center;
}

.glass-btn {
  background: var(--glass-bg-medium);
  backdrop-filter: blur(15px);
  border: 1px solid var(--border-glass);
  color: var(--text-primary);
  padding: 8px 12px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 0.85rem;
  font-weight: 600;
  text-shadow: var(--text-shadow-light);
  white-space: nowrap;
  min-width: fit-content;
}

.glass-btn.btn-small {
  padding: 6px 10px;
  font-size: 0.8rem;
  gap: 4px;
}

.glass-btn.btn-small svg {
  width: 14px;
  height: 14px;
}

.glass-btn:hover {
  background: var(--surface-2);
  border-color: rgba(99, 102, 241, 0.4);
  transform: translateY(-2px);
  box-shadow: 0 6px 15px rgba(0, 0, 0, 0.2);
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .templates-layout {
    grid-template-columns: 1fr;
    gap: 15px;
    height: auto;
  }

  .template-item {
    padding: 15px;
    margin-bottom: 10px;
  }

  .template-meta {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .header-actions,
  .editor-actions {
    flex-wrap: wrap;
    gap: 8px;
  }

  .glass-btn {
    padding: 8px 12px;
    font-size: 0.85rem;
  }

  .form-label {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }

  .code-editor {
    height: 300px;
  }
}
</style>

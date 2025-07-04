<template>
  <div id="app">
    <!-- Header -->
    <div class="app-header">
      <div class="header-content">
        <div class="logo-section">
          <div class="logo-icon">
            <img :src="logoPath" alt="PRISM Logo" width="40" height="40" />
          </div>
          <div class="title-group">
            <h1>PRISM</h1>
            <p class="subtitle">Platform for Research Infrastructure Smart Manufacturing</p>
          </div>
        </div>
      </div>
      <div class="header-tabs">
        <button
          class="tab-btn wide-tab"
          :class="{ active: activeMainTab === 'home' }"
          @click="activeMainTab = 'home'"
        >
          <svg class="tab-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" fill="currentColor"/>
          </svg>
          <span class="tab-text">Program Generator</span>
        </button>
        <button
          class="tab-btn wide-tab"
          :class="{ active: activeMainTab === 'templates' }"
          @click="activeMainTab = 'templates'"
        >
          <svg class="tab-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
          </svg>
          <span class="tab-text">Template Manager</span>
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="main-container">
      <!-- Generator Tab -->
      <div v-if="activeMainTab === 'home'" class="generator-view">
        <div class="page-header">
          <h2 class="page-title">
            <svg class="page-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
            </svg>
            <span>Smart Manufacturing Hub</span>
          </h2>
          <p class="page-description">Upload Excel metadata, configure templates, and manufacture standardized research programs</p>
        </div>

        <div class="content-grid">
          <!-- Left Column -->
          <div class="left-column">
            <!-- Upload Section -->
            <div class="section-card upload-section">
              <div class="section-header">
                <h3 class="section-title">
                  <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8C22,6.89 21.1,6 20,6H12L10,4Z" fill="currentColor"/>
                  </svg>
                  <span>Upload Excel File</span>
                </h3>
              </div>
              <div class="section-body">
                <div class="upload-zone" :class="{ uploading: uploading }">
                  <input
                    type="file"
                    @change="handleExcelUpload"
                    accept=".xlsx,.xls"
                    :disabled="uploading"
                    id="file-input"
                    class="file-input"
                  />
                  <label for="file-input" class="upload-label">
                    <div class="upload-content">
                      <div class="upload-visual">
                        <svg class="upload-icon" width="32" height="32" viewBox="0 0 24 24" fill="none">
                          <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                        </svg>
                        <div class="upload-text">
                          <span v-if="uploading" class="uploading-text">
                            <span class="spinner-small"></span>
                            <span class="uploading-label">Processing file...</span>
                          </span>
                          <span v-else class="upload-prompt">
                            <strong class="upload-main">Click to upload file</strong>
                            <span class="upload-sub">or drag and drop file here</span>
                            <small class="upload-hint">Supports Excel files (.xlsx, .xls)</small>
                          </span>
                        </div>
                      </div>
                    </div>
                  </label>
                </div>
              </div>
            </div>

            <!-- Data Preview -->
            <div v-if="hasSelectedSheets" class="section-card data-section">
              <div class="section-header">
                <h3 class="section-title">
                  <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19Z" fill="currentColor"/>
                  </svg>
                  <span>Data Preview</span>
                </h3>
                <div class="sheet-selector-container" v-if="selectedSheets.length > 1">
                  <label class="sheet-label">Current Worksheet:</label>
                  <select v-model="activeSheet" @change="onSheetChange" class="sheet-select">
                    <option v-for="sheet in selectedSheets" :key="sheet" :value="sheet">
                      {{ sheet }}
                    </option>
                  </select>
                </div>
              </div>

              <!-- Data Stats -->
              <div class="data-stats" v-if="currentSheetData.length > 0">
                <div class="stat-card">
                  <svg class="stat-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z" fill="currentColor"/>
                  </svg>
                  <div class="stat-content">
                    <div class="stat-number">{{ currentSheetData.length }}</div>
                    <div class="stat-label">Total Records</div>
                  </div>
                </div>
                <div class="stat-card">
                  <svg class="stat-icon" width="16" height="16" viewBox="0 0 24 24" fill="none">
                    <path d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z" fill="currentColor"/>
                  </svg>
                  <div class="stat-content">
                    <div class="stat-number">{{ selectedDataCount }}</div>
                    <div class="stat-label">Selected</div>
                  </div>
                </div>
              </div>

              <!-- Table -->
              <div class="table-container">
                <div v-if="currentSheetData.length === 0" class="no-data">
                  <svg class="no-data-icon" width="48" height="48" viewBox="0 0 24 24" fill="none">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                  </svg>
                  <p>No data available in selected sheet</p>
                </div>
                <div v-else class="table-wrapper">
                  <table class="data-table" :class="{ 'tlf-table': showOutputNameColumn }">
                    <thead>
                      <tr>
                        <th class="checkbox-col">
                          <div class="checkbox-wrapper">
                            <input
                              type="checkbox"
                              :checked="isAllSelected"
                              @change="toggleSelectAll"
                              class="checkbox-input"
                            />
                            <span class="checkbox-custom"></span>
                          </div>
                        </th>
                        <th class="dataset-col">{{ firstColumnName }}</th>
                        <th v-if="showOutputNameColumn" class="output-name-col">Output Name</th>
                        <th class="program-col">{{ programColumnName }}</th>
                        <th class="programmer-col">{{ programmerColumnName }}</th>
                      </tr>
                    </thead>
                    <tbody>
                      <tr
                        v-for="(item, index) in currentSheetData"
                        :key="index"
                        :class="{ selected: selectedDataIndices.has(index) }"
                        @click="toggleDataSelection(index)"
                        class="data-row"
                      >
                        <td class="checkbox-col">
                          <div class="checkbox-wrapper">
                            <input
                              type="checkbox"
                              :checked="selectedDataIndices.has(index)"
                              @change.stop="toggleDataSelection(index)"
                              class="checkbox-input"
                            />
                            <span class="checkbox-custom"></span>
                          </div>
                        </td>
                        <td class="dataset-cell">
                          <div class="dataset-badge">{{ getDisplayContent(item) }}</div>
                        </td>
                        <td v-if="showOutputNameColumn" class="output-name-cell">{{ getOutputName(item) }}</td>
                        <td class="program-cell">{{ getProgramName(item) }}</td>
                        <td class="programmer-cell">{{ getProgrammer(item) }}</td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          <!-- Right Column -->
          <div class="right-column">
            <!-- Generation Controls -->
            <div v-if="hasSelectedSheets" class="section-card generation-section">
              <div class="section-header">
                <h3 class="section-title">
                  <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
                  </svg>
                  <span>Program Configuration</span>
                </h3>
              </div>

              <div class="config-form">
                <div class="form-group">
                  <label class="form-label">Output Type</label>
                  <div class="radio-group">
                    <label class="radio-option">
                      <input type="radio" value="production" v-model="outputType" @change="onOutputTypeChange" />
                      <span class="radio-label">Production Program</span>
                    </label>
                    <label class="radio-option">
                      <input type="radio" value="validation" v-model="outputType" @change="onOutputTypeChange" />
                      <span class="radio-label">Validation Program</span>
                    </label>
                  </div>
                </div>

                <div class="form-group">
                  <label class="form-label">
                    Template
                    <button @click="refreshTemplates" class="refresh-btn" title="Refresh templates from Template Manager">
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
                        <path d="M17.65,6.35C16.2,4.9 14.21,4 12,4A8,8 0 0,0 4,12A8,8 0 0,0 12,20C15.73,20 18.84,17.45 19.73,14H17.65C16.83,16.33 14.61,18 12,18A6,6 0 0,1 6,12A6,6 0 0,1 12,6C13.66,6 15.14,6.69 16.22,7.78L13,11H20V4L17.65,6.35Z" fill="currentColor"/>
                      </svg>
                    </button>
                  </label>
                  <select v-model="selectedTemplate" class="form-select">
                    <option value="">Default Template</option>
                    <option v-for="template in availableTemplates" :key="template.value" :value="template.value">
                      {{ template.label }}
                    </option>
                  </select>
                  <div v-if="selectedTemplate" class="template-info">
                    <small>{{ getTemplateName(selectedTemplate) }}</small>
                  </div>
                  <div v-if="availableTemplates.length === 0" class="no-templates-hint">
                    <small>No templates available for {{ outputType }} type. Go to Template Manager to create or import templates.</small>
                  </div>
                </div>

                <div class="action-section">
                  <button
                    @click="generatePrograms"
                    :disabled="generating || selectedDataItems.length === 0"
                    class="generate-btn"
                  >
                    <span v-if="generating">
                      Generating... {{ progress }}%
                    </span>
                    <span v-else>
                      Generate Programs ({{ selectedDataItems.length }})
                    </span>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Templates Tab -->
      <div v-else-if="activeMainTab === 'templates'" class="templates-view">
        <TemplateManager @template-action="refreshTemplates" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useProgramStore } from './stores/templateStore';
import { TemplateStorageService, type Template } from './services/TemplateStorageService';
import TemplateManager from './components/TemplateManager.vue';

const programStore = useProgramStore();
const templateService = new TemplateStorageService();

// 主要状态
const activeMainTab = ref('home');
const uploading = ref(false);
const showSheetDialog = ref(false);
const availableSheets = ref<string[]>([]);
const selectedSheets = ref<string[]>([]);
const activeSheet = ref('');
const generating = ref(false);
const progress = ref(0);

// 程序生成相关
const outputType = ref<'production' | 'validation'>('production');
const selectedTemplate = ref('');
const selectedDataIndices = ref<Set<number>>(new Set());

// 从模板管理器获取的模板列表
const managedTemplates = ref<Template[]>([]);

// 计算可用模板 - 根据输出类型过滤
const availableTemplates = computed(() => {
  const outputTypeFilter = outputType.value === 'production' ? 'Production' : 'Validation';

  return managedTemplates.value
    .filter(template => template.type === outputTypeFilter || template.type === 'Custom')
    .map(template => ({
      value: template.id,
      label: template.name,
      description: template.description,
      template: template
    }));
});

// 计算属性
const hasSelectedSheets = computed(() => selectedSheets.value.length > 0);

// Logo路径计算 - 考虑生产环境的base路径
const logoPath = computed(() => {
  const basePath = import.meta.env.BASE_URL || '/';
  return `${basePath}prism-logo.svg`;
});

const currentSheetData = computed(() => {
  if (!activeSheet.value) return [];
  return programStore.filteredData || [];
});

const selectedDataCount = computed(() => selectedDataIndices.value.size);

const isAllSelected = computed(() => {
  if (currentSheetData.value.length === 0) return false;
  return selectedDataIndices.value.size === currentSheetData.value.length;
});

const selectedDataItems = computed(() => {
  return Array.from(selectedDataIndices.value)
    .map(index => currentSheetData.value[index])
    .filter(Boolean);
});

// 动态列名计算
const firstColumnName = computed(() => {
  if (currentSheetData.value.length > 0 && currentSheetData.value[0]?.hasTitle) {
    return 'Title';  // 改为Title
  }
  return 'Dataset';
});

// 是否显示Output Name列
const showOutputNameColumn = computed(() => {
  return currentSheetData.value.length > 0 && currentSheetData.value[0]?.hasTitle;
});

const programColumnName = computed(() => {
  return outputType.value === 'production' ? 'Program' : 'QC Program';
});

const programmerColumnName = computed(() => {
  return outputType.value === 'production' ? 'Programmer' : 'QC Programmer';
});

// 初始化时加载模板
onMounted(async () => {
  try {
    await loadManagedTemplates();
  } catch (error) {
    console.warn('Failed to load templates:', error);
  }
});

// 加载模板管理器中的模板
async function loadManagedTemplates() {
  try {
    managedTemplates.value = await templateService.getAllTemplates();
    console.log('✅ 已加载模板:', managedTemplates.value.length);
  } catch (error) {
    console.error('❌ 加载模板失败:', error);
    managedTemplates.value = [];
  }
}

// 监听输出类型变化，重新选择适当的模板
function onOutputTypeChange() {
  // 如果当前选择的模板不适用于新的输出类型，清空选择
  if (selectedTemplate.value) {
    const currentTemplate = managedTemplates.value.find(t => t.id === selectedTemplate.value);
    const newOutputType = outputType.value === 'production' ? 'Production' : 'Validation';

    if (currentTemplate && currentTemplate.type !== newOutputType && currentTemplate.type !== 'Custom') {
      selectedTemplate.value = '';
    }
  }
}

// 方法
async function handleExcelUpload(event: Event) {
  const files = (event.target as HTMLInputElement).files;
  if (!files || files.length === 0) return;

  console.log('Starting file upload:', files[0].name);
  uploading.value = true;

  try {
    const sheetNames = await programStore.processExcelFile(files[0]);
    availableSheets.value = sheetNames;
    selectedSheets.value = [...sheetNames];

    // 自动选择第一个工作表并显示数据
    if (sheetNames.length > 0) {
      activeSheet.value = sheetNames[0];
      programStore.selectSheet(activeSheet.value);
    }
  } catch (error) {
    console.error('Error processing Excel file:', error);
    alert('Error processing Excel file: ' + (error as Error).message);
  } finally {
    uploading.value = false;
  }
}

function onSheetChange() {
  programStore.selectSheet(activeSheet.value);
  selectedDataIndices.value.clear(); // 清空选择
}

function confirmSheetSelection() {
  programStore.selectSheets(selectedSheets.value);
  showSheetDialog.value = false;
  activeSheet.value = selectedSheets.value[0] || '';
  if (activeSheet.value) {
    programStore.selectSheet(activeSheet.value);
  }
}

function selectAllSheets() {
  selectedSheets.value = [...availableSheets.value];
}

function deselectAllSheets() {
  selectedSheets.value = [];
}

function toggleSelectAll() {
  if (isAllSelected.value) {
    selectedDataIndices.value.clear();
  } else {
    selectedDataIndices.value = new Set(Array.from({ length: currentSheetData.value.length }, (_, i) => i));
  }
}

function toggleDataSelection(index: number) {
  if (selectedDataIndices.value.has(index)) {
    selectedDataIndices.value.delete(index);
  } else {
    selectedDataIndices.value.add(index);
  }
}

function getProgramName(item: any) {
  return outputType.value === 'production' ? (item.prodProgram || '-') : (item.valProgram || '-');
}

function getProgrammer(item: any) {
  return outputType.value === 'production' ? (item.prodProgrammer || '-') : (item.valProgrammer || '-');
}

function getTemplateName(templateId: string) {
  const template = managedTemplates.value.find(t => t.id === templateId);
  return template ? template.name : 'Unknown Template';
}

// 获取显示内容的函数
function getDisplayContent(item: any) {
  if (item.hasTitle && item.outputType && item.outputNumber && item.outputTitle) {
    // TLF类型数据：拼接 Output Type + Output # + Title
    const parts = [item.outputType, item.outputNumber, item.outputTitle].filter(part => part && part.length > 0);
    return parts.join(' ');
  }
  // 普通数据或TLF数据缺少字段时，返回domain
  return item.domain || '-';
}

// 获取Output Name的函数
function getOutputName(item: any) {
  return item.outputName || '-';
}

async function generatePrograms() {
  console.log('=== Starting program generation ===');

  if (selectedDataItems.value.length === 0) {
    alert('Please select datasets to generate programs');
    return;
  }

  // 弹窗让用户输入ZIP文件名
  const defaultZipName = `ADaM_Programs_${outputType.value === 'production' ? 'Production' : 'Validation'}`;
  const zipName = prompt('Please enter the ZIP file name (without .zip extension):', defaultZipName);

  // 如果用户取消或输入空值，则退出
  if (zipName === null || zipName.trim() === '') {
    return;
  }

  const sanitizedZipName = zipName.trim().replace(/[<>:"/\\|?*]/g, '_'); // 清理文件名中的非法字符

  try {
    generating.value = true;
    progress.value = 0;

    const { default: ProgramGenerator } = await import('./services/ProgramGenerator');
    const generator = new ProgramGenerator();

    const finalOutputType = outputType.value === 'production' ? 'Production' : 'Validation';

    // 使用选中的模板内容
    if (selectedTemplate.value) {
      const selectedTemplateObj = managedTemplates.value.find(t => t.id === selectedTemplate.value);
      if (selectedTemplateObj && selectedTemplateObj.content) {
        console.log('Using template:', selectedTemplateObj.name);
        generator.setTemplate(selectedTemplateObj.content);
      }
    }

    await generator.generateZip(
      selectedDataItems.value,
      finalOutputType,
      sanitizedZipName, // 传递自定义的ZIP名称
      (p) => {
        progress.value = Math.round(p);
      }
    );

    alert('Program generation completed! Please check your downloads folder.');
  } catch (error) {
    console.error('Error generating programs:', error);
    alert('Error generating programs: ' + (error as Error).message);
  } finally {
    generating.value = false;
    progress.value = 0;
  }
}

// 暴露方法供模板管理器调用，实现联动
function refreshTemplates() {
  loadManagedTemplates();
}

// 当用户切换到模板标签时刷新模板列表
function onTabChange(tab: string) {
  activeMainTab.value = tab;
  if (tab === 'home') {
    // 切换回程序生成器时刷新模板��表
    loadManagedTemplates();
  }
}
</script>

<style scoped>
/* Tab样式 - 高优先级覆盖 */
.header-tabs {
  display: flex;
  gap: 0;
  margin-top: 1rem;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
  padding: 4px;
  backdrop-filter: blur(10px);
  justify-content: center;
  max-width: 600px; /* 限制最大宽度 */
  margin-left: auto;
  margin-right: auto;
}

.tab-btn.wide-tab {
  flex: 1;
  background: none !important;
  border: none !important;
  color: rgba(255, 255, 255, 0.8) !important;
  padding: 1.2rem 3rem !important; /* 增加更多内边距 */
  border-radius: 10px !important;
  cursor: pointer !important;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.75rem !important; /* 增加图标和文字间距 */
  font-size: 1.1rem !important; /* 增大字体 */
  font-weight: 600 !important; /* 增加字重 */
  min-width: 200px !important; /* 设置更大的最小宽度 */
  white-space: nowrap !important;
}

.tab-btn.wide-tab:hover {
  color: white !important;
  background: rgba(255, 255, 255, 0.15) !important;
  transform: translateY(-1px) !important;
}

.tab-btn.wide-tab.active {
  background: rgba(255, 255, 255, 0.25) !important;
  color: white !important;
  font-weight: 700 !important;
  backdrop-filter: blur(10px) !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1) !important;
}

.tab-icon {
  color: currentColor !important;
  width: 22px !important; /* 稍微增大图标 */
  height: 22px !important;
}

.tab-text {
  font-size: inherit !important;
  font-weight: inherit !important;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .tab-btn.wide-tab {
    padding: 1rem 2rem !important;
    font-size: 1rem !important;
    min-width: 150px !important;
  }

  .header-tabs {
    max-width: 100%;
  }
}

/* Template selection styling */
.refresh-btn {
  background: none;
  border: none;
  color: #007bff;
  cursor: pointer;
  padding: 2px 4px;
  margin-left: 8px;
  border-radius: 4px;
  transition: all 0.2s ease;
  display: inline-flex;
  align-items: center;
}

.refresh-btn:hover {
  background: rgba(0, 123, 255, 0.1);
  color: #0056b3;
}

.refresh-btn svg {
  transition: transform 0.3s ease;
}

.refresh-btn:hover svg {
  transform: rotate(180deg);
}

.template-info {
  margin-top: 4px;
  color: #6c757d;
  font-style: italic;
}

.no-templates-hint {
  margin-top: 4px;
  color: #dc3545;
  font-style: italic;
}

.form-label {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* Table styling for TLF data */
.data-table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 1rem;
}

.data-table th,
.data-table td {
  padding: 0.75rem;
  text-align: left;
  border-bottom: 1px solid #e0e0e0;
  vertical-align: top;
}

.data-table th {
  background-color: #f8f9fa;
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
  position: sticky;
  top: 0;
  z-index: 10;
}

/* Column widths - different for TLF vs regular data */
.checkbox-col {
  width: 50px;
  text-align: center;
}

.dataset-col {
  width: 35%; /* Wider for TLF titles */
  min-width: 300px;
}

.output-name-col {
  width: 15%;
  min-width: 120px;
}

.program-col {
  width: 20%;
  min-width: 150px;
}

.programmer-col {
  width: 20%;
  min-width: 150px;
}

/* Adjust widths when Output Name column is not shown (regular ADaM data) */
.data-table:not(.tlf-table) .dataset-col {
  width: 25%;
  min-width: 200px;
}

.data-table:not(.tlf-table) .program-col {
  width: 30%;
}

.data-table:not(.tlf-table) .programmer-col {
  width: 30%;
}

/* Row styling */
.data-row {
  transition: background-color 0.2s ease;
  cursor: pointer;
}

.data-row:hover {
  background-color: #f8f9fa;
}

.data-row.selected {
  background-color: #e3f2fd;
}

.data-row.selected:hover {
  background-color: #bbdefb;
}

/* Cell content styling */
.dataset-cell, .output-name-cell, .program-cell, .programmer-cell {
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 0; /* Enable text wrapping */
}

.dataset-badge {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  background-color: #007bff;
  color: white;
  border-radius: 4px;
  font-size: 0.875rem;
  font-weight: 500;
  max-width: 100%;
  word-break: break-word;
}

/* Checkbox styling */
.checkbox-wrapper {
  display: flex;
  align-items: center;
  justify-content: center;
}

.checkbox-input {
  width: 18px;
  height: 18px;
  margin: 0;
  cursor: pointer;
}

.checkbox-custom {
  display: none; /* Use native checkbox for simplicity */
}

/* Table container */
.table-wrapper {
  max-height: 500px;
  overflow-y: auto;
  border: 1px solid #dee2e6;
  border-radius: 8px;
}

/* Responsive adjustments */
@media (max-width: 1200px) {
  .dataset-col {
    min-width: 250px;
  }

  .output-name-col {
    min-width: 100px;
  }

  .program-col,
  .programmer-col {
    min-width: 120px;
  }
}

@media (max-width: 768px) {
  .data-table th,
  .data-table td {
    padding: 0.5rem;
    font-size: 0.875rem;
  }

  .dataset-col {
    width: 40%;
    min-width: 200px;
  }

  .output-name-col {
    width: 20%;
    min-width: 80px;
  }

  .program-col,
  .programmer-col {
    width: 20%;
    min-width: 100px;
  }
}
</style>

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
            <h1 class="sparkle-text">PRISM</h1>
            <p class="subtitle">Platform for Research Infrastructure Smart Manufacturing</p>
          </div>
        </div>
      </div>
      <div class="header-tabs">
        <button
          class="tab-btn wide-tab"
          :class="{ active: activeMainTab === 'about' }"
          @click="activeMainTab = 'about'"
        >
          <svg class="tab-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
            <path d="M12,2C13.1,2 14,2.9 14,4C14,5.1 13.1,6 12,6C10.9,6 10,5.1 10,4C10,2.9 10.9,2 12,2M21,9V7L15,1H5C3.89,1 3,1.89 3,3V21A2,2 0 0,0 5,23H19A2,2 0 0,0 21,21V9M19,21H5V3H13V9H19V21Z" fill="currentColor"/>
          </svg>
          <span class="tab-text">项目介绍</span>
        </button>
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
      <!-- About Tab -->
      <div v-if="activeMainTab === 'about'" class="about-view">
        <div class="page-header glass-effect">
          <h2 class="page-title glow-text">
            <svg class="page-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12,2C13.1,2 14,2.9 14,4C14,5.1 13.1,6 12,6C10.9,6 10,5.1 10,4C10,2.9 10.9,2 12,2M21,9V7L15,1H5C3.89,1 3,1.89 3,3V21A2,2 0 0,0 5,23H19A2,2 0 0,0 21,21V9M19,21H5V3H13V9H19V21Z" fill="currentColor"/>
            </svg>
            <span class="sparkle-text">关于 PRISM</span>
          </h2>
          <p class="page-description">Platform for Research Infrastructure Smart Manufacturing</p>
        </div>

        <div class="about-content">
          <div class="about-section glass-effect">
            <div class="section-header">
              <h3 class="section-title glow-text">
                <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M11,16.5L6.5,12L7.91,10.59L11,13.67L16.59,8.09L18,9.5L11,16.5Z" fill="currentColor"/>
                </svg>
                <span class="sparkle-text">项目简介</span>
              </h3>
            </div>
            <div class="section-body">
              <p>PRISM (Platform for Research Infrastructure Smart Manufacturing) 是一个智能化的研究程序制造平台，专门为临床研究和生物统计学领域设计。</p>
              <p>该平台通过上传Excel元数据文件，自动化生成标准化的SAS研究程序，大幅提高工作效率并确保代码质量的一致性。</p>
            </div>
          </div>

          <div class="about-section glass-effect">
            <div class="section-header">
              <h3 class="section-title glow-text">
                <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12,2A2,2 0 0,1 14,4C14,5.33 13.67,6.5 13.07,7.43L17.5,9.5C17.83,9.67 18,10 18,10.36V11.64C18,12 17.83,12.33 17.5,12.5L13.07,14.57C13.67,15.5 14,16.67 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18C10,16.67 10.33,15.5 10.93,14.57L6.5,12.5C6.17,12.33 6,12 6,11.64V10.36C6,10 6.17,9.67 6.5,9.5L10.93,7.43C10.33,6.5 10,5.33 10,4A2,2 0 0,1 12,2M12,7A1,1 0 0,0 11,8A1,1 0 0,0 12,9A1,1 0 0,0 13,8A1,1 0 0,0 12,7M12,15A1,1 0 0,0 11,16A1,1 0 0,0 12,17A1,1 0 0,0 13,16A1,1 0 0,0 12,15Z" fill="currentColor"/>
                </svg>
                <span class="sparkle-text">核心功能</span>
              </h3>
            </div>
            <div class="section-body">
              <div class="features-grid">
                <div class="feature-card">
                  <div class="feature-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <h4>Excel数据处理</h4>
                  <p>智能解析Excel文件，自动识别数据结构和元数据信息</p>
                </div>
                <div class="feature-card">
                  <div class="feature-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <h4>程序自动生成</h4>
                  <p>基于模板自动生成Production和Validation程序</p>
                </div>
                <div class="feature-card">
                  <div class="feature-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <h4>模板管理</h4>
                  <p>创建、编辑和管理SAS程序����板，支持自定义模板</p>
                </div>
                <div class="feature-card">
                  <div class="feature-icon">
                    <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
                      <path d="M17,7H22V17H17V19A1,1 0 0,0 18,20H20V22H17.5C16.95,22 16,21.55 16,21C16,21.55 15.05,22 14.5,22H12V20H14A1,1 0 0,0 15,19V5A1,1 0 0,0 14,4H12V2H14.5C15.05,2 16,2.45 16,3C16,2.45 16.95,2 17.5,2H20V4H18A1,1 0 0,0 17,5V7M2,7H13V17H2V7M4,9V15H11V9H4Z" fill="currentColor"/>
                    </svg>
                  </div>
                  <h4>服务器集成</h4>
                  <p>直接上传生成的程序到服务器，支持冲突检测和处理</p>
                </div>
              </div>
            </div>
          </div>

          <div class="about-section glass-effect">
            <div class="section-header">
              <h3 class="section-title glow-text">
                <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2M17.5,12A1.5,1.5 0 0,1 16,13.5A1.5,1.5 0 0,1 14.5,12A1.5,1.5 0 0,1 16,10.5A1.5,1.5 0 0,1 17.5,12M10,11.5C10,10.12 8.88,9 7.5,9C6.12,9 5,10.12 5,11.5C5,12.88 6.12,14 7.5,14C8.88,14 10,12.88 10,11.5M12,15.5C10.62,15.5 9.5,16.62 9.5,18C9.5,19.38 10.62,20.5 12,20.5C13.38,20.5 14.5,19.38 14.5,18C14.5,16.62 13.38,15.5 12,15.5Z" fill="currentColor"/>
                </svg>
                <span class="sparkle-text">使用指南</span>
              </h3>
            </div>
            <div class="section-body">
              <div class="usage-steps">
                <div class="step-item">
                  <div class="step-number">1</div>
                  <div class="step-content">
                    <h4>上传Excel文件</h4>
                    <p>在Program Generator页面上传包含数据集元数据的Excel文件</p>
                  </div>
                </div>
                <div class="step-item">
                  <div class="step-number">2</div>
                  <div class="step-content">
                    <h4>数据预览与选择</h4>
                    <p>预览解析后的数据，选择需要生成程序的数据集</p>
                  </div>
                </div>
                <div class="step-item">
                  <div class="step-number">3</div>
                  <div class="step-content">
                    <h4>配置生成选项</h4>
                    <p>选择输出类型（Production/Validation）和相应的模板</p>
                  </div>
                </div>
                <div class="step-item">
                  <div class="step-number">4</div>
                  <div class="step-content">
                    <h4>生成或上传</h4>
                    <p>点击生成按钮下载ZIP文件，或直接上传到服务器</p>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div class="about-section glass-effect">
            <div class="section-header">
              <h3 class="section-title glow-text">
                <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                  <path d="M21,5V19C21,20.1 20.1,21 19,21H5C3.9,21 3,20.1 3,19V5C3,3.9 3.9,3 5,3H19C20.1,3 21,3.9 21,5M17,17H7V15H17V17M17,13H7V11H17V13M17,9H7V7H17V9Z" fill="currentColor"/>
                </svg>
                <span class="sparkle-text">技术特性</span>
              </h3>
            </div>
            <div class="section-body">
              <div class="tech-features">
                <div class="tech-item">
                  <strong>前端技术：</strong>Vue.js 3 + TypeScript + Vite
                </div>
                <div class="tech-item">
                  <strong>文件处理：</strong>支持Excel (.xlsx/.xls) 文件解析
                </div>
                <div class="tech-item">
                  <strong>模板引擎：</strong>动态SAS代码生成和变量替换
                </div>
                <div class="tech-item">
                  <strong>服务器支持：</strong>SSH文件传输和冲突检测
                </div>
                <div class="tech-item">
                  <strong>用户界面：</strong>现代化玻璃质感设计，响应式布局
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Generator Tab -->
      <div v-if="activeMainTab === 'home'" class="generator-view">
        <div class="page-header glass-effect">
          <h2 class="page-title glow-text">
            <svg class="page-icon" width="24" height="24" viewBox="0 0 24 24" fill="none">
              <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
            </svg>
            <span class="sparkle-text">Smart Manufacturing Hub</span>
          </h2>
          <p class="page-description">Upload Excel metadata, configure templates, and manufacture standardized research programs</p>
        </div>

        <div class="content-grid">
          <!-- Left Column -->
          <div class="left-column">
            <!-- Upload Section -->
            <div class="section-card upload-section glass-effect">
              <div class="section-header">
                <h3 class="section-title glow-text">
                  <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M10,4H4C2.89,4 2,4.89 2,6V18A2,2 0 0,0 4,20H20A2,2 0 0,0 22,18V8L14,2M18,20H6V4H13V9H18V20Z" fill="currentColor"/>
                  </svg>
                  <span class="sparkle-text">Upload Excel File</span>
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
            <div v-if="hasSelectedSheets" class="section-card data-section glass-effect">
              <div class="section-header">
                <h3 class="section-title glow-text">
                  <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M19,3H5C3.9,3 3,3.9 3,5V19C3,20.1 3.9,21 5,21H19C20.1,21 21,20.1 21,19V5C21,3.9 20.1,3 19,3M19,19H5V5H19V19Z" fill="currentColor"/>
                  </svg>
                  <span class="sparkle-text">Data Preview</span>
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
            <div v-if="hasSelectedSheets" class="section-card generation-section glass-effect">
              <div class="section-header">
                <h3 class="section-title glow-text">
                  <svg class="section-icon" width="20" height="20" viewBox="0 0 24 24" fill="none">
                    <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z" fill="currentColor"/>
                  </svg>
                  <span class="sparkle-text">Program Configuration</span>
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

                  <button
                    @click="uploadToServer"
                    :disabled="generating || selectedDataItems.length === 0"
                    class="upload-btn"
                  >
                    <span v-if="uploading">
                      Uploading... {{ uploadProgress }}%
                    </span>
                    <span v-else>
                      Upload to Server ({{ selectedDataItems.length }})
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

    <!-- Template Selection Dialog -->
    <TemplateSelectionDialog
      :visible="showTemplateSelectionDialog"
      :template-matches="templateMatches"
      :current-template-name="getTemplateName(selectedTemplate) || 'Default Template'"
      @confirm="onTemplateSelectConfirm"
      @cancel="showTemplateSelectionDialog = false"
    />

    <!-- Server Connection Dialog -->
    <ServerConnectionDialog
      :visible="showServerConnectionDialog"
      @close="showServerConnectionDialog = false"
      @connect="handleServerConnection"
    />

    <!-- Upload Progress Dialog -->
    <div v-if="showUploadProgress" class="upload-progress-dialog">
      <div class="dialog-content">
        <h3 class="dialog-title">Upload Progress</h3>
        <div class="progress-status">{{ uploadStatus }}</div>
        <div class="progress-bar-container">
          <div class="progress-bar" :style="{ width: `${uploadProgress}%` }"></div>
        </div>
        <div class="uploaded-files-info">
          Uploaded {{ uploadedFiles }} of {{ totalFiles }} files
        </div>
        <button @click="showUploadProgress = false" class="close-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19.77,4.23L4.23,19.77C3.84,20.17 3.84,20.83 4.23,21.23C4.63,21.63 5.29,21.63 5.69,21.23L21.23,5.69C21.63,5.29 21.63,4.63 21.23,4.23C20.83,3.84 20.17,3.84 19.77,4.23Z" fill="currentColor"/>
            <path d="M4.23,4.23C3.84,4.63 3.84,5.29 4.23,5.69L19.77,21.23C20.17,21.63 20.83,21.63 21.23,21.23C21.63,20.83 21.63,20.17 21.23,19.77L5.69,4.23C5.29,3.84 4.63,3.84 4.23,4.23Z" fill="currentColor"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- Upload Complete Notification -->
    <div v-if="showUploadCompleteNotification" class="upload-complete-notification">
      <div class="notification-content">
        <div class="notification-icon">✓</div>
        <div class="notification-message">File upload completed successfully!</div>
        <button @click="showUploadCompleteNotification = false" class="notification-close-btn">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none">
            <path d="M19.77,4.23L4.23,19.77C3.84,20.17 3.84,20.83 4.23,21.23C4.63,21.63 5.29,21.63 5.69,21.23L21.23,5.69C21.63,5.29 21.63,4.63 21.23,4.23C20.83,3.84 20.17,3.84 19.77,4.23Z" fill="currentColor"/>
            <path d="M4.23,4.23C3.84,4.63 3.84,5.29 4.23,5.69L19.77,21.23C20.17,21.63 20.83,21.63 21.23,21.23C21.63,20.83 21.63,20.17 21.23,19.77L5.69,4.23C5.29,3.84 4.63,3.84 4.23,4.23Z" fill="currentColor"/>
          </svg>
        </button>
      </div>
    </div>

    <!-- File Conflict Dialog -->
    <FileConflictDialog
      :visible="showFileConflictDialog"
      :conflicts="fileConflicts"
      @resolve="handleConflictResolution"
      @close="showFileConflictDialog = false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue';
import { useProgramStore } from './stores/templateStore';
import { TemplateStorageService, type Template } from './services/TemplateStorageService';
import { referenceTemplateService, type TemplateMatch } from './services/ReferenceTemplateService';
import TemplateManager from './components/TemplateManager.vue';
import TemplateSelectionDialog from './components/TemplateSelectionDialog.vue';
import ServerConnectionDialog from './components/ServerConnectionDialog.vue';
import FileConflictDialog from './components/FileConflictDialog.vue';

// 导入模拟服务器API
import './services/MockServerAPI';
import { serverFileManager, type FileConflict, type ConflictResolution } from './services/ServerFileManager';


const programStore = useProgramStore();
const templateService = new TemplateStorageService();

// 主要状态
const activeMainTab = ref('about');
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

// 服务器上传相关状态
const showServerConnectionDialog = ref(false);
const uploadProgress = ref(0);
const isUploading = ref(false);
const showUploadProgress = ref(false); // 新增：显��上传进度对话框
const uploadStatus = ref(''); // 新增：上传状态消息
const uploadedFiles = ref(0); // 新增：已上传文件数
const totalFiles = ref(0); // 新增：总文件数
const showUploadCompleteNotification = ref(false); // 新增：显示上传完成通知

// 从模板管理器获取的模板列表
const managedTemplates = ref<Template[]>([]);

// 新增：备用模板相关状态
const showTemplateSelectionDialog = ref(false);
const templateMatches = ref<TemplateMatch[]>([]);
const pendingGenerationData = ref<{
  items: any[];
  outputType: 'production' | 'validation';
  zipName?: string;
  generalTemplateName?: string;
}>({ items: [], outputType: 'production' });

// 新增：待上传数据状态
const pendingUploadData = ref<{
  items: any[];
  outputType: 'production' | 'validation';
  connectionInfo?: any;
  generalTemplateName?: string;
}>({ items: [], outputType: 'production' });

// 文件冲突相关状态
const showFileConflictDialog = ref(false);
const fileConflicts = ref<FileConflict[]>([]);

// ���算可用模板 - 根据输出类型过滤
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

// Logo路径计算 - 考虑生产环境的base���径
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
    // 加载引用模板
    await referenceTemplateService.loadReferenceTemplates();
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

// 刷新模板列表
async function refreshTemplates() {
  try {
    await loadManagedTemplates();
    console.log('Templates refreshed successfully');
  } catch (error) {
    console.error('Failed to refresh templates:', error);
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

    // 自��选择第一个工作表并显示数据
    if (sheetNames.length > 0) {
      activeSheet.value = sheetNames[0];
      programStore.selectSheet(activeSheet.value);
    }

    // 显示上传完成通知
    showUploadCompleteNotification.value = true;
  } catch (error) {
    console.error('Error processing Excel file:', error);
    alert('Error processing Excel file: ' + (error as Error).message);
  } finally {
    uploading.value = false;
  }
}

function onSheetChange() {
  programStore.selectSheet(activeSheet.value);
  selectedDataIndices.value.clear(); // ���空选���
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
    // 如果当前全选，则取消全选
    selectedDataIndices.value.clear();
  } else {
    // 如果当前未全选，则全选所有
    selectedDataIndices.value = new Set(Array.from({ length: currentSheetData.value.length }, (_, i) => i));
  }
  console.log('Toggle select all:', selectedDataIndices.value.size, 'items selected');
}

function toggleDataSelection(index: number) {
  if (selectedDataIndices.value.has(index)) {
    selectedDataIndices.value.delete(index);
  } else {
    selectedDataIndices.value.add(index);
  }
  console.log('Toggle row', index, '- Total selected:', selectedDataIndices.value.size);
}

// 添加全选所有数据的方法
function selectAllData() {
  selectedDataIndices.value = new Set(Array.from({ length: currentSheetData.value.length }, (_, i) => i));
  console.log('Select all data:', selectedDataIndices.value.size, 'items selected');
}

// 添加取消全选的方法
function deselectAllData() {
  selectedDataIndices.value.clear();
  console.log('Deselect all data');
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
    // TLF类型数据��拼接 Output Type + Output # + Title
    const parts = [item.outputType, item.outputNumber, item.outputTitle].filter(part => part && part.length > 0);
    return parts.join(' ');
  }
  // 普通数据���TLF数���缺少字段时，返回domain
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

  try {
    // 首先检测引用模板匹配，不需要ZIP文件名
    const programNames = selectedDataItems.value
      .map(item => outputType.value === 'production' ? item.prodProgram : item.valProgram)
      .filter((name): name is string => name != null && name.trim() !== '');

    // 获取当前选择的通用模板名称
    const currentTemplateName = selectedTemplate.value
      ? getTemplateName(selectedTemplate.value)
      : 'Default Template';

    console.log('Checking for reference template matches...');
    const matches = referenceTemplateService.getTemplateMatches(programNames, 'sdtm');
    const hasMatches = matches.some(match => match.matchedTemplate !== null);

    if (hasMatches) {
      // 发现匹配的引用模板，先显示模板选择对话框
      console.log('Found matching reference templates, showing selection dialog');
      templateMatches.value = matches;
      pendingGenerationData.value = {
        items: selectedDataItems.value,
        outputType: outputType.value,
        generalTemplateName: currentTemplateName
      };
      showTemplateSelectionDialog.value = true;
    } else {
      // 没��匹配的引用模板，直接询问ZIP文件名然后生成
      console.log('No matching reference templates found, asking for ZIP name');
      const defaultZipName = `ADaM_Programs_${outputType.value === 'production' ? 'Production' : 'Validation'}`;
      const zipName = prompt('Please enter the ZIP file name (without .zip extension):', defaultZipName);

      if (zipName === null || zipName.trim() === '') {
        return;
      }

      const sanitizedZipName = zipName.trim().replace(/[<>:"/\\|?*]/g, '_');
      await executeGeneration(selectedDataItems.value, outputType.value, sanitizedZipName);
    }
  } catch (error) {
    console.error('Error in program generation:', error);
    alert('Error generating programs: ' + (error as Error).message);
  }
}

// 新增：实际执行生成的方法
async function executeGeneration(items: any[], outputTypeValue: string, zipName?: string) {
  const defaultZipName = `ADaM_Programs_${outputTypeValue === 'production' ? 'Production' : 'Validation'}`;
  const finalZipName = zipName || defaultZipName;

  try {
    generating.value = true;
    progress.value = 0;

    const { default: ProgramGenerator } = await import('./services/ProgramGenerator');
    const generator = new ProgramGenerator();

    const finalOutputType = outputTypeValue === 'production' ? 'Production' : 'Validation';

    // 使用选中的通用模板内容
    if (selectedTemplate.value) {
      const selectedTemplateObj = managedTemplates.value.find(t => t.id === selectedTemplate.value);
      if (selectedTemplateObj && selectedTemplateObj.content) {
        console.log('Using general template:', selectedTemplateObj.name);
        generator.setTemplate(selectedTemplateObj.content);
      }
    }

    await generator.generateZip(
      items,
      finalOutputType,
      finalZipName,
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

// 新增：模板选择相关方法
async function onTemplateSelectConfirm(matches: TemplateMatch[]) {
  console.log('Template selection confirmed:', matches);

  // 检查是否为上传操作
  const isUploadOperation = pendingUploadData.value.items.length > 0;

  if (isUploadOperation) {
    // 处理上传操作的模板选择
    const updatedItems = pendingUploadData.value.items.map(item => {
      const programName = pendingUploadData.value.outputType === 'production'
        ? item.prodProgram
        : item.valProgram;

      const match = matches.find(m => m.programName === programName);
      if (match && match.useReference && match.matchedTemplate) {
        return {
          ...item,
          useReferenceTemplate: true,
          referenceTemplatePath: match.matchedTemplate.path,
          referenceTemplateContent: match.matchedTemplate.content
        };
      }

      return {
        ...item,
        useReferenceTemplate: false
      };
    });

    // 关闭对话框
    showTemplateSelectionDialog.value = false;

    // 将更新后的项目存储回待上传数���
    pendingUploadData.value.items = updatedItems;

    // 显示服务器连接对话框
    showServerConnectionDialog.value = true;
  } else {
    // 处理生成操作的模板选择（原有逻辑）
    const updatedItems = pendingGenerationData.value.items.map(item => {
      const programName = pendingGenerationData.value.outputType === 'production'
        ? item.prodProgram
        : item.valProgram;

      const match = matches.find(m => m.programName === programName);
      if (match && match.useReference && match.matchedTemplate) {
        return {
          ...item,
          useReferenceTemplate: true,
          referenceTemplatePath: match.matchedTemplate.path,
          referenceTemplateContent: match.matchedTemplate.content
        };
      }

      return {
        ...item,
        useReferenceTemplate: false
      };
    });

    // 关闭对话框
    showTemplateSelectionDialog.value = false;

    // 现在询问ZIP文件名，然后执行生成
    const defaultZipName = `ADaM_Programs_${pendingGenerationData.value.outputType === 'production' ? 'Production' : 'Validation'}`;
    const zipName = prompt('Please enter the ZIP file name (without .zip extension):', defaultZipName);

    if (zipName === null || zipName.trim() === '') {
      return;
    }

    const sanitizedZipName = zipName.trim().replace(/[<>:"/\\|?*]/g, '_');

    // 执行实际的程序生成
    await executeGeneration(updatedItems, pendingGenerationData.value.outputType, sanitizedZipName);
  }
}

// 新增：上传到服务器的方法
async function uploadToServer() {
  console.log('=== Starting server upload ===');

  if (selectedDataItems.value.length === 0) {
    alert('Please select datasets to upload programs');
    return;
  }

  try {
    // 首先检测引用模板匹配���类似于generatePrograms
    const programNames = selectedDataItems.value
      .map(item => outputType.value === 'production' ? item.prodProgram : item.valProgram)
      .filter((name): name is string => name != null && name.trim() !== '');

    // 获取当前选择的通用模板名称
    const currentTemplateName = selectedTemplate.value
      ? getTemplateName(selectedTemplate.value)
      : 'Default Template';

    console.log('Checking for reference template matches for upload...');
    const matches = referenceTemplateService.getTemplateMatches(programNames, 'sdtm');
    const hasMatches = matches.some(match => match.matchedTemplate !== null);

    if (hasMatches) {
      // 发现匹配的引用模板，先显示模板选择��话框
      console.log('Found matching reference templates for upload, showing selection dialog');
      templateMatches.value = matches;
      pendingUploadData.value = {
        items: selectedDataItems.value,
        outputType: outputType.value,
        generalTemplateName: currentTemplateName
      };
      showTemplateSelectionDialog.value = true;
    } else {
      // 没有匹配的引用模板，直接显示服务器连接弹窗
      console.log('No matching reference templates found for upload, showing server connection dialog');
      showServerConnectionDialog.value = true;
    }
  } catch (error) {
    console.error('Error in upload to server:', error);
    alert('Error preparing upload: ' + (error as Error).message);
  }
}

// 新增：处理服���器连��
async function handleServerConnection(connectionInfo: any) {
  console.log('Server connection info:', connectionInfo);

  try {
    // 删除原本关闭连接弹窗的代码，保���文件选择窗口

    // 显示上传进度对话框
    showUploadProgress.value = true;
    uploadProgress.value = 0;
    uploadStatus.value = '连接服务器...';
    uploadedFiles.value = 0;
    totalFiles.value = 0;

    // 检查是否需要重新连接服务器
    let connected = false;
    if (serverFileManager.isServerConnected() &&
        serverFileManager.getConnection()?.host === connectionInfo.host &&
        serverFileManager.getConnection()?.username === connectionInfo.username) {
      // 如果已经连接到相同的服务器，则跳过连接步骤
      console.log('使用现有的服务器连接');
      connected = true;
    } else {
      // 连接到服务器
      connected = await serverFileManager.connect(connectionInfo);
    }

    if (!connected) {
      uploadStatus.value = '连接服务器失败';
      alert('连接服务器失败，请检查连接信息');
      showUploadProgress.value = false;
      return;
    }

    uploadStatus.value = '生成程序文件...';

    // 生成程序文件（不打包）
    const { default: ProgramGenerator } = await import('./services/ProgramGenerator');
    const generator = new ProgramGenerator();

    const finalOutputType = outputType.value === 'production' ? 'Production' : 'Validation';

    // ��用选中的通用模板内容
    if (selectedTemplate.value) {
      const selectedTemplateObj = managedTemplates.value.find(t => t.id === selectedTemplate.value);
      if (selectedTemplateObj && selectedTemplateObj.content) {
        console.log('Using general template:', selectedTemplateObj.name);
        generator.setTemplate(selectedTemplateObj.content);
      }
    }

    // 决定使用哪些数据项 - 如果有pending upload data则使用，否则使用当前选择的数据项
    const itemsToUpload = pendingUploadData.value.items.length > 0
      ? pendingUploadData.value.items
      : selectedDataItems.value;

    console.log('Using items for upload:', itemsToUpload.length, 'items');

    // 生成所有程序文件
    const programFiles = await generator.generateFiles(
      itemsToUpload,
      finalOutputType,
      (p) => {
        uploadProgress.value = Math.round(p * 0.4); // 生成占40%进度
        uploadStatus.value = `生成程序文件... ${Math.round(p)}%`;
      }
    );

    // 检查文件冲突
    uploadStatus.value = '正在检查文件冲突，请稍候...';
    uploadProgress.value = 40;

    const filesToUpload = programFiles.map(file => ({
      file: new File([new Blob([file.content], { type: 'text/plain' })], file.name, { type: 'text/plain' }),
      remotePath: `${connectionInfo.remotePath}/${file.name}`
    }));

    // 添加一些延迟来让用户看到检查状态
    uploadStatus.value = `正在检查 ${filesToUpload.length} 个文件的冲突状态...`;
    await new Promise(resolve => setTimeout(resolve, 500)); // 0.5秒延迟让用户看到状态

    const conflicts = await serverFileManager.checkFileConflicts(filesToUpload);

    if (conflicts.length > 0) {
      // 发现文件冲突，更新状态并显示冲突选择对话框
      uploadStatus.value = `发现 ${conflicts.length} 个文件冲突，请在������窗口中选择处理方式...`;
      uploadProgress.value = 45;

      // 稍等一下让用户看到提示信息
      await new Promise(resolve => setTimeout(resolve, 1000));

      showUploadProgress.value = false; // 隐藏进度对话框

      fileConflicts.value = conflicts;
      showFileConflictDialog.value = true;

      // 等待用户选择，函数在这里暂停
      return;
    } else {
      // 没有冲突，显示继续上传的状态
      uploadStatus.value = '未发现文件冲突，准备上传文件...';
      uploadProgress.value = 50;
      await new Promise(resolve => setTimeout(resolve, 300)); // 短暂延迟
    }

    // 没有冲突，直接上传文件
    await uploadFilesToServer(filesToUpload, connectionInfo);

    // 清空pending upload data
    pendingUploadData.value = { items: [], outputType: 'production' };

  } catch (error) {
    console.error('Upload to server failed:', error);
    uploadStatus.value = '上传失败';
    alert('上传到服务器失败: ' + (error as Error).message);
    showUploadProgress.value = false;
  } finally {
    isUploading.value = false;
  }
}

// 新增：实际上传文件的函数
async function uploadFilesToServer(filesToUpload: Array<{file: File, remotePath: string}>, connectionInfo: any) {
  try {
    // 显示上传进度对话框
    showUploadProgress.value = true;
    uploadProgress.value = 50; // 从50%开始，因为前面已经用了40%生成+10%冲突检测
    uploadStatus.value = '开始上传文件...';

    totalFiles.value = filesToUpload.length;
    uploadedFiles.value = 0;

    for (const {file, remotePath} of filesToUpload) {
      try {
        uploadStatus.value = `上传文件: ${file.name}`;

        // 上传文件
        await serverFileManager.uploadFile(
          file,
          remotePath,
          (progress) => {
            // 更新总体进度 (50% 已完成 + 50% 上传)
            const fileProgress = (uploadedFiles.value / totalFiles.value) * 50 + (progress.progress / totalFiles.value) * 50;
            uploadProgress.value = Math.round(50 + fileProgress);
          }
        );

        uploadedFiles.value++;
        console.log(`Uploaded ${file.name} (${uploadedFiles.value}/${totalFiles.value})`);
      } catch (error) {
        console.error(`Failed to upload ${file.name}:`, error);
        uploadStatus.value = `上传失败: ${file.name}`;
        alert(`上传文件 ${file.name} 失败: ${(error as Error).message}`);
      }
    }

    uploadProgress.value = 100;
    uploadStatus.value = `上传完成！���功上传 ${uploadedFiles.value} 个文件`;

    // 3秒后��动关闭进度对话框
    setTimeout(() => {
      showUploadProgress.value = false;
    }, 3000);

  } catch (error) {
    console.error('Upload files failed:', error);
    uploadStatus.value = '上传失败';
    alert('上传文件失败: ' + (error as Error).message);
    showUploadProgress.value = false;
  }
}

// 新增：��理文件冲突
async function handleConflictResolution(resolution: ConflictResolution) {
  console.log('Handling file conflict resolution:', resolution);

  try {
    showFileConflictDialog.value = false;

    if (resolution.skipAll) {
      // 用户选择跳过所有冲突文件
      const filesToUpload = resolution.conflicts
        .filter(conflict => !conflict.shouldOverwrite)
        .map(conflict => ({
          file: conflict.localFile,
          remotePath: conflict.remotePath
        }));

      if (filesToUpload.length === 0) {
        alert('所有文件都存在冲突，上传已取消。');
        return;
      }

      await uploadFilesToServer(filesToUpload, serverFileManager.getConnection());
    } else {
      // 根据用�������上传文件
      const filesToUpload = resolution.conflicts
        .filter(conflict => conflict.shouldOverwrite)
        .map(conflict => ({
          file: conflict.localFile,
          remotePath: conflict.remotePath
        }));

      if (filesToUpload.length === 0) {
        alert('没有选择要覆盖的文件，上传已取消。');
        return;
      }

      await uploadFilesToServer(filesToUpload, serverFileManager.getConnection());
    }

  } catch (error) {
    console.error('Error handling conflict resolution:', error);
    alert('处理文件冲突时出错: ' + (error as Error).message);
  }
}
</script>

<style scoped>
/* PRISM 高级主题样式 */

/* Tab样式 - 优雅简约 */
.header-tabs {
  display: flex;
  gap: 0;
  margin-top: 1rem;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 20px;
  padding: 6px;
  backdrop-filter: blur(30px);
  justify-content: center;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  box-shadow: var(--shadow-lg);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.tab-btn.wide-tab {
  flex: 1;
  background: none !important;
  border: none !important;
  color: var(--text-secondary) !important;
  padding: 1.2rem 3rem !important;
  border-radius: 16px !important;
  cursor: pointer !important;
  transition: all 0.3s cubic-bezier(0.25, 0.46, 0.45, 0.94) !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  gap: 0.75rem !important;
  font-size: 1.1rem !important;
  font-weight: 600 !important;
  min-width: 200px !important;
  white-space: nowrap !important;
  text-shadow: var(--text-shadow-subtle) !important;
}

.tab-btn.wide-tab:hover {
  color: var(--text-primary) !important;
  background: rgba(255, 255, 255, 0.3) !important;
  transform: translateY(-2px) !important;
  box-shadow: var(--shadow-md) !important;
}

.tab-btn.wide-tab.active {
  background: var(--accent-gradient) !important;
  color: white !important;
  font-weight: 700 !important;
  backdrop-filter: blur(30px) !important;
  box-shadow: var(--shadow-xl) !important;
  border: 1px solid rgba(255, 255, 255, 0.4) !important;
}

.tab-icon {
  color: currentColor !important;
  width: 22px !important;
  height: 22px !important;
}

.tab-text {
  font-size: inherit !important;
  font-weight: inherit !important;
}

/* Page title and section title effects - 去除彩虹，使用优雅渐变 */
.page-title.glow-text {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--text-primary);
  font-size: 1.8rem;
  font-weight: 800;
  text-shadow: var(--text-shadow-soft);
}

.section-title.glow-text {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  color: var(--text-primary);
  font-size: 1.2rem;
  font-weight: 700;
  text-shadow: var(--text-shadow-subtle);
}

/* PRISM标题 - 优雅的渐变效�� */
.sparkle-text {
  background: var(--accent-gradient);
  background-size: 200% 200%;
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  animation: elegantFlow 8s ease-in-out infinite;
  font-weight: 800;
  letter-spacing: -0.02em;
  position: relative;
}

.sparkle-text::after {
  content: '';
  position: absolute;
  bottom: -3px;
  left: 0;
  width: 100%;
  height: 3px;
  background: var(--accent-gradient);
  opacity: 0.4;
  border-radius: 2px;
  animation: elegantFlow 8s ease-in-out infinite;
}

@keyframes elegantFlow {
  0%, 100% {
    background-position: 0% 50%;
    filter: brightness(1);
  }
  50% {
    background-position: 100% 50%;
    filter: brightness(1.2);
  }
}

/* Main layout - 更深的背景层次 */
#app {
  min-height: 100vh;
  background: linear-gradient(135deg,
    #94a3b8 0%,
    #cbd5e1 25%,
    #e2e8f0 50%,
    #f1f5f9 75%,
    #f8fafc 100%);
  background-size: 300% 300%;
  animation: sophisticatedFlow 25s ease infinite;
  color: var(--text-primary);
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

@keyframes sophisticatedFlow {
   0% { background-position: 0% 50%; }
 33% { background-position: 100% 25%; }
 66% { background-position: 0% 75%; }
 100% { background-position: 0% 50%; }
}

.app-header {
  padding: 2rem 1rem;
  background: var(--glass-bg-strong);
  backdrop-filter: blur(40px);
  border-bottom: 1px solid rgba(255, 255, 0.3);
  box-shadow: var(--shadow-lg);
  position: relative;
}

.app-header::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-gradient);
  opacity: 0.8;
}

.header-content {
  max-width: 1200px;
  margin: 0 auto;
}

.logo-section {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.logo-icon img {
  border-radius: 12px;
  box-shadow: var(--shadow-md);
  border: 2px solid rgba(255, 255, 255, 0.4);
  transition: all 0.3s ease;
}

.logo-icon img:hover {
  transform: scale(1.05);
  box-shadow: var(--shadow-lg);
}

.title-group h1 {
  margin: 0;
  font-size: 2.5rem;
  font-weight: 800;
}

.subtitle {
  margin: 0;
  color: var(--text-secondary);
  font-size: 1rem;
  font-weight: 500;
  text-shadow: var(--text-shadow-subtle);
}

.main-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem 1rem;
}

/* Content layout */
.content-grid {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 2rem;
  margin-top: 2rem;
}

.left-column, .right-column {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

/* 高级玻璃质感卡片 */
.section-card {
  background: var(--glass-bg-medium);
  border-radius: 24px;
  padding: 2rem;
  backdrop-filter: blur(30px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: var(--shadow-xl);
  position: relative;
  transition: all 0.3s ease;
}

.section-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--shadow-2xl);
  border-color: rgba(79, 70, 229, 0.3);
}

.section-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gradient);
  opacity: 0.6;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid rgba(255, 255, 255, 0.2);
}

.section-icon, .page-icon {
  color: var(--prism-accent);
  flex-shrink: 0;
}

/* Upload section */
.upload-zone {
  border: 2px dashed var(--prism-primary);
  border-radius: 16px;
  padding: 2.5rem;
  text-align: center;
  transition: all 0.3s ease;
  cursor: pointer;
  background: var(--glass-bg-light);
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

.upload-zone:hover {
  border-color: var(--prism-secondary);
  background: var(--glass-bg-medium);
  transform: scale(1.02);
  box-shadow: var(--shadow-lg);
}

.upload-zone.uploading {
  border-color: var(--prism-accent);
  background: rgba(6, 182, 212, 0.1);
  box-shadow: 0 0 20px rgba(6, 182, 212, 0.3);
}

.file-input {
  display: none;
}

.upload-label {
  cursor: pointer;
  display: block;
}

.upload-visual {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
}

.upload-icon {
  color: var(--prism-primary);
  transition: all 0.3s ease;
}

.upload-zone:hover .upload-icon {
  color: var(--prism-secondary);
  transform: scale(1.1);
}

.upload-text {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.upload-main {
  font-size: 1.2rem;
  color: var(--text-primary);
  font-weight: 700;
}

.upload-sub {
  color: var(--text-secondary);
  font-weight: 500;
}

.upload-hint {
  color: var(--text-tertiary);
  font-size: 0.875rem;
}

.uploading-text {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--prism-accent);
  font-weight: 600;
}

.spinner-small {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(6, 182, 212, 0.3);
  border-top: 2px solid var(--prism-accent);
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

/* Data stats */
.data-stats {
  display: flex;
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.stat-card {
  display: flex;
  align-items: center;
  gap: 1rem;
  background: var(--glass-bg-strong);
  padding: 1.5rem;
  border-radius: 16px;
  flex: 1;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: var(--shadow-md);
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gradient);
  opacity: 0.6;
  border-radius: 16px 16px 0 0;
}

.stat-icon {
  color: var(--prism-accent);
}

.stat-number {
  font-size: 1.8rem;
  font-weight: 800;
  color: var(--text-primary);
  text-shadow: var(--text-shadow-subtle);
}

.stat-label {
  font-size: 0.875rem;
  color: var(--text-secondary);
  font-weight: 600;
}

/* Form styling */
.config-form {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.form-label {
  font-weight: 700;
  color: var(--text-primary);
  font-size: 1rem;
  display: flex;
  align-items: center;
  text-shadow: var(--text-shadow-subtle);
}

.radio-group {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.radio-option {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  cursor: pointer;
  padding: 1rem;
  border-radius: 12px;
  transition: all 0.2s ease;
  background: var(--glass-bg-light);
  border: 1px solid rgba(255, 255, 255, 0.3);
}

.radio-option:hover {
  background: var(--glass-bg-medium);
  transform: translateY(-1px);
  box-shadow: var(--shadow-sm);
}

.radio-option input[type="radio"] {
  margin: 0;
  accent-color: var(--prism-primary);
}

.radio-label {
  color: var(--text-primary);
  font-weight: 600;
}

.form-select {
  padding: 1rem;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 12px;
  background: var(--glass-bg-medium);
  color: var(--text-primary);
  font-size: 1rem;
  font-weight: 600;
  backdrop-filter: blur(20px);
  box-shadow: var(--shadow-sm);
}

.form-select option {
  background: rgba(255, 255, 255, 0.95);
  color: var(--text-primary);
  font-weight: 600;
}

/* Generate button */
.generate-btn {
  padding: 1.25rem 2.5rem;
  background: var(--accent-gradient);
  background-size: 200% 200%;
  color: white;
  border: none;
  border-radius: 16px;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-lg);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
  animation: buttonGlow 3s ease-in-out infinite;
}

@keyframes buttonGlow {
  0%, 100% { background-position: 0% 50%; }
  50% { background-position: 100% 50%; }
}

.generate-btn:hover:not(:disabled) {
  transform: translateY(-3px);
  box-shadow: var(--shadow-xl);
}

.generate-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Upload button */
.upload-btn {
  padding: 1.25rem 2.5rem;
  background: var(--prism-primary);
  color: white;
  border: none;
  border-radius: 16px;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: var(--shadow-lg);
  text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
}

.upload-btn:hover:not(:disabled) {
  background: var(--prism-secondary);
  transform: translateY(-3px);
  box-shadow: var(--shadow-xl);
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none;
}

/* Sheet selector */
.sheet-selector-container {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.sheet-label {
  font-size: 0.9rem;
  color: var(--text-secondary);
  font-weight: 600;
}

.sheet-select {
  padding: 0.5rem 0.75rem;
  border: 1px solid rgba(255, 255, 255, 0.4);
  border-radius: 8px;
  background: var(--glass-bg-medium);
  color: var(--text-primary);
  font-size: 0.9rem;
  font-weight: 600;
}

/* No data state */
.no-data {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 1.5rem;
  padding: 3rem 2rem;
  color: var(--text-muted);
  text-align: center;
}

.no-data-icon {
  color: var(--text-tertiary);
}

/* Page header */
.page-header {
  text-align: center;
  margin-bottom: 2rem;
  background: var(--glass-bg-strong);
  padding: 2.5rem;
  border-radius: 24px;
  backdrop-filter: blur(40px);
  border: 1px solid rgba(255, 255, 255, 0.4);
  box-shadow: var(--shadow-xl);
  position: relative;
}

.page-header::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 3px;
  background: var(--accent-gradient);
  opacity: 0.8;
  border-radius: 24px 24px 0 0;
}

.page-description {
  color: var(--text-secondary);
  font-size: 1.1rem;
  font-weight: 500;
  margin: 1rem 0 0 0;
  max-width: 600px;
  margin-left: auto;
  margin-right: auto;
  text-shadow: var(--text-shadow-subtle);
}

/* About page specific styles */
.about-view {
  min-height: 60vh;
}

.about-content {
  display: flex;
  flex-direction: column;
  gap: 2rem;
  max-width: 1200px;
  margin: 0 auto;
}

.about-section {
  position: relative;
}

.about-section .section-body {
  color: var(--text-secondary);
  line-height: 1.7;
}

.about-section .section-body p {
  margin-bottom: 1.5rem;
  font-size: 1.1rem;
  font-weight: 500;
}

.about-section .section-body p:last-child {
  margin-bottom: 0;
}

/* Features grid */
.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-top: 1rem;
}

.feature-card {
  background: var(--glass-bg-light);
  padding: 2rem;
  border-radius: 16px;
  text-align: center;
  transition: all 0.3s ease;
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(20px);
  position: relative;
  overflow: hidden;
}

.feature-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gradient);
  opacity: 0.6;
}

.feature-card:hover {
  transform: translateY(-8px);
  box-shadow: var(--shadow-xl);
  border-color: rgba(79, 70, 229, 0.4);
}

.feature-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 60px;
  background: var(--glass-bg-medium);
  border-radius: 50%;
  margin-bottom: 1.5rem;
  color: var(--prism-primary);
  backdrop-filter: blur(15px);
  border: 1px solid rgba(255, 255, 255, 0.3);
  transition: all 0.3s ease;
}

.feature-card:hover .feature-icon {
  background: var(--prism-primary);
  color: white;
  transform: scale(1.1);
  box-shadow: 0 0 20px rgba(79, 70, 229, 0.4);
}

.feature-card h4 {
  margin: 0 0 1rem 0;
  font-size: 1.2rem;
  font-weight: 700;
  color: var(--text-primary);
  text-shadow: var(--text-shadow-subtle);
}

.feature-card p {
  margin: 0;
  font-size: 0.95rem;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Usage steps */
.usage-steps {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  margin-top: 1rem;
}

.step-item {
  display: flex;
  align-items: flex-start;
  gap: 1.5rem;
  padding: 1.5rem;
  background: var(--glass-bg-light);
  border-radius: 16px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(20px);
  transition: all 0.3s ease;
  position: relative;
}

.step-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gradient);
  opacity: 0.6;
  border-radius: 16px 16px 0 0;
}

.step-item:hover {
  transform: translateY(-3px);
  box-shadow: var(--shadow-lg);
  border-color: rgba(79, 70, 229, 0.4);
}

.step-number {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  background: var(--prism-primary);
  color: white;
  border-radius: 50%;
  font-weight: 700;
  font-size: 1.1rem;
  flex-shrink: 0;
  box-shadow: 0 0 15px rgba(79, 70, 229, 0.3);
}

.step-content h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  font-weight: 700;
  color: var(--text-primary);
  text-shadow: var(--text-shadow-subtle);
}

.step-content p {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}

/* Tech features */
.tech-features {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  margin-top: 1rem;
}

.tech-item {
  padding: 1.5rem;
  background: var(--glass-bg-light);
  border-radius: 12px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  backdrop-filter: blur(20px);
  transition: all 0.3s ease;
  position: relative;
}

.tech-item::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 2px;
  background: var(--accent-gradient);
  opacity: 0.6;
  border-radius: 12px 12px 0 0;
}

.tech-item:hover {
  transform: translateY(-2px);
  box-shadow: var(--shadow-md);
  border-color: rgba(79, 70, 229, 0.4);
}

.tech-item strong {
  color: var(--prism-primary);
  font-weight: 700;
}

/* Responsive design for about page */
@media (max-width: 768px) {
  .features-grid {
    grid-template-columns: 1fr;
  }

  .step-item {
    flex-direction: column;
    text-align: center;
  }

  .step-number {
    align-self: center;
  }

  .about-content {
    padding: 0 1rem;
  }
}
</style>

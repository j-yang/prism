<template>
  <div v-if="visible" class="template-selection-overlay">
    <div class="template-selection-dialog">
      <div class="dialog-header">
        <h3>Template Selection</h3>
        <p>Detected program names that match reference templates. Please select which template to use:</p>
      </div>

      <div class="dialog-content">
        <div class="template-matches">
          <div v-for="match in templateMatches" :key="match.programName" class="match-item">
            <div class="program-info">
              <strong>{{ match.programName }}</strong>
              <span v-if="match.matchedTemplate" class="matched-badge">
                Match Found: {{ match.matchedTemplate.name }}
              </span>
            </div>

            <div class="template-options">
              <label class="radio-option">
                <input
                  type="radio"
                  :name="`template-${match.programName}`"
                  :value="false"
                  v-model="match.useReference"
                />
                <span>Use General Template</span>
                <small>{{ currentTemplateName }} from Template Manager</small>
              </label>

              <label
                v-if="match.matchedTemplate"
                class="radio-option recommended"
              >
                <input
                  type="radio"
                  :name="`template-${match.programName}`"
                  :value="true"
                  v-model="match.useReference"
                />
                <span>Use Specific Template <span class="recommend-tag">Recommended</span></span>
                <small>{{ match.matchedTemplate.path }}</small>
              </label>
            </div>
          </div>
        </div>

        <div class="batch-selection">
          <h4>Batch Operations:</h4>
          <button @click="selectAllGeneral" class="batch-btn">Use General Template for All</button>
          <button @click="selectAllReference" class="batch-btn">Use Specific Template for All</button>
        </div>
      </div>

      <div class="dialog-footer">
        <button @click="cancel" class="btn-cancel">Cancel</button>
        <button @click="confirm" class="btn-confirm">Confirm</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { TemplateMatch } from '../services/ReferenceTemplateService'

interface Props {
  visible: boolean
  templateMatches: TemplateMatch[]
  currentTemplateName: string
}

interface Emits {
  (e: 'confirm', matches: TemplateMatch[]): void
  (e: 'cancel'): void
}

const props = defineProps<Props>()
const emit = defineEmits<Emits>()

const templateMatches = ref<TemplateMatch[]>([])

// 监听props变化
watch(() => props.templateMatches, (newMatches) => {
  templateMatches.value = [...newMatches]
}, { immediate: true })

const hasMatches = computed(() =>
  templateMatches.value.some(match => match.matchedTemplate !== null)
)

function selectAllGeneral() {
  templateMatches.value.forEach(match => {
    match.useReference = false
  })
}

function selectAllReference() {
  templateMatches.value.forEach(match => {
    if (match.matchedTemplate) {
      match.useReference = true
    }
  })
}

function confirm() {
  emit('confirm', templateMatches.value)
}

function cancel() {
  emit('cancel')
}
</script>

<style scoped>
.template-selection-overlay {
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

.template-selection-dialog {
  background: white;
  border-radius: 8px;
  max-width: 700px;
  width: 90%;
  max-height: 80vh;
  overflow-y: auto;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.dialog-header {
  padding: 20px;
  border-bottom: 1px solid #eee;
}

.dialog-header h3 {
  margin: 0 0 8px 0;
  color: #333;
}

.dialog-header p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.dialog-content {
  padding: 20px;
}

.match-item {
  margin-bottom: 20px;
  padding: 16px;
  border: 1px solid #eee;
  border-radius: 6px;
}

.program-info {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 12px;
}

.matched-badge {
  background: #e8f5e8;
  color: #2d7d2d;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 12px;
  font-weight: normal;
}

.template-options {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.radio-option {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
  border-radius: 4px;
  transition: background-color 0.2s;
}

.radio-option:hover {
  background: #f5f5f5;
}

.radio-option.recommended {
  border: 1px solid #4CAF50;
  background: #f8fff8;
}

.radio-option input[type="radio"] {
  margin-top: 2px;
}

.radio-option span {
  font-weight: 500;
}

.radio-option small {
  display: block;
  color: #666;
  font-size: 12px;
  margin-top: 2px;
}

.recommend-tag {
  background: #4CAF50;
  color: white;
  padding: 1px 6px;
  border-radius: 8px;
  font-size: 10px;
  margin-left: 4px;
}

.batch-selection {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.batch-selection h4 {
  margin: 0 0 10px 0;
  font-size: 14px;
  color: #333;
}

.batch-btn {
  margin-right: 10px;
  padding: 6px 12px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.batch-btn:hover {
  background: #f5f5f5;
}

.dialog-footer {
  padding: 16px 20px;
  border-top: 1px solid #eee;
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}

.btn-cancel {
  padding: 8px 20px;
  border: 1px solid #ddd;
  background: white;
  border-radius: 4px;
  cursor: pointer;
}

.btn-confirm {
  padding: 8px 20px;
  border: none;
  background: #007bff;
  color: white;
  border-radius: 4px;
  cursor: pointer;
}

.btn-cancel:hover {
  background: #f5f5f5;
}

.btn-confirm:hover {
  background: #0056b3;
}
</style>

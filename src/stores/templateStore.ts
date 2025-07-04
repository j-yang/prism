import { defineStore } from 'pinia';
import { ref, computed } from 'vue';
import {ExcelProcessor} from '../services/ExcelProcessor';
import ProgramGenerator from '../services/ProgramGenerator';
import type { Template, ADaMItem } from '../services/types/adam';

export const useTemplateStore = defineStore('template', () => {
    const templates = ref<Template[]>([
        {
            id: 'prod_default',
            name: '默认生产模板',
            content: `/* 生产程序: @@domain */
data adam.@@domain;
set raw.source;
/* 生成日期: @@date */`
        },
        {
            id: 'val_default',
            name: '默认验证模板',
            content: `/* 验证程序: @@domain */
proc validate data=@@domain;
/* 验证人: @@programmer */`
        }
    ]);

    const addTemplate = (template: Omit<Template, 'id'>) => {
        templates.value.push({
            ...template,
            id: `custom_${Date.now()}`
        });
    };

    return {
        templates,
        addTemplate
    };
});

export const useProgramStore = defineStore('program', () => {
    // 状态
    const outputType = ref<'Production' | 'Validation'>('Production');
    const selectedProgrammer = ref('ALL');
    const selectedIndices = ref<Set<number>>(new Set());
    const excelData = ref<ADaMItem[]>([]);
    const templateContent = ref('');
    const excelProcessor = new ExcelProcessor();
    const sheetNames = ref<string[]>([]);
    const selectedSheet = ref<string>('');
    const selectedSheets = ref<string[]>([]);
    const sheetDataMap = ref<Record<string, ADaMItem[]>>({});

    // 计算属性
    const filteredData = computed(() => {
        if (!selectedSheet.value || !sheetDataMap.value[selectedSheet.value]) {
            return [];
        }
        return sheetDataMap.value[selectedSheet.value];
    });

    const selectedData = computed(() => {
        return Array.from(selectedIndices.value)
            .map(index => filteredData.value[index])
            .filter(Boolean);
    });

    // 方法
    const processExcelFile = async (file: File): Promise<string[]> => {
        try {
            console.log('Processing Excel file:', file.name);
            const result = await excelProcessor.processFile(file);

            // 清空之前的数据
            sheetDataMap.value = {};
            excelData.value = [];

            // 保存工作表名称
            sheetNames.value = result.sheetNames;

            // 保存每个工作表的数据
            for (const [sheetName, data] of Object.entries(result.sheetsData)) {
                sheetDataMap.value[sheetName] = data as ADaMItem[];
            }

            console.log('Excel processing completed. Sheets:', sheetNames.value);
            console.log('Sheet data map:', sheetDataMap.value);

            return sheetNames.value;
        } catch (error) {
            console.error('Error processing Excel file:', error);
            throw error;
        }
    };

    const selectSheet = (sheetName: string) => {
        selectedSheet.value = sheetName;
        selectedIndices.value.clear(); // 清空选择

        if (sheetDataMap.value[sheetName]) {
            excelData.value = sheetDataMap.value[sheetName];
            console.log(`Selected sheet: ${sheetName}, Data count: ${excelData.value.length}`);
        }
    };

    const selectSheets = (sheets: string[]) => {
        selectedSheets.value = sheets;
        if (sheets.length > 0 && !selectedSheet.value) {
            selectSheet(sheets[0]);
        }
    };

    const toggleSelection = (index: number) => {
        if (selectedIndices.value.has(index)) {
            selectedIndices.value.delete(index);
        } else {
            selectedIndices.value.add(index);
        }
    };

    const selectAll = () => {
        selectedIndices.value = new Set(Array.from({ length: filteredData.value.length }, (_, i) => i));
    };

    const deselectAll = () => {
        selectedIndices.value.clear();
    };

    const setOutputType = (type: 'Production' | 'Validation') => {
        outputType.value = type;
    };

    const setSelectedProgrammer = (programmer: string) => {
        selectedProgrammer.value = programmer;
    };

    const setTemplateContent = (content: string) => {
        templateContent.value = content;
    };

    const generatePrograms = async (progressCallback?: (progress: number) => void) => {
        if (selectedData.value.length === 0) {
            throw new Error('No data selected for program generation');
        }

        const generator = new ProgramGenerator();

        if (templateContent.value) {
            generator.setTemplate(templateContent.value);
        }

        await generator.generateZip(
            selectedData.value,
            outputType.value,
            progressCallback
        );
    };

    return {
        // 状态
        outputType,
        selectedProgrammer,
        selectedIndices,
        excelData,
        templateContent,
        sheetNames,
        selectedSheet,
        selectedSheets,
        sheetDataMap,

        // 计算属性
        filteredData,
        selectedData,

        // 方法
        processExcelFile,
        selectSheet,
        selectSheets,
        toggleSelection,
        selectAll,
        deselectAll,
        setOutputType,
        setSelectedProgrammer,
        setTemplateContent,
        generatePrograms
    };
});

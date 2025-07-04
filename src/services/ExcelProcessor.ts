import * as XLSX from 'xlsx';
import type { ADaMItem } from './types/adam';

export interface ExcelProcessResult {
    sheetNames: string[];
    sheetsData: Record<string, ADaMItem[]>;
}

export class ExcelProcessor {
    private workbook: XLSX.WorkBook | null = null;

    async processFile(file: File): Promise<ExcelProcessResult> {
        try {
            console.log('Starting Excel file processing:', file.name);

            // 读取文件
            const data = await this.readFileAsArrayBuffer(file);
            this.workbook = XLSX.read(data, { type: 'array' });

            const sheetNames = this.workbook.SheetNames;
            const sheetsData: Record<string, ADaMItem[]> = {};

            // 处理每个工作表
            for (const sheetName of sheetNames) {
                console.log(`Processing sheet: ${sheetName}`);
                const sheetData = this.parseSheet(sheetName);
                sheetsData[sheetName] = sheetData;
                console.log(`Sheet ${sheetName} processed: ${sheetData.length} rows`);
            }

            console.log('Excel processing completed successfully');
            return {
                sheetNames,
                sheetsData
            };
        } catch (error) {
            console.error('Error processing Excel file:', error);
            throw new Error(`Failed to process Excel file: ${error instanceof Error ? error.message : 'Unknown error'}`);
        }
    }

    private parseSheet(sheetName: string): ADaMItem[] {
        if (!this.workbook) {
            console.warn('No workbook loaded');
            return [];
        }

        const worksheet = this.workbook.Sheets[sheetName];
        if (!worksheet) {
            console.warn(`Sheet ${sheetName} not found`);
            return [];
        }

        try {
            // 获取工作表范围
            const range = XLSX.utils.decode_range(worksheet['!ref'] || 'A1');
            console.log(`Sheet ${sheetName} range:`, range);

            // 从第二行开始读取数据，跳过表头
            const jsonData = XLSX.utils.sheet_to_json(worksheet, {
                range: 1  // 从第二行开始（0-based，所以1表示第二行）
            });

            console.log(`Raw data from ${sheetName}:`, jsonData.length, 'rows');
            if (jsonData.length > 0) {
                console.log('Sample row:', jsonData[0]);
                console.log('Available columns:', Object.keys(jsonData[0]));
            }

            return this.parseExcelData(jsonData);
        } catch (error) {
            console.error(`Error parsing sheet ${sheetName}:`, error);
            return [];
        }
    }

    private parseExcelData(jsonData: any[]): ADaMItem[] {
        if (!jsonData || jsonData.length === 0) {
            console.log('No data to parse');
            return [];
        }

        console.log('Parsing Excel data:', jsonData.length, 'rows');
        console.log('Available columns:', Object.keys(jsonData[0]));

        // 过滤掉第一列以 "SUPP" 开头的行
        const filteredData = jsonData.filter((row, index) => {
            const firstColumnKey = Object.keys(row)[0];
            if (firstColumnKey) {
                const firstColumnValue = String(row[firstColumnKey] || '').trim().toUpperCase();
                if (firstColumnValue.startsWith('SUPP')) {
                    console.log(`Filtered out row ${index + 1}: First column value "${firstColumnValue}" starts with SUPP`);
                    return false;
                }
            }
            return true;
        });

        console.log(`Filtered data: ${filteredData.length} rows (${jsonData.length - filteredData.length} rows filtered out)`);

        // 检查是否包含Title列，决定解析模式
        const firstRow = filteredData[0];
        if (!firstRow) {
            console.log('No data remaining after filtering');
            return [];
        }

        const columns = Object.keys(firstRow);
        const hasTitle = columns.some(col =>
            col.toLowerCase().includes('title')
        );

        console.log('Data type detected:', hasTitle ? 'TLF (with Title column)' : 'Dataset');

        const parsed = filteredData.map((row, index) => {
            try {
                // 动态查找列名，使用所有可能的变体
                const findColumnValue = (possibleNames: string[]): string => {
                    for (const name of possibleNames) {
                        const value = row[name];
                        if (value !== undefined && value !== null && value !== '') {
                            return String(value).trim();
                        }
                    }
                    return '';
                };

                // 根据是否有Title列来使用������的匹配策略
                let domain = '';
                let prodProgram = '';
                let valProgram = '';
                let prodProgrammer = '';
                let valProgrammer = '';
                let title = '';

                if (hasTitle) {
                    // TLF类型数据 - 保存原始字段，在前端进行拼接
                    const outputType = findColumnValue([
                        'Output Type (Table, Listing, Figure)', 'OUTPUT TYPE (TABLE, LISTING, FIGURE)',
                        'Output Type', 'OUTPUT TYPE', 'output type',
                        'Type', 'TYPE', 'type',
                        'Output_Type', 'OUTPUT_TYPE',
                        'OutputType', 'OUTPUTTYPE'
                    ]);

                    const outputNumber = findColumnValue([
                        'Output # ', 'Output #', 'OUTPUT # ', 'OUTPUT #', 'OUTPUT NUMBER',
                        'Number', 'NUMBER', 'number', '#', 'No', 'NO', 'no',
                        'Output_#', 'OUTPUT_#', 'Output No', 'OUTPUT NO',
                        'OutputNumber', 'OUTPUTNUMBER', 'Output_Number'
                    ]);

                    const titleValue = findColumnValue([
                        'Title', 'TITLE', 'title',
                        'Output Title', 'OUTPUT TITLE', 'outputTitle',
                        'Description', 'DESCRIPTION', 'description',
                        'OutputTitle', 'OUTPUTTITLE'
                    ]);

                    // 保存原始字段供前端拼接使用 - 不再使用domain概念，直接使用Index
                    domain = `Item_${index + 1}`;  // TLF数据不需要domain概念

                    title = titleValue;

                    // TLF的Program和Programmer字段
                    prodProgram = findColumnValue([
                        'Program Name', 'PROGRAM NAME', 'program name',
                        'Production Program', 'Prod Program', 'PROD_PROGRAM', 'prodProgram'
                    ]);

                    valProgram = findColumnValue([
                        'QC Program', 'QC PROGRAM', 'qc program',
                        'QC Program (if any)', 'QC_PROGRAM', 'qcProgram',
                        'Validation Program', 'Val Program', 'VAL_PROGRAM', 'valProgram'
                    ]);

                    prodProgrammer = findColumnValue([
                        'Programmer PRID', 'PROGRAMMER PRID', 'programmer prid',
                        'Production Programmer', 'Prod Programmer', 'PROD_PROGRAMMER', 'prodProgrammer'
                    ]);

                    valProgrammer = findColumnValue([
                        'QC Programmer PRID', 'QC PROGRAMMER PRID', 'qc programmer prid',
                        'Validation Programmer', 'Val Programmer', 'VAL_PROGRAMMER', 'valProgrammer'
                    ]);

                    // 添加Output Name字段的提取
                    const outputName = findColumnValue([
                        'Output Name', 'OUTPUT NAME', 'output name',
                        'OutputName', 'OUTPUTNAME', 'outputname',
                        'Output_Name', 'OUTPUT_NAME', 'output_name',
                        'File Name', 'FILE NAME', 'filename', 'FileName'
                    ]);

                    // 添加调试信息（在所有变量定义之后）
                    console.log(`TLF Row ${index + 1} Processing:`, {
                        outputType: outputType || '(empty)',
                        outputNumber: outputNumber || '(empty)',
                        titleValue: titleValue || '(empty)',
                        outputName: outputName || '(empty)',
                        domain,
                        prodProgram: prodProgram || '(empty)',
                        valProgram: valProgram || '(empty)',
                        prodProgrammer: prodProgrammer || '(empty)',
                        valProgrammer: valProgrammer || '(empty)',
                        allColumns: Object.keys(row)
                    });

                    const item: ADaMItem = {
                        domain: domain,
                        prodProgram: prodProgram || '',
                        valProgram: valProgram || '',
                        prodProgrammer: prodProgrammer || '',
                        valProgrammer: valProgrammer || '',
                        title: title || '',
                        hasTitle: hasTitle,
                        // 保存TLF特有字段
                        outputType: outputType || '',
                        outputNumber: outputNumber || '',
                        outputTitle: titleValue || '',
                        outputName: outputName || '' // 添加outputName字段
                    };

                    return item;
                } else {
                    // ADaM类型数据 - 使用原有的匹配逻辑
                    domain = findColumnValue([
                        'Dataset Name', 'DATASET NAME', 'dataset name',
                        'Domain', 'DOMAIN', 'domain',
                        'Dataset', 'DATASET', 'dataset',
                        'Table', 'TABLE', 'table'
                    ]);

                    prodProgram = findColumnValue([
                        'Program Name', 'PROGRAM NAME', 'program name',
                        'Production Program', 'Prod Program', 'PROD_PROGRAM', 'prodProgram',
                        'Program', 'PROGRAM', 'program'
                    ]);

                    valProgram = findColumnValue([
                        'QC Program (if any)', 'QC Program', 'QC_PROGRAM', 'qcProgram',
                        'Validation Program', 'Val Program', 'VAL_PROGRAM', 'valProgram'
                    ]);

                    prodProgrammer = findColumnValue([
                        'Programmer PRID', 'PROGRAMMER PRID', 'programmer prid',
                        'Production Programmer', 'Prod Programmer', 'PROD_PROGRAMMER', 'prodProgrammer',
                        'Programmer', 'PROGRAMMER', 'programmer'
                    ]);

                    valProgrammer = findColumnValue([
                        'QC Programmer PRID', 'QC PROGRAMMER PRID', 'qc programmer prid',
                        'Validation Programmer', 'Val Programmer', 'VAL_PROGRAMMER', 'valProgrammer'
                    ]);
                }

                const item: ADaMItem = {
                    domain: domain || `Item_${index + 1}`,
                    prodProgram: prodProgram || '',
                    valProgram: valProgram || '',
                    prodProgrammer: prodProgrammer || '',
                    valProgrammer: valProgrammer || '',
                    title: title || '',
                    hasTitle: hasTitle  // 添加标识字段
                };

                return item;
            } catch (error) {
                console.error(`Error parsing row ${index}:`, error, row);
                return {
                    domain: `Error_Row_${index + 1}`,
                    prodProgram: '',
                    valProgram: '',
                    prodProgrammer: '',
                    valProgrammer: '',
                    title: '',
                    hasTitle: false
                };
            }
        });

        console.log(`Parsed ${parsed.length} items successfully`);
        console.log('Sample parsed item:', parsed[0]);

        return parsed;
    }

    private readFileAsArrayBuffer(file: File): Promise<ArrayBuffer> {
        return new Promise((resolve, reject) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                if (e.target?.result instanceof ArrayBuffer) {
                    resolve(e.target.result);
                } else {
                    reject(new Error('Failed to read file as ArrayBuffer'));
                }
            };
            reader.onerror = () => reject(new Error('File reading failed'));
            reader.readAsArrayBuffer(file);
        });
    }

    // 获取工作表名称（用于向后兼容）
    async loadExcel(file: File): Promise<string[]> {
        const result = await this.processFile(file);
        return result.sheetNames;
    }

    // 解析特定工作表（用于向后兼容）
    parseSheetData(sheetName: string): ADaMItem[] {
        if (!this.workbook) {
            console.warn('No workbook loaded');
            return [];
        }

        const worksheet = this.workbook.Sheets[sheetName];
        if (!worksheet) {
            console.warn(`Sheet ${sheetName} not found`);
            return [];
        }

        try {
            // 从第二行开始读取数据，跳过表头
            const jsonData = XLSX.utils.sheet_to_json(worksheet, {
                range: 1  // 从第二行开始（0-based，所以1表示第二行）
            });

            return this.parseExcelData(jsonData);
        } catch (error) {
            console.error(`Error parsing sheet ${sheetName}:`, error);
            return [];
        }
    }
}

import type { ADaMItem, OutputType } from './types/adam';

export default class ProgramGenerator {
    private currentTemplate = '';

    setTemplate(content: string): void {
        this.currentTemplate = content;
        console.log('Template set successfully:', content.length, 'characters');
    }

    // 新增：为单个项目生成代码，支持引用模板
    generateCode(item: ADaMItem, outputType: OutputType): string {
        // 如果使用引用模板且有引用模板内容，使用引用模板
        if (item.useReferenceTemplate && item.referenceTemplateContent) {
            console.log(`Using reference template for ${item.domain}`);
            return this.processTemplate(item.referenceTemplateContent, item, outputType);
        }

        // 否则使用通用模板
        console.log(`Using general template for ${item.domain}`);
        return this.processTemplate(this.currentTemplate, item, outputType);
    }

    private processTemplate(template: string, item: ADaMItem, outputType: OutputType): string {
        let result = template;

        // 基本替换
        const programmer = outputType === 'Production' ? item.prodProgrammer : item.valProgrammer;
        const programName = this.getFileName(item, outputType).replace('.sas', '');

        result = result.replace(/@@program_name/g, programName);
        result = result.replace(/@@author/g, programmer || 'Unknown');
        result = result.replace(/@@date/g, new Date().toLocaleDateString('en-US', {
            year: 'numeric',
            month: '2-digit',
            day: '2-digit'
        }));

        // 根据数据类型进行特定替换
        if (item.hasTitle) {
            // TLF数据的替换
            result = result.replace(/@@purpose/g, item.title || item.outputTitle || `Generate ${item.outputType} ${item.outputNumber}`);
            result = result.replace(/@@output/g, item.outputName || `${item.outputType}_${item.outputNumber}.rtf`);
        } else {
            // 普通ADaM数据的替换
            result = result.replace(/@@purpose/g, `Create ${item.domain.toUpperCase()} dataset`);
            result = result.replace(/@@output/g, `${item.domain.toLowerCase()}.xpt`);
        }

        return result;
    }

    getFileName(item: ADaMItem, outputType: OutputType): string {
        // 对于TLF数据，使用Excel中的Program Name或QC Program
        if (item.hasTitle) {
            const programName = outputType === 'Production'
                ? (item.prodProgram || `${item.domain.toLowerCase()}`)
                : (item.valProgram || `v_${item.domain.toLowerCase()}`);

            // 确保文件名以.sas结尾
            return programName.endsWith('.sas') ? programName : `${programName}.sas`;
        } else {
            // 对于普通ADaM数据，使用原有逻辑
            return outputType === 'Production'
                ? `${item.domain.toLowerCase()}.sas`
                : `v_${item.domain.toLowerCase()}.sas`;
        }
    }

    /**
     * 创建占位符替换映射表
     * 支持Excel中的所有数据字段
     */
    private createReplacementMap(item: ADaMItem, outputType: OutputType, allItems?: ADaMItem[]): Record<string, string> {
        const currentDate = new Date();
        const dateString = currentDate.toISOString().slice(0, 10);
        const dateTimeString = currentDate.toLocaleString();

        // 根据输出类型选择程序员和程序名
        const programmer = outputType === 'Production'
            ? (item.prodProgrammer || 'Unknown Programmer')
            : (item.valProgrammer || 'Unknown QC Programmer');

        const programName = outputType === 'Production'
            ? (item.prodProgram || `${item.domain.toLowerCase()}.sas`)
            : (item.valProgram || `v_${item.domain.toLowerCase()}.sas`);

        // 生成输出文件名和目的描述
        const outputFile = this.generateOutputFileName(item, outputType);
        const allOutputFiles = allItems
            ? this.generateAllOutputFiles(allItems, item, outputType)
            : outputFile;
        const purpose = this.generatePurposeDescription(item, outputType, allItems);

        return {
            // 基础字段
            'domain': item.domain.toLowerCase(),
            'DOMAIN': item.domain.toUpperCase(),
            'Domain': this.capitalizeFirst(item.domain),

            // 程序相关
            'program_name': programName,
            'program': programName,
            'PROGRAM_NAME': programName.toUpperCase(),

            // 人员信息
            'programmer': programmer,
            'author': programmer,
            'PROGRAMMER': programmer.toUpperCase(),
            'AUTHOR': programmer.toUpperCase(),

            // 日期时间
            'date': dateString,
            'DATE': dateString,
            'datetime': dateTimeString,
            'DATETIME': dateTimeString,
            'timestamp': currentDate.getTime().toString(),

            // 输出文件 - 支持多输出文件
            'output': allOutputFiles,
            'OUTPUT': allOutputFiles.toUpperCase(),
            'output_file': allOutputFiles,
            'OUTPUT_FILE': allOutputFiles.toUpperCase(),
            'output_files': allOutputFiles,
            'OUTPUT_FILES': allOutputFiles.toUpperCase(),

            // 程序目的和描述
            'purpose': purpose,
            'PURPOSE': purpose.toUpperCase(),
            'description': purpose,
            'DESCRIPTION': purpose.toUpperCase(),

            // TLF特有字段 (如果有的话)
            'output_type': item.outputType || '',
            'OUTPUT_TYPE': (item.outputType || '').toUpperCase(),
            'output_number': item.outputNumber || '',
            'OUTPUT_NUMBER': (item.outputNumber || '').toUpperCase(),
            'output_title': item.outputTitle || '',
            'OUTPUT_TITLE': (item.outputTitle || '').toUpperCase(),

            // 程序类型
            'program_type': outputType,
            'PROGRAM_TYPE': outputType.toUpperCase(),
            'type': outputType === 'Production' ? 'Production' : 'Validation',
            'TYPE': outputType === 'Production' ? 'PRODUCTION' : 'VALIDATION',

            // 项目路��相关
            'study': 'STUDY_ID', // 可以根据需要调整
            'STUDY': 'STUDY_ID',
            'project': 'PROJECT_NAME', // 可以根据需要调整
            'PROJECT': 'PROJECT_NAME',

            // 版本信息
            'version': '1.0',
            'VERSION': '1.0',

            // 其他常用占位符
            'company': 'Your Company Name', // 可以配置
            'COMPANY': 'YOUR COMPANY NAME'
        };
    }

    /**
     * 生成输出文件名
     */
    private generateOutputFileName(item: ADaMItem, outputType: OutputType): string {
        if (item.hasTitle && item.outputName) {
            // TLF类型的输出 - 使用直接来自Excel的Output Name
            if (outputType === 'Validation') {
                // Validation程序输出.lst文��，使用原始的outputName
                return `${item.outputName}.lst`;
            } else {
                // Production程序保持原来的.rtf格式
                return `${item.outputName}.rtf`;
            }
        } else {
            // 标准ADAM输出
            const prefix = outputType === 'Production' ? '' : 'v_';
            if (outputType === 'Validation') {
                // Validation程序输出.lst文件
                return `${prefix}${item.domain.toLowerCase()}.lst`;
            } else {
                // Production程序保持原来的.sas7bdat格式
                return `${prefix}${item.domain.toLowerCase()}.sas7bdat`;
            }
        }
    }

    /**
     * 生成所有相关输出文件列表
     * 处理一个程序可能有多个输出文件的情况
     */
    private generateAllOutputFiles(items: ADaMItem[], currentItem: ADaMItem, outputType: OutputType): string {
        // 获取程序名用于匹配
        const currentProgramName = outputType === 'Production'
            ? currentItem.prodProgram
            : currentItem.valProgram;

        if (!currentProgramName) {
            // 如果没有程序名，只返回当前项的输出
            return this.generateOutputFileName(currentItem, outputType);
        }

        // 查找所有使用相同程序名的项目
        const relatedItems = items.filter(item => {
            const itemProgramName = outputType === 'Production'
                ? item.prodProgram
                : item.valProgram;
            return itemProgramName === currentProgramName;
        });

        // 如果只有一个输出文件，直接返��输出文件名
        if (relatedItems.length === 1) {
            return this.generateOutputFileName(currentItem, outputType);
        }

        // 多个输出文件时，生成对齐的列表
        const outputFiles = relatedItems.map((item, index) => {
            const fileName = this.generateOutputFileName(item, outputType);

            // 第一行不需要前缀，后续行需要对齐
            if (index === 0) {
                return fileName;
            } else {
                return `*                     ${fileName}`;
            }
        });

        return outputFiles.join('\n');
    }

    /**
     * 生成程序目的描述
     */
    private generatePurposeDescription(item: ADaMItem, outputType: OutputType, allItems?: ADaMItem[]): string {
        if (item.hasTitle && item.outputTitle) {
            // TLF类型：处理多个输出的情况
            const currentProgramName = outputType === 'Production'
                ? item.prodProgram
                : item.valProgram;

            if (!currentProgramName || !allItems) {
                // 单个输出的情况
                const outputType = item.outputType || '';
                const outputNumber = item.outputNumber || '';
                const outputTitle = item.outputTitle || '';

                const parts = [outputType, outputNumber, outputTitle].filter(part => part && part.trim().length > 0);
                const fullDescription = parts.join(' ');

                const action = outputType === 'Production' ? 'Generate' : 'Validate';
                return `${action} ${fullDescription}`;
            } else {
                // 查找所有使用相同程序名的项目
                const relatedItems = allItems.filter(relatedItem => {
                    const itemProgramName = outputType === 'Production'
                        ? relatedItem.prodProgram
                        : relatedItem.valProgram;
                    return itemProgramName === currentProgramName;
                });

                if (relatedItems.length === 1) {
                    // 单个输出
                    const outputType = item.outputType || '';
                    const outputNumber = item.outputNumber || '';
                    const outputTitle = item.outputTitle || '';

                    const parts = [outputType, outputNumber, outputTitle].filter(part => part && part.trim().length > 0);
                    const fullDescription = parts.join(' ');

                    const action = outputType === 'Production' ? 'Generate' : 'Validate';
                    return `${action} ${fullDescription}`;
                } else {
                    // 多个输出的情况，生成对齐的列表
                    const action = outputType === 'Production' ? 'Generate' : 'Validate';
                    const purposes = relatedItems.map((relatedItem, index) => {
                        const outputType = relatedItem.outputType || '';
                        const outputNumber = relatedItem.outputNumber || '';
                        const outputTitle = relatedItem.outputTitle || '';

                        const parts = [outputType, outputNumber, outputTitle].filter(part => part && part.trim().length > 0);
                        const fullDescription = parts.join(' ');

                        // 第一行不需要前缀，后续行需要对齐
                        if (index === 0) {
                            return `${action} ${fullDescription}`;
                        } else {
                            return `*                   ${action} ${fullDescription}`;
                        }
                    });

                    return purposes.join('\n');
                }
            }
        } else {
            // 标准ADAM：生成通用���述
            const action = outputType === 'Production' ? 'Create' : 'Validate';
            const domainName = item.domain.toUpperCase();
            return `${action} ${domainName} dataset`;
        }
    }

    /**
     * 首字母大写
     */
    private capitalizeFirst(str: string): string {
        return str.charAt(0).toUpperCase() + str.slice(1).toLowerCase();
    }

    private getDefaultProductionTemplate(): string {
        return `/*******************************************************************************
* Program Name: @@domain.sas
* Purpose: Production program for @@DOMAIN dataset
* Programmer: @@programmer
* Date: @@date
* Program: @@program
*******************************************************************************/

%*--- Setup environment ---*;
options symbolgen mprint mlogic;
%let pgm = @@domain;

%*--- Set up library references ---*;
libname adam "path/to/adam";
libname raw "path/to/raw";

%*--- Create @@DOMAIN dataset ---*;
data adam.@@domain;
    set raw.source_data;
    
    %*--- Add your data processing logic here ---*;
    %*--- Example: Create required ADaM variables ---*;
    
    %*--- Subject-level variables ---*;
    STUDYID = "STUDY001";
    USUBJID = strip(STUDYID) || "-" || strip(SUBJID);
    
    %*--- Analysis variables ---*;
    PARAMCD = "@@DOMAIN";
    PARAM = "@@DOMAIN Analysis Parameter";
    
    %*--- Timing variables ---*;
    format ADT ADTM datetime20.;
    
run;

%*--- Generate summary ---*;
proc contents data=adam.@@domain;
run;

proc freq data=adam.@@domain;
    tables PARAMCD*PARAM / list missing;
run;

%*--- End of program ---*;`;
    }

    private getDefaultValidationTemplate(): string {
        return `/*******************************************************************************
* Program Name: v_@@domain.sas
* Purpose: Validation program for @@DOMAIN dataset
* Programmer: @@programmer
* Date: @@date
* Program: @@program
*******************************************************************************/

%*--- Setup environment ---*;
options symbolgen mprint mlogic;
%let pgm = v_@@domain;

%*--- Set up library references ---*;
libname vadam "path/to/validation/adam";
libname padam "path/to/production/adam";

%*--- Compare production and validation datasets ---*;
proc compare base=padam.@@domain compare=vadam.@@domain 
             out=work.diff_@@domain outnoequal;
    id USUBJID PARAMCD;
run;

%*--- Check for differences ---*;
proc freq data=work.diff_@@domain;
    tables _TYPE_ / list missing;
    title "Comparison Results for @@DOMAIN";
run;

%*--- Summary statistics ---*;
proc means data=padam.@@domain n nmiss min max mean std;
    class PARAMCD;
    var AVAL;
    title "Production @@DOMAIN Summary";
run;

proc means data=vadam.@@domain n nmiss min max mean std;
    class PARAMCD;
    var AVAL;
    title "Validation @@DOMAIN Summary";
run;

%*--- End of validation program ---*;`;
    }

    /**
     * 获取显示内容 - 用于Title列显示
     */
    private getDisplayContent(item: ADaMItem): string {
        if (item.hasTitle && item.outputType && item.outputNumber && item.outputTitle) {
            // TLF类型数据：拼接 Output Type + Output # + Title
            const parts = [item.outputType, item.outputNumber, item.outputTitle].filter(part => part && part.length > 0);
            return parts.join(' ');
        }
        // 普通数据或TLF数据缺少字段时，返回domain
        return item.domain || '-';
    }

    /**
     * 从CDN加载脚本
     */
    private loadScriptFromCDN(url: string): Promise<void> {
        return new Promise((resolve, reject) => {
            // 检查是否已经加载过
            const existingScript = document.querySelector(`script[src="${url}"]`);
            if (existingScript) {
                resolve();
                return;
            }

            const script = document.createElement('script');
            script.src = url;
            script.onload = () => {
                console.log(`Script loaded successfully from: ${url}`);
                resolve();
            };
            script.onerror = (error) => {
                console.error(`Failed to load script from: ${url}`, error);
                reject(new Error(`Failed to load script from CDN: ${url}`));
            };
            document.head.appendChild(script);
        });
    }

    // 新增：生成单独的文件（不打包成ZIP），用于上传到服务器
    async generateFiles(
        items: ADaMItem[],
        outputType: OutputType,
        onProgress?: (percent: number) => void
    ): Promise<{ name: string; content: string }[]> {
        console.log('=== Starting files generation ===');
        console.log('Items to process:', items.length);
        console.log('Output type:', outputType);

        const files: { name: string; content: string }[] = [];

        try {
            // 生成所有文件
            items.forEach((item, index) => {
                try {
                    const content = this.generateCode(item, outputType);
                    const fileName = this.getFileName(item, outputType);

                    console.log(`Creating file ${index + 1}/${items.length}: ${fileName}`);
                    files.push({
                        name: fileName,
                        content: content
                    });

                    if (onProgress) {
                        const progressPercent = Math.round(((index + 1) / items.length) * 100);
                        onProgress(progressPercent);
                    }
                } catch (error) {
                    console.error(`Error creating file for ${item.domain}:`, error);
                }
            });

            console.log(`Generated ${files.length} files successfully`);
            return files;

        } catch (error) {
            console.error('Files generation failed:', error);
            throw new Error(`Failed to generate files: ${(error as Error).message}`);
        }
    }

    async generateZip(
        items: ADaMItem[],
        outputType: OutputType,
        customZipName?: string,
        onProgress?: (percent: number) => void
    ): Promise<void> {
        console.log('=== Starting ZIP generation ===');
        console.log('Items to process:', items.length);
        console.log('Output type:', outputType);

        try {
            // Load dependencies
            console.log('Loading dependencies...');
            let JSZip: any;
            let saveAs: any;

            try {
                const jszipModule = await import('jszip');
                JSZip = jszipModule.default || jszipModule;
                console.log('JSZip loaded from npm package');
            } catch (npmError) {
                console.log('Loading JSZip from CDN...');
                await this.loadScriptFromCDN('https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js');
                JSZip = (window as any).JSZip;
                if (!JSZip) throw new Error('JSZip failed to load from CDN');
            }

            try {
                const fileSaverModule = await import('file-saver');
                saveAs = fileSaverModule.saveAs || fileSaverModule.default?.saveAs;
            } catch (npmError) {
                await this.loadScriptFromCDN('https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js');
                saveAs = (window as any).saveAs;
                if (!saveAs) throw new Error('FileSaver failed to load from CDN');
            }

            // Create ZIP file
            const zip = new JSZip();
            const folderName = customZipName || `ADaM_Programs_${outputType}`;
            const programsFolder = zip.folder(folderName);
            if (!programsFolder) throw new Error('Failed to create programs folder');

            // Generate files using the new generateCode method
            items.forEach((item, index) => {
                try {
                    const content = this.generateCode(item, outputType);
                    const fileName = this.getFileName(item, outputType);

                    console.log(`Creating file ${index + 1}/${items.length}: ${fileName}`);
                    programsFolder.file(fileName, content);

                    if (onProgress) {
                        const progressPercent = Math.round(((index + 1) / items.length) * 50);
                        onProgress(progressPercent);
                    }
                } catch (error) {
                    console.error(`Error creating file for ${item.domain}:`, error);
                }
            });

            // Generate ZIP blob
            const zipBlob = await zip.generateAsync({
                type: 'blob',
                compression: 'DEFLATE',
                compressionOptions: { level: 6 }
            }, (metadata) => {
                const progressPercent = 50 + Math.round(metadata.percent / 2);
                if (onProgress) onProgress(progressPercent);
            });

            // Download
            const timestamp = new Date().toISOString().slice(0, 10);
            const fileName = customZipName
                ? (customZipName.endsWith('.zip') ? customZipName : `${customZipName}.zip`)
                : `ADaM_Programs_${outputType}_${timestamp}.zip`;

            saveAs(zipBlob, fileName);
            if (onProgress) onProgress(100);

        } catch (error) {
            console.error('ZIP generation failed:', error);
            throw new Error(`Failed to generate ZIP file: ${(error as Error).message}`);
        }
    }
}

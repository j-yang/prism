export interface ReferenceTemplate {
    name: string;
    path: string;
    content: string;
    type: 'sdtm' | 'adam';
}

export interface TemplateMatch {
    programName: string;
    matchedTemplate: ReferenceTemplate | null;
    useReference: boolean; // 用户选择是否使用引用模板
}

export class ReferenceTemplateService {
    private referenceTemplates: Map<string, ReferenceTemplate> = new Map();

    constructor() {
        // 构造函数保持简单
    }

    async loadReferenceTemplates(): Promise<void> {
        try {
            // 加载SDTM引用模板 - 使用预定义的模板列表
            await this.loadPredefinedTemplates();
        } catch (error) {
            console.error('Failed to load reference templates:', error);
        }
    }

    private async loadPredefinedTemplates(): Promise<void> {
        // 预定义的SDTM模板列表
        const sdtmTemplates = [
            'ae', 'ce', 'cm', 'co', 'cv', 'dd', 'dm', 'ds', 'dv', 'ec', 'eg', 'ex',
            'fa', 'faae', 'face', 'faho', 'ft', 'ho', 'ie', 'is', 'lb', 'mh', 'mi',
            'oe', 'pc', 'pd', 'pr', 'qs', 'rp', 'se', 'su', 'sv', 'ta', 'te', 'ti',
            'ts', 'tv', 'vs'
        ];

        for (const templateName of sdtmTemplates) {
            try {
                const content = await this.loadTemplateContent(`/references/sdtm/prod/${templateName}.sas`);
                if (content) {
                    this.referenceTemplates.set(templateName, {
                        name: templateName,
                        path: `/references/sdtm/prod/${templateName}.sas`,
                        content,
                        type: 'sdtm'
                    });
                }
            } catch (error) {
                console.warn(`Failed to load template ${templateName}:`, error);
                // 为未找到的模板创建占位符
                this.referenceTemplates.set(templateName, {
                    name: templateName,
                    path: `/references/sdtm/prod/${templateName}.sas`,
                    content: this.getDefaultTemplate(templateName),
                    type: 'sdtm'
                });
            }
        }

        console.log(`Loaded ${this.referenceTemplates.size} reference templates`);
    }

    private async loadTemplateContent(path: string): Promise<string> {
        try {
            // 通过fetch获取模板内容
            const response = await fetch(path);
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }
            return await response.text();
        } catch (error) {
            // 如果文件不存在，抛出错误
            throw error;
        }
    }

    private getDefaultTemplate(templateName: string): string {
        return `/*******************************************************************************
* Program Name: ${templateName}.sas
* Purpose: Create ${templateName.toUpperCase()} SDTM dataset
* Programmer: @@programmer
* Date: @@date
* Study: @@study
*******************************************************************************/

%*--- Setup environment ---*;
options symbolgen mprint mlogic;
%let pgm = ${templateName};

%*--- Set up library references ---*;
libname sdtm "path/to/sdtm";
libname raw "path/to/raw";

%*--- Create ${templateName.toUpperCase()} dataset ---*;
data sdtm.${templateName};
    set raw.source_data;
    
    %*--- Standard SDTM variables ---*;
    STUDYID = "@@study";
    DOMAIN = "${templateName.toUpperCase()}";
    USUBJID = strip(STUDYID) || "-" || strip(SUBJID);
    
    %*--- Add domain-specific logic here ---*;
    
run;

%*--- Generate summary ---*;
proc contents data=sdtm.${templateName};
run;

proc freq data=sdtm.${templateName};
    tables DOMAIN / list missing;
run;

%*--- End of program ---*;`;
    }

    findMatchingTemplate(programName: string, type: 'sdtm' | 'adam' = 'sdtm'): ReferenceTemplate | null {
        // 清理程序名称
        const cleanProgramName = programName.toLowerCase()
            .replace(/\.sas$/, '')  // 移除.sas后缀
            .replace(/^v_/, '');    // 移除v_前缀

        return this.referenceTemplates.get(cleanProgramName) || null;
    }

    getTemplateMatches(programNames: string[], type: 'sdtm' | 'adam' = 'sdtm'): TemplateMatch[] {
        return programNames.map(programName => ({
            programName,
            matchedTemplate: this.findMatchingTemplate(programName, type),
            useReference: false // 默认不使用引用模板
        }));
    }

    getAllReferenceTemplates(): ReferenceTemplate[] {
        return Array.from(this.referenceTemplates.values());
    }
}

export const referenceTemplateService = new ReferenceTemplateService();

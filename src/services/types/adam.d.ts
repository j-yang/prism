export interface ADaMItem {
    domain: string;
    prodProgrammer: string | null;
    prodProgram: string | null;
    valProgrammer: string | null;
    valProgram: string | null;
    title?: string;
    hasTitle?: boolean;
    // TLF特有字段
    outputType?: string;
    outputNumber?: string;
    outputTitle?: string;
    outputName?: string; // 新增：直接来自Excel的Output Name字段
}

export type OutputType = 'Production' | 'Validation';

export interface Template {
    id: string;
    name: string;
    content: string;
}
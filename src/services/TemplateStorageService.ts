// 模板本地存储服务
export interface Template {
  id: string;
  name: string;
  description: string;
  type: 'Production' | 'Validation' | 'Custom';
  filename: string;
  content: string;
  created: Date;
  updated: Date;
  isDefault?: boolean; // 标记是否为默认模板
}

export class TemplateStorageService {
  private readonly STORAGE_KEY = 'sas-templates';
  private readonly VERSION_KEY = 'sas-templates-version';
  private readonly CURRENT_VERSION = '1.1.0'; // 强制更新版本号

  // 默认模板（所有用户共享的基础模板）
  private async getDefaultTemplates(): Promise<Template[]> {
    const templates: Template[] = [];

    // 从 public/templates/ 文件夹加载所有模板文件
    const templateFiles = [
      {
        filename: 'adam production template.sas',
        id: 'default-adam-prod',
        name: 'ADaM Production Template',
        description: 'ADaM数据集生产程序标准模板，包含基础数据处理和质量控制流程',
        type: 'Production' as const
      },
      {
        filename: 'adam validation template.sas',
        id: 'default-adam-val',
        name: 'ADaM Validation Template',
        description: 'ADaM数据集验证程序标准模板，用于独立验证和质量检查',
        type: 'Validation' as const
      },
      {
        filename: 'sdtm production template.sas',
        id: 'default-sdtm-prod',
        name: 'SDTM Production Template',
        description: 'SDTM数据集生产程序标准模板，符合CDISC SDTM标准规范',
        type: 'Production' as const
      },
      {
        filename: 'sdtm validation template.sas',
        id: 'default-sdtm-val',
        name: 'SDTM Validation Template',
        description: 'SDTM数据集验证程序标准模板，确保数据质量和合规性',
        type: 'Validation' as const
      },
      {
        filename: 'tlf_dev_template_code.sas',
        id: 'default-tlf-dev',
        name: 'TLF Development Template',
        description: 'Tables, Listings & Figures开发模板，用于统计报告和图表生成',
        type: 'Production' as const
      },
      {
        filename: 'tlf_val_template_code.sas',
        id: 'default-tlf-val',
        name: 'TLF Validation Template',
        description: 'TLF验证程序模板，用于独立验证统计输出的准确性',
        type: 'Validation' as const
      }
    ];

    for (const templateInfo of templateFiles) {
      try {
        // 对文件名进行URL编码以处理空格
        const encodedFilename = encodeURIComponent(templateInfo.filename);
        const response = await fetch(`/templates/${encodedFilename}`);

        if (!response.ok) {
          console.warn(`Failed to load template: ${templateInfo.filename} (status: ${response.status})`);
          continue;
        }
        const content = await response.text();

        templates.push({
          id: templateInfo.id,
          name: templateInfo.name,
          description: templateInfo.description,
          type: templateInfo.type,
          filename: templateInfo.filename,
          isDefault: true,
          content: content,
          created: new Date('2024-01-01'),
          updated: new Date('2024-01-15')
        });
      } catch (error) {
        console.warn(`Error loading template ${templateInfo.filename}:`, error);
      }
    }

    console.log(`✅ 成功从 public/templates/ 文件夹加载了 ${templates.length} 个默认模板`);
    return templates;
  }

  // 初始化本地存储
  private async initializeStorage(): Promise<void> {
    const version = localStorage.getItem(this.VERSION_KEY);
    const existingTemplates = this.getStoredTemplates();

    // 如果是首次使用或版本更新，初始化默认模板
    if (!version || version !== this.CURRENT_VERSION || existingTemplates.length === 0) {
      try {
        const defaultTemplates = await this.getDefaultTemplates();
        this.saveTemplatesToStorage(defaultTemplates);
        localStorage.setItem(this.VERSION_KEY, this.CURRENT_VERSION);
        console.log('✅ 模板库已初始化，从 public/templates/ 加载了默认模板');
      } catch (error) {
        console.error('❌ 无法从 public/templates/ 加载模板文件:', error);
        throw new Error('模板文件加载失败，请确保 public/templates/ 文件夹中存在模板文件');
      }
    }
  }

  // 从本地存储获取模板
  private getStoredTemplates(): Template[] {
    try {
      const stored = localStorage.getItem(this.STORAGE_KEY);
      if (!stored) return [];

      const templates = JSON.parse(stored);
      // 转换日期字符串回Date对象
      return templates.map((t: any) => ({
        ...t,
        created: new Date(t.created),
        updated: new Date(t.updated)
      }));
    } catch (error) {
      console.warn('读取模板数据失败:', error);
      return [];
    }
  }

  // 保存模板到本地存储
  private saveTemplatesToStorage(templates: Template[]): void {
    try {
      localStorage.setItem(this.STORAGE_KEY, JSON.stringify(templates));
    } catch (error) {
      console.error('保存模板数据失败:', error);
      throw new Error('模板保存失败，可能是存储空间不足');
    }
  }

  // 获取所有模板
  async getAllTemplates(): Promise<Template[]> {
    await this.initializeStorage();
    return this.getStoredTemplates();
  }

  // 保存模板
  saveTemplate(template: Template): void {
    const templates = this.getStoredTemplates();
    const existingIndex = templates.findIndex(t => t.id === template.id);

    if (existingIndex >= 0) {
      // 更新现有模板
      templates[existingIndex] = { ...template, updated: new Date() };
    } else {
      // 添加新模板
      templates.push({ ...template, created: new Date(), updated: new Date() });
    }

    this.saveTemplatesToStorage(templates);
  }

  // 删除模板
  deleteTemplate(id: string): boolean {
    const templates = this.getStoredTemplates();
    const template = templates.find(t => t.id === id);

    // 不允许删除默认模板
    if (template?.isDefault) {
      throw new Error('不能删除默认模板');
    }

    const filteredTemplates = templates.filter(t => t.id !== id);
    if (filteredTemplates.length === templates.length) {
      return false; // 没有找到要删除的模板
    }

    this.saveTemplatesToStorage(filteredTemplates);
    return true;
  }

  // 重置为默认模板（清除所有自定义模板）
  async resetToDefault(): Promise<void> {
    try {
      const defaultTemplates = await this.getDefaultTemplates();
      this.saveTemplatesToStorage(defaultTemplates);
      console.log('✅ 已重置为默认模板');
    } catch (error) {
      console.error('❌ 重置模板失败，无法从 public/templates/ 加载:', error);
      throw new Error('重置失败，无法加载默认模板文件');
    }
  }

  // 导出模板数据（用于备份）
  exportTemplates(): string {
    const templates = this.getStoredTemplates();
    return JSON.stringify(templates, null, 2);
  }

  // 导入模板数据（用于恢复）
  importTemplates(jsonData: string): void {
    try {
      const templates = JSON.parse(jsonData);
      // 验证数据格式
      if (!Array.isArray(templates)) {
        throw new Error('无效的模板数据格式');
      }

      // 转���并保存
      const validatedTemplates = templates.map((t: any) => ({
        ...t,
        created: new Date(t.created),
        updated: new Date(t.updated)
      }));

      this.saveTemplatesToStorage(validatedTemplates);
      console.log('✅ 模板导入成功');
    } catch (error) {
      console.error('导入模板失败:', error);
      throw new Error('模板导入失败，请检查数据格式');
    }
  }

  // 获取存储使用情况
  getStorageInfo(): { used: number; total: number; percentage: number } {
    try {
      const data = localStorage.getItem(this.STORAGE_KEY) || '';
      const used = new Blob([data]).size;
      const total = 5 * 1024 * 1024; // 假设5MB限制
      return {
        used,
        total,
        percentage: Math.round((used / total) * 100)
      };
    } catch {
      return { used: 0, total: 0, percentage: 0 };
    }
  }
}

// 导出单例实例
export const templateStorage = new TemplateStorageService();

export interface ServerFile {
  name: string;
  type: 'file' | 'directory';
  size?: number;
  lastModified?: Date;
  path: string;
}

export interface ServerConnection {
  host: string;
  port: number;
  username: string;
  password: string;
  protocol: 'sftp' | 'ftp';
}

export interface UploadProgress {
  fileName: string;
  progress: number;
  status: 'uploading' | 'completed' | 'error';
  error?: string;
}

export interface FileConflict {
  fileName: string;
  localFile: File;
  remoteFile: ServerFile;
  remotePath: string;
  shouldOverwrite: boolean;
}

export interface ConflictResolution {
  conflicts: FileConflict[];
  overwriteAll: boolean;
  skipAll: boolean;
}

export class ServerFileManager {
  private connection: ServerConnection | null = null;
  private currentPath: string = '/';
  private isConnected: boolean = false;

  // 连接到服务器
  async connect(connection: ServerConnection): Promise<boolean> {
    try {
      // 检查是否在GitHub Pages环境中
      const isGitHubPages = window.location.hostname.includes('github.io') ||
                            window.location.hostname.includes('pages.github.io');

      if (isGitHubPages) {
        console.warn('当前在GitHub Pages环境中，服务器连接功能不可用');
        throw new Error('服务器连接功能在GitHub Pages环境中不可用，请在本地环境中使用此功能');
      }

      console.log('正在连接到服务器:', connection.host);

      // 添加重试逻辑
      const maxRetries = 3;
      let lastError: Error | null = null;

      for (let attempt = 1; attempt <= maxRetries; attempt++) {
        try {
          console.log(`连接尝试 ${attempt}/${maxRetries}`);

          const controller = new AbortController();
          const timeoutId = setTimeout(() => controller.abort(), 60000); // 60秒超时

          // 使用绝对URL来避免路径问题
          const apiUrl = window.location.origin.includes('localhost') || window.location.origin.includes('127.0.0.1')
            ? 'http://localhost:3001/api/server/connect'
            : '/api/server/connect';

          const response = await fetch(apiUrl, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              host: connection.host,
              port: connection.port,
              username: connection.username,
              password: connection.password,
              protocol: connection.protocol,
            }),
            signal: controller.signal,
          });

          clearTimeout(timeoutId);

          if (response.ok) {
            const result = await response.json();
            this.connection = connection;
            this.isConnected = true;
            this.currentPath = result.initialPath || '/home/sasuser';
            console.log('服务器连接成功');
            return true;
          } else {
            // 改进错误处理
            let errorMessage;
            let errorDetails = null;

            try {
              const errorData = await response.json();
              errorMessage = errorData.error || errorData.message || '连接失败';
              errorDetails = errorData.details || null;

              // 记录详细错误信息
              console.error('服务器连接失败详情:', {
                status: response.status,
                statusText: response.statusText,
                error: errorMessage,
                details: errorDetails,
                host: connection.host,
                port: connection.port,
                username: connection.username,
              });

              // ���果是网络繁忙错误，等待后重试
              if (errorMessage.includes('网络连���繁忙') || errorMessage.includes('ENOBUFS')) {
                if (attempt < maxRetries) {
                  console.log(`网络繁忙，等待 ${attempt * 2} 秒后重试...`);
                  await new Promise(resolve => setTimeout(resolve, attempt * 2000));
                  continue;
                }
              }

            } catch (jsonError) {
              // 如果响应不是JSON格式，使用状态码和状态文本
              errorMessage = `连接失败: ${response.status} ${response.statusText}`;
              console.error('服务器连接失败 (非JSON响应):', {
                status: response.status,
                statusText: response.statusText,
                host: connection.host,
                port: connection.port,
                username: connection.username,
              });
            }

            // 如果是最后一次尝试，抛出错误
            if (attempt === maxRetries) {
              throw new Error(errorMessage);
            }
          }
        } catch (fetchError: any) {
          lastError = fetchError;
          console.error(`连接尝试 ${attempt} 失败:`, fetchError);

          // 检查是否是网络相关错误
          if (fetchError.name === 'AbortError') {
            console.log('连接超时');
            if (attempt < maxRetries) {
              console.log(`等待 ${attempt * 2} 秒后重试...`);
              await new Promise(resolve => setTimeout(resolve, attempt * 2000));
              continue;
            }
          } else if (fetchError.message.includes('Failed to fetch') ||
                     fetchError.message.includes('network') ||
                     fetchError.message.includes('ENOBUFS')) {
            console.log('网络错误，准备重试...');
            if (attempt < maxRetries) {
              console.log(`等待 ${attempt * 2} 秒后重试...`);
              await new Promise(resolve => setTimeout(resolve, attempt * 2000));
              continue;
            }
          }

          // 如果是最后一次尝试，重新抛出错误
          if (attempt === maxRetries) {
            throw fetchError;
          }
        }
      }

      // 如果所有重试都失败了
      throw lastError || new Error('连接失败');

    } catch (error) {
      console.error('连接失败:', error);
      this.isConnected = false;
      this.connection = null;

      // 提供用户友好的错误消息
      let userMessage = '连接失败';
      if (error instanceof Error) {
        if (error.message.includes('网络连接繁忙') || error.message.includes('ENOBUFS')) {
          userMessage = '网络连接繁忙，请稍后重试';
        } else if (error.message.includes('timeout') || error.name === 'AbortError') {
          userMessage = '连接超时，请检查网络连接';
        } else if (error.message.includes('Failed to fetch')) {
          userMessage = '无法连接到服务器，请检查服务器是否运行';
        } else {
          userMessage = error.message;
        }
      }

      throw new Error(userMessage);
    }
  }

  // 断���连接
  async disconnect(): Promise<void> {
    if (this.isConnected) {
      try {
        await fetch('/api/server/disconnect', {
          method: 'POST',
        });
      } catch (error) {
        console.error('断开连接时出错:', error);
      }
      this.connection = null;
      this.isConnected = false;
      this.currentPath = '/';
    }
  }

  // 获取当前目录文件列表
  async listFiles(path?: string): Promise<ServerFile[]> {
    if (!this.isConnected) {
      throw new Error('未连接到服务器');
    }

    const targetPath = path || this.currentPath;

    try {
      console.log('正在获取文件列表:', targetPath);

      // 强制使用生产环境API
      const response = await fetch(
        `/api/server/files?path=${encodeURIComponent(targetPath)}`
      );
      if (response.ok) {
        const files = await response.json();
        console.log('获取到文件列表:', files.length, '个项目');
        return files.map((file: any) => ({
          name: file.name,
          type: file.type,
          size: file.size,
          lastModified: file.lastModified
            ? new Date(file.lastModified)
            : undefined,
          path: file.path,
        }));
      }
      const errorMessage = `获取文件列表失败: ${response.status} ${response.statusText}`;
      console.error(errorMessage);
      throw new Error(errorMessage);
    } catch (error) {
      console.error('获取文件列表失败:', error);
      if (error instanceof Error) {
        throw error;
      }
      throw new Error('获取文件列表失败');
    }
  }

  // 上传文件
  async uploadFile(
    file: File,
    remotePath: string,
    onProgress?: (progress: UploadProgress) => void
  ): Promise<boolean> {
    if (!this.isConnected) {
      throw new Error('未连接到服务器');
    }

    console.log('正在上传文件:', file.name, '到', remotePath);

    // 强制��用生产环境API进行实际上传
    const formData = new FormData();
    formData.append('file', file);
    formData.append('path', remotePath);

    try {
      const xhr = new XMLHttpRequest();

      return new Promise((resolve, reject) => {
        xhr.upload.addEventListener('progress', (e) => {
          if (e.lengthComputable && onProgress) {
            const progress = (e.loaded / e.total) * 100;
            onProgress({
              fileName: file.name,
              progress,
              status: 'uploading',
            });
          }
        });

        xhr.addEventListener('load', () => {
          if (xhr.status === 200) {
            console.log('文件上传成功:', file.name);
            if (onProgress) {
              onProgress({
                fileName: file.name,
                progress: 100,
                status: 'completed',
              });
            }
            resolve(true);
          } else {
            const errorMessage = xhr.responseText || '上传失败';
            console.error('文件上传失败:', errorMessage);
            if (onProgress) {
              onProgress({
                fileName: file.name,
                progress: 0,
                status: 'error',
                error: errorMessage,
              });
            }
            reject(new Error(errorMessage));
          }
        });

        xhr.addEventListener('error', () => {
          console.error('上传过程中发生网络错误');
          if (onProgress) {
            onProgress({
              fileName: file.name,
              progress: 0,
              status: 'error',
              error: '网络错误',
            });
          }
          reject(new Error('网络错误'));
        });

        xhr.open('POST', '/api/server/upload');

        // 添加连接ID到请求头
        if (this.connection) {
          const connectionId = `${this.connection.username}@${this.connection.host}:${this.connection.port}`;
          xhr.setRequestHeader('connection-id', connectionId);
        }

        xhr.send(formData);
      });
    } catch (error) {
      console.error('上传文件失败:', error);
      throw error;
    }
  }

  // 移除创建目录和删除文件功能（生产环境不需要）
  // 保留方法但返回false，避免前端调用出错
  async createDirectory(_path: string, _name: string): Promise<boolean> {
    console.warn('生产环境不支持创建目录功能');
    return false;
  }

  async deleteFile(_path: string): Promise<boolean> {
    console.warn('生产环境不支持删除文件功能');
    return false;
  }

  // 获取当前路径
  getCurrentPath(): string {
    return this.currentPath;
  }

  // 检查连接状态
  isConnectionActive(): boolean {
    return this.isConnected;
  }

  // 添加缺失的方法 - 检查是否已连接
  isServerConnected(): boolean {
    return this.isConnected;
  }

  // 获取当前连接信息
  getConnection(): ServerConnection | null {
    return this.connection;
  }

  // 检查文件是否存在
  async checkFileExists(remotePath: string): Promise<ServerFile | null> {
    if (!this.isConnected) {
      throw new Error('未连接到服务器');
    }

    try {
      const response = await fetch(`/api/server/file-exists?path=${encodeURIComponent(remotePath)}`);
      if (response.ok) {
        const result = await response.json();
        return result.exists ? result.file : null;
      }
      return null;
    } catch (error) {
      console.error('检查文件是否存在失败:', error);
      return null;
    }
  }

  // 批量检查文件冲突
  async checkFileConflicts(files: Array<{file: File, remotePath: string}>): Promise<FileConflict[]> {
    if (!this.isConnected) {
      throw new Error('未连接到服务器');
    }

    console.log('🔍 开始检查文件冲突，共', files.length, '个文件');
    const conflicts: FileConflict[] = [];

    for (const {file, remotePath} of files) {
      console.log('检查文件:', file.name, '-> 远程路径:', remotePath);
      const remoteFile = await this.checkFileExists(remotePath);
      if (remoteFile) {
        console.log('⚠️ 发现冲突:', file.name);
        conflicts.push({
          fileName: file.name,
          localFile: file,
          remoteFile,
          remotePath,
          shouldOverwrite: false
        });
      } else {
        console.log('✅ 无冲突:', file.name);
      }
    }

    console.log('冲突检查完成，发现', conflicts.length, '个冲突');
    return conflicts;
  }
}

// 单例模式
export const serverFileManager = new ServerFileManager();

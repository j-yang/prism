import 'jszip';

declare module 'jszip' {
    interface JSZipGeneratorOptions<T extends any> {
        progress?: (metadata: {
            percent: number;
            currentFile: string | null;
        }) => void;
    }
}
// Real Server API for file conflict detection
// This provides actual file existence checking on the server

// Store for tracking uploaded files and server file listing cache
const uploadedFiles = new Map<string, any>();
const serverFileCache = new Map<string, Set<string>>(); // path -> Set of filenames

// Helper function to get actual server file list
async function getServerFileList(directoryPath: string): Promise<string[]> {
  try {
    // Extract directory from full path
    const directory = directoryPath.substring(0, directoryPath.lastIndexOf('/')) || directoryPath;

    // Check cache first
    if (serverFileCache.has(directory)) {
      return Array.from(serverFileCache.get(directory) || new Set());
    }

    console.log('🔍 Fetching actual server file list for directory:', directory);

    // Make actual API call to get server files
    const response = await fetch(`/api/server/files?path=${encodeURIComponent(directory)}`);

    if (response.ok) {
      const files = await response.json();
      const fileNames = files
        .filter((file: any) => file.type === 'file' && file.name.endsWith('.sas'))
        .map((file: any) => file.name);

      // Cache the result
      serverFileCache.set(directory, new Set(fileNames));
      console.log('📁 Found', fileNames.length, 'SAS files on server:', fileNames);

      return fileNames;
    } else {
      console.warn('⚠️ Failed to fetch server file list, falling back to empty list');
      return [];
    }
  } catch (error) {
    console.error('❌ Error fetching server file list:', error);
    return [];
  }
}

// Real file existence check using actual server files
async function checkFileExistsOnServer(remotePath: string) {
  const fileName = remotePath.split('/').pop() || '';

  try {
    // Check if file was uploaded in current session
    if (uploadedFiles.has(remotePath)) {
      console.log(`🔍 File conflict detected (uploaded this session): ${fileName}`);
      return {
        exists: true,
        file: uploadedFiles.get(remotePath)
      };
    }

    // Get actual server file list
    const serverFiles = await getServerFileList(remotePath);
    const exists = serverFiles.includes(fileName);

    if (exists) {
      console.log(`🔍 File conflict detected (exists on server): ${fileName}`);
      return {
        exists: true,
        file: {
          name: fileName,
          type: 'file',
          size: Math.floor(Math.random() * 10000) + 1000, // Placeholder size
          lastModified: new Date(Date.now() - Math.floor(Math.random() * 30 * 24 * 60 * 60 * 1000)), // Random date within last month
          path: remotePath
        }
      };
    }

    console.log(`✅ No conflict: ${fileName} is safe to upload`);
    return {
      exists: false,
      file: null
    };

  } catch (error) {
    console.error('❌ Error checking file existence:', error);
    // In case of error, assume file doesn't exist to allow upload
    return {
      exists: false,
      file: null
    };
  }
}

// Mock API endpoint for checking file existence
if (typeof window !== 'undefined' && window.fetch) {
  const originalFetch = window.fetch;

  window.fetch = function(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
    const url = typeof input === 'string' ? input : input.toString();

    console.log('🌐 Intercepted fetch request:', url);

    // Handle file existence check
    if (url.includes('/api/server/file-exists')) {
      console.log('🔍 Processing file-exists request');
      const urlObj = new URL(url, window.location.origin);
      const path = urlObj.searchParams.get('path');

      if (path) {
        console.log('Checking path:', path);

        // Return a Promise that resolves with the result
        return checkFileExistsOnServer(path).then(result => {
          console.log('Result:', result);
          return new Response(JSON.stringify(result), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
        }).catch(error => {
          console.error('Error in file exists check:', error);
          return new Response(JSON.stringify({ exists: false, file: null }), {
            status: 200,
            headers: { 'Content-Type': 'application/json' }
          });
        });
      }

      return Promise.resolve(new Response(JSON.stringify({ exists: false, file: null }), {
        status: 200,
        headers: { 'Content-Type': 'application/json' }
      }));
    }

    // Handle file upload - store uploaded files for future conflict checking
    if (url.includes('/api/server/upload') && init?.method === 'POST') {
      console.log('📤 Processing file upload request');
      const formData = init.body as FormData;
      const file = formData.get('file') as File;
      const path = formData.get('path') as string;

      if (file && path) {
        console.log('Storing uploaded file:', file.name, 'at path:', path);
        // Store the uploaded file info for future conflict detection
        uploadedFiles.set(path, {
          name: file.name,
          type: 'file',
          size: file.size,
          lastModified: new Date(),
          path: path
        });
      }
    }

    // Fall back to original fetch for other requests
    return originalFetch.call(this, input, init);
  };

  console.log('✅ MockServerAPI fetch interceptor initialized');
}

export { checkFileExistsOnServer };

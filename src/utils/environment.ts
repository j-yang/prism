// Environment detection utilities for PRISM Platform

export interface EnvironmentInfo {
  isProduction: boolean;
  isGitHubPages: boolean;
  isLocalDevelopment: boolean;
  hasServerAPI: boolean;
  baseUrl: string;
  apiBaseUrl: string;
}

export function detectEnvironment(): EnvironmentInfo {
  const hostname = window.location.hostname;
  const origin = window.location.origin;
  const protocol = window.location.protocol;

  // Detect GitHub Pages
  const isGitHubPages = hostname.includes('github.io') ||
                        hostname.includes('pages.github.io');

  // Detect local development
  const isLocalDevelopment = hostname === 'localhost' ||
                             hostname === '127.0.0.1' ||
                             hostname.startsWith('192.168.') ||
                             hostname.startsWith('10.') ||
                             hostname.includes('local');

  // Determine if this is production
  const isProduction = !isLocalDevelopment;

  // Determine if server API is available
  const hasServerAPI = isLocalDevelopment;

  // Set base URLs
  const baseUrl = isGitHubPages ? '/prism/' : '/';
  const apiBaseUrl = isLocalDevelopment ? 'http://localhost:3001' : '';

  return {
    isProduction,
    isGitHubPages,
    isLocalDevelopment,
    hasServerAPI,
    baseUrl,
    apiBaseUrl
  };
}

export function getApiUrl(endpoint: string): string {
  const env = detectEnvironment();

  if (env.isLocalDevelopment) {
    return `${env.apiBaseUrl}${endpoint}`;
  }

  // For production/GitHub Pages, API endpoints don't exist
  return endpoint;
}

export function showServerUnavailableWarning(): void {
  const env = detectEnvironment();

  if (env.isGitHubPages) {
    console.warn(`
🚨 PRISM Platform - Server Features Unavailable

You are currently viewing the PRISM Platform on GitHub Pages.
Server connection and file upload features are not available in this environment.

To use the full functionality including server connections:
1. Clone the repository locally
2. Run 'npm install' in both root and server directories
3. Start the development server with 'npm run dev'

GitHub Pages version is for demonstration purposes only.
    `);
  }
}

// Initialize environment detection on module load
export const ENVIRONMENT = detectEnvironment();

// Log environment info in development
if (ENVIRONMENT.isLocalDevelopment) {
  console.log('🌍 PRISM Environment:', ENVIRONMENT);
}

import { ApiConfig, HttpLog } from '../types';

// Default configuration based on prompt specifications
export const DEFAULT_CONFIG: ApiConfig = {
  // The backend's nginx only terminates TLS (self-signed cert in dev) on these
  // ports — there is no plaintext HTTP listener, so this must be https://.
  authBaseUrl: 'https://localhost:4293',
  coreBaseUrl: 'https://localhost:4294',
  platform: 'mobile', // 'mobile' is recommended in dev because PRODUCTION_MODE=false uses allow_origins=["*"] and allow_credentials=False
  useRealBackend: false, // Default to mock for instant frontend testing, togglable to real backend
  saveTokensInStorage: true,
};

class ApiClient {
  private config: ApiConfig;
  private logs: HttpLog[] = [];
  private logListeners: Array<(logs: HttpLog[]) => void> = [];
  private accessToken: string | null = null;
  private refreshToken: string | null = null;

  constructor() {
    const saved = localStorage.getItem('iip_api_config');
    if (saved) {
      try {
        this.config = { ...DEFAULT_CONFIG, ...JSON.parse(saved) };
      } catch (e) {
        this.config = { ...DEFAULT_CONFIG };
      }
    } else {
      this.config = { ...DEFAULT_CONFIG };
    }

    if (this.config.saveTokensInStorage) {
      this.accessToken = sessionStorage.getItem('iip_access_token');
      this.refreshToken = sessionStorage.getItem('iip_refresh_token');
    }
  }

  public getConfig(): ApiConfig {
    return { ...this.config };
  }

  public updateConfig(newConfig: Partial<ApiConfig>) {
    this.config = { ...this.config, ...newConfig };
    localStorage.setItem('iip_api_config', JSON.stringify(this.config));
  }

  public setTokens(accessToken: string | null, refreshToken: string | null) {
    this.accessToken = accessToken;
    this.refreshToken = refreshToken;
    if (this.config.saveTokensInStorage) {
      if (accessToken) sessionStorage.setItem('iip_access_token', accessToken);
      else sessionStorage.removeItem('iip_access_token');

      if (refreshToken) sessionStorage.setItem('iip_refresh_token', refreshToken);
      else sessionStorage.removeItem('iip_refresh_token');
    }
  }

  public getTokens() {
    return {
      accessToken: this.accessToken,
      refreshToken: this.refreshToken,
    };
  }

  public clearTokens() {
    this.accessToken = null;
    this.refreshToken = null;
    sessionStorage.removeItem('iip_access_token');
    sessionStorage.removeItem('iip_refresh_token');
  }

  public subscribeLogs(listener: (logs: HttpLog[]) => void) {
    this.logListeners.push(listener);
    listener(this.logs);
    return () => {
      this.logListeners = this.logListeners.filter((l) => l !== listener);
    };
  }

  private addLog(log: HttpLog) {
    this.logs = [log, ...this.logs.slice(0, 49)]; // keep latest 50
    this.logListeners.forEach((l) => l(this.logs));
  }

  public getLogs(): HttpLog[] {
    return [...this.logs];
  }

  public clearLogs() {
    this.logs = [];
    this.logListeners.forEach((l) => l(this.logs));
  }

  /**
   * Request dispatcher
   */
  public async request<T = any>(
    service: 'auth' | 'core',
    path: string,
    options: {
      method?: 'GET' | 'POST' | 'PUT' | 'DELETE';
      body?: any;
      headers?: Record<string, string>;
      requiresAuth?: boolean;
      isAuthAction?: 'login' | 'reauth' | 'logout' | 'register' | null;
    } = {}
  ): Promise<{ data: T; status: number; headers: Headers }> {
    const method = options.method || 'GET';
    const baseUrl = service === 'auth' ? this.config.authBaseUrl : this.config.coreBaseUrl;
    // ensure leading slash
    const cleanPath = path.startsWith('/') ? path : `/${path}`;
    const url = `${baseUrl}${cleanPath}`;
    const startTime = Date.now();

    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      'X-Platform': this.config.platform,
      ...(options.headers || {}),
    };

    // Attach Authorization Bearer token if required or available
    if (options.requiresAuth && this.accessToken) {
      headers['Authorization'] = `Bearer ${this.accessToken}`;
    }

    // Attach X-Refresh-Token if in mobile mode for reauth/logout
    if (
      this.config.platform === 'mobile' &&
      (options.isAuthAction === 'reauth' || options.isAuthAction === 'logout') &&
      this.refreshToken
    ) {
      headers['X-Refresh-Token'] = this.refreshToken;
    }

    // If Real Backend is disabled, throw error to let service layer fall back to mock
    if (!this.config.useRealBackend) {
      const mockLog: HttpLog = {
        id: `mock-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        timestamp: new Date().toISOString(),
        method,
        url,
        headers,
        body: options.body,
        status: 200,
        response: { note: 'Mock mode active. Dispatched to local state.' },
        durationMs: 40,
        mode: 'mock',
      };
      this.addLog(mockLog);
      throw new Error('MOCK_MODE_ACTIVE');
    }

    try {
      const fetchOptions: RequestInit = {
        method,
        headers,
      };

      if (options.body && method !== 'GET') {
        fetchOptions.body = JSON.stringify(options.body);
      }

      // In web mode, include credentials for cookies
      if (this.config.platform === 'web') {
        fetchOptions.credentials = 'include';
      }

      const res = await fetch(url, fetchOptions);
      const durationMs = Date.now() - startTime;

      let responseData: any = null;
      const contentType = res.headers.get('content-type');
      if (contentType && contentType.includes('application/json')) {
        try {
          responseData = await res.json();
        } catch {
          responseData = await res.text();
        }
      } else {
        responseData = await res.text();
      }

      const log: HttpLog = {
        id: `req-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        timestamp: new Date().toISOString(),
        method,
        url,
        headers,
        body: options.body,
        status: res.status,
        response: responseData,
        durationMs,
        mode: 'real',
      };
      this.addLog(log);

      // Handle documented backend gap: 500 error on invalid/expired tokens treated as unauthenticated
      if (res.status === 500 && (typeof responseData === 'string' && responseData.toLowerCase().includes('token'))) {
        throw {
          status: 401,
          isTokenError: true,
          message: 'Sesión expirada o token inválido (Servidor devolvió 500 según especificación).',
          data: responseData,
        };
      }

      if (!res.ok) {
        throw {
          status: res.status,
          message: responseData?.message || `Error ${res.status}: ${res.statusText}`,
          data: responseData,
        };
      }

      return {
        data: responseData,
        status: res.status,
        headers: res.headers,
      };
    } catch (err: any) {
      if (err.message === 'MOCK_MODE_ACTIVE') throw err;

      const durationMs = Date.now() - startTime;
      const errorLog: HttpLog = {
        id: `err-${Date.now()}-${Math.random().toString(36).substring(2, 6)}`,
        timestamp: new Date().toISOString(),
        method,
        url,
        headers,
        body: options.body,
        status: err.status || 0,
        response: err.data || { error: err.message || 'Error de conexión con el backend' },
        durationMs,
        mode: 'real',
      };
      this.addLog(errorLog);
      throw err;
    }
  }
}

export const apiClient = new ApiClient();

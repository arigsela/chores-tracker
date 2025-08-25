import { getAPIUrl } from '../api';

describe('API Configuration', () => {
  const originalWindow = global.window;

  beforeEach(() => {
    // Clean up environment variables and window object
    delete process.env.REACT_APP_API_URL;
    global.window = originalWindow;
  });

  afterEach(() => {
    global.window = originalWindow;
  });

  it('should use runtime window.APP_CONFIG.API_URL when available', () => {
    // Mock window with APP_CONFIG
    Object.defineProperty(global, 'window', {
      value: {
        APP_CONFIG: {
          API_URL: 'http://runtime-config.example.com/api/v1'
        }
      },
      writable: true
    });

    const url = getAPIUrl();
    expect(url).toBe('http://runtime-config.example.com/api/v1');
  });

  it('should use build-time REACT_APP_API_URL when window.APP_CONFIG is not available', () => {
    // Mock build-time environment variable
    process.env.REACT_APP_API_URL = 'http://build-time.example.com/api/v1';

    const url = getAPIUrl();
    expect(url).toBe('http://build-time.example.com/api/v1');
  });

  it('should use default localhost when no configuration is available', () => {
    // Ensure no configuration is available
    Object.defineProperty(global, 'window', {
      value: {},
      writable: true
    });

    const url = getAPIUrl();
    expect(url).toBe('http://localhost:8000/api/v1');
  });

  it('should handle server-side rendering (no window object)', () => {
    // Mock server environment (no window)
    delete (global as any).window;

    const url = getAPIUrl();
    expect(url).toBe('http://localhost:8000/api/v1');
  });
});
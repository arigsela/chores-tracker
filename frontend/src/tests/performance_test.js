/**
 * Phase 4.5 - Frontend Performance Testing
 * Tests loading times, render performance, and API response times
 */

const BASE_URL = 'http://localhost:8081';
// Use environment-based API URL or default to localhost for testing
const API_URL = process.env.API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

// Test credentials
const PARENT_USER = { username: 'demoparent', password: 'password123' };
const CHILD_USER = { username: 'demochild1', password: 'password123' };

// Performance thresholds (in ms)
const THRESHOLDS = {
  pageLoad: 3000,      // Full page load
  apiCall: 500,        // API response time
  navigation: 1000,    // Navigation between screens
  listRender: 500,     // Rendering lists of items
  formSubmit: 1000,    // Form submission and response
};

// Performance metrics collector
class PerformanceMetrics {
  constructor() {
    this.metrics = [];
  }

  record(name, duration, threshold) {
    const passed = duration <= threshold;
    this.metrics.push({
      name,
      duration,
      threshold,
      passed,
      status: passed ? '✅' : '❌'
    });
    console.log(`${passed ? '✅' : '❌'} ${name}: ${duration}ms (threshold: ${threshold}ms)`);
  }

  summary() {
    console.log('\n========== PERFORMANCE TEST SUMMARY ==========');
    const passed = this.metrics.filter(m => m.passed).length;
    const total = this.metrics.length;
    
    console.log('\nDetailed Results:');
    this.metrics.forEach(m => {
      console.log(`${m.status} ${m.name}: ${m.duration}ms / ${m.threshold}ms`);
    });
    
    const percentage = (passed / total * 100).toFixed(1);
    console.log(`\nOverall: ${passed}/${total} tests passed (${percentage}%)`);
    
    if (percentage >= 90) {
      console.log('✅ EXCELLENT PERFORMANCE! All critical metrics within thresholds.');
    } else if (percentage >= 75) {
      console.log('⚠️ GOOD PERFORMANCE with some areas for optimization.');
    } else {
      console.log('❌ PERFORMANCE NEEDS IMPROVEMENT. Review slow operations above.');
    }
    
    // Calculate averages
    const avgApiTime = this.metrics
      .filter(m => m.name.includes('API'))
      .reduce((sum, m) => sum + m.duration, 0) / 
      this.metrics.filter(m => m.name.includes('API')).length || 0;
    
    console.log(`\nAverage API response time: ${avgApiTime.toFixed(0)}ms`);
  }
}

// Utility functions
async function measureTime(fn, name, threshold, metrics) {
  const start = performance.now();
  try {
    await fn();
    const duration = Math.round(performance.now() - start);
    metrics.record(name, duration, threshold);
    return duration;
  } catch (error) {
    console.error(`Error in ${name}:`, error);
    metrics.record(name, Infinity, threshold);
    return Infinity;
  }
}

async function login(username, password) {
  const response = await fetch(`${API_URL}/users/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({ username, password })
  });
  const data = await response.json();
  return data.access_token;
}

async function fetchWithAuth(url, token) {
  return fetch(url, {
    headers: { 'Authorization': `Bearer ${token}` }
  });
}

// Performance tests
async function runPerformanceTests() {
  const metrics = new PerformanceMetrics();
  
  console.log('Starting Frontend Performance Tests...');
  console.log('Make sure both backend and frontend are running\n');
  
  try {
    // Test 1: Initial page load
    await measureTime(
      async () => {
        const response = await fetch(BASE_URL);
        await response.text();
      },
      'Initial Page Load',
      THRESHOLDS.pageLoad,
      metrics
    );
    
    // Test 2: Authentication API
    let parentToken;
    await measureTime(
      async () => {
        parentToken = await login(PARENT_USER.username, PARENT_USER.password);
      },
      'API: Authentication',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 3: Fetch children list
    await measureTime(
      async () => {
        const response = await fetchWithAuth(`${API_URL}/users/my-children`, parentToken);
        await response.json();
      },
      'API: Fetch Children',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 4: Fetch chores list
    await measureTime(
      async () => {
        const response = await fetchWithAuth(`${API_URL}/chores/`, parentToken);
        await response.json();
      },
      'API: Fetch Chores',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 5: Fetch pending approvals
    await measureTime(
      async () => {
        const response = await fetchWithAuth(`${API_URL}/chores/pending-approval`, parentToken);
        await response.json();
      },
      'API: Pending Approvals',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 6: Create chore
    await measureTime(
      async () => {
        const choreData = {
          title: `Performance Test Chore ${Date.now()}`,
          description: 'Test chore for performance measurement',
          reward: 5.00,
          is_recurring: false
        };
        const response = await fetch(`${API_URL}/chores/`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${parentToken}`,
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(choreData)
        });
        await response.json();
      },
      'API: Create Chore',
      THRESHOLDS.formSubmit,
      metrics
    );
    
    // Test 7: Fetch allowance summary
    await measureTime(
      async () => {
        const response = await fetchWithAuth(`${API_URL}/users/allowance-summary`, parentToken);
        await response.json();
      },
      'API: Allowance Summary',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 8: Child authentication
    let childToken;
    await measureTime(
      async () => {
        childToken = await login(CHILD_USER.username, CHILD_USER.password);
      },
      'API: Child Authentication',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 9: Child fetch chores
    await measureTime(
      async () => {
        const response = await fetchWithAuth(`${API_URL}/chores/my-chores`, childToken);
        await response.json();
      },
      'API: Child Chores',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 10: Child fetch balance
    await measureTime(
      async () => {
        const response = await fetchWithAuth(`${API_URL}/users/me/balance`, childToken);
        await response.json();
      },
      'API: Child Balance',
      THRESHOLDS.apiCall,
      metrics
    );
    
    // Test 11: Batch API calls (simulate dashboard load)
    await measureTime(
      async () => {
        await Promise.all([
          fetchWithAuth(`${API_URL}/users/my-children`, parentToken).then(r => r.json()),
          fetchWithAuth(`${API_URL}/chores/`, parentToken).then(r => r.json()),
          fetchWithAuth(`${API_URL}/users/allowance-summary`, parentToken).then(r => r.json()),
          fetchWithAuth(`${API_URL}/chores/pending-approval`, parentToken).then(r => r.json())
        ]);
      },
      'Dashboard Load (4 parallel APIs)',
      THRESHOLDS.pageLoad,
      metrics
    );
    
    // Test 12: Create adjustment
    await measureTime(
      async () => {
        // First get a child ID
        const childrenResponse = await fetchWithAuth(`${API_URL}/users/my-children`, parentToken);
        const children = await childrenResponse.json();
        
        if (children.length > 0) {
          const adjustmentData = {
            child_id: children[0].id,
            amount: 5.00,
            reason: 'Performance test adjustment'
          };
          
          const response = await fetch(`${API_URL}/adjustments/`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${parentToken}`,
              'Content-Type': 'application/json'
            },
            body: JSON.stringify(adjustmentData)
          });
          await response.json();
        }
      },
      'API: Create Adjustment',
      THRESHOLDS.formSubmit,
      metrics
    );
    
  } catch (error) {
    console.error('Test suite error:', error);
  }
  
  // Print summary
  metrics.summary();
}

// Run tests if executed directly
if (typeof window === 'undefined') {
  // Node.js environment
  global.performance = require('perf_hooks').performance;
  global.fetch = require('node-fetch');
  runPerformanceTests().then(() => process.exit(0));
} else {
  // Browser environment
  runPerformanceTests();
}

// Export for use in other test suites
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { runPerformanceTests, PerformanceMetrics };
}
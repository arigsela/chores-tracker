// Quick test script to verify chores UI functionality
// Run this in the browser console after logging in as demochild

/* eslint-env browser */
/* global console, window, document, AsyncStorage */

async function testChoresUI() {
  console.log('Testing Chores UI...');
  
  // Check if we're logged in
  const token = await AsyncStorage.getItem('@chores_tracker_token');
  if (!token) {
    console.error('❌ Not logged in! Please login as demochild first.');
    return;
  }
  
  // Check current user
  const userStr = await AsyncStorage.getItem('@chores_tracker_user');
  const user = JSON.parse(userStr);
  console.log('✓ Logged in as:', user.username, '(Role:', user.role, ')');
  
  // Check if we're on the chores screen
  const currentScreen = window.location.pathname;
  if (!currentScreen.includes('chores')) {
    console.log('⚠️ Not on chores screen. Navigate to Chores tab.');
  }
  
  // Check for chore cards
  const choreCards = document.querySelectorAll('[data-testid="chore-card"]');
  console.log(`✓ Found ${choreCards.length} chore cards`);
  
  // Check for available chores tab
  const availableTab = document.querySelector('[data-testid="tab-available"]');
  if (availableTab) {
    console.log('✓ Available tab found');
  } else {
    console.log('❌ Available tab not found');
  }
  
  // Check for complete buttons (child view only)
  if (user.role === 'child') {
    const completeButtons = document.querySelectorAll('[data-testid="complete-chore-button"]');
    console.log(`✓ Found ${completeButtons.length} complete buttons`);
  }
  
  console.log('Test complete!');
}

// Note: To use this, open browser console and paste the function, then call testChoresUI()
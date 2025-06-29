import { HedgeFundAIClient } from './client.js';

async function testClient() {
  const client = new HedgeFundAIClient();
  
  try {
    console.log('Testing Hedge Fund AI MCP Client...');
    
    // Test getting available analysts
    console.log('\n1. Testing getAvailableAnalysts...');
    const analysts = await client.getAvailableAnalysts();
    console.log('Available analysts:', Object.keys(analysts).length);
    
    // Test searching tickers
    console.log('\n2. Testing searchTickers...');
    const tickers = await client.searchTickers('AAPL');
    console.log('Search results for AAPL:', tickers);
    
    // Test health check (this will fail if server is not running)
    console.log('\n3. Testing health check...');
    try {
      const health = await client.getHealth();
      console.log('Health status:', health.status);
    } catch (error) {
      console.log('Health check failed (server may not be running):', error instanceof Error ? error.message : 'Unknown error');
    }
    
    console.log('\nClient test completed successfully!');
    
  } catch (error) {
    console.error('Test failed:', error);
  }
}

// Run test if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  testClient();
} 
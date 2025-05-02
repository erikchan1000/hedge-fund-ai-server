import { NextResponse } from 'next/server';
import tickers from '@/public/tickers.json';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const query = searchParams.get('q')?.toLowerCase() || '';
  const isInitial = searchParams.get('initial') === 'true';

  if (isInitial) {
    // Return first 50 tickers for initial population
    return NextResponse.json(tickers.tickers.slice(0, 50));
  }

  if (!query) {
    return NextResponse.json([]);
  }

  const results = tickers.tickers
    .filter(ticker => ticker.symbol.toLowerCase().includes(query))
    .slice(0, 20);

  return NextResponse.json(results);
} 
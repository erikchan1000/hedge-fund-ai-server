'use client';

import { useState } from 'react';
import { AnalysisForm } from './components/AnalysisForm';
import { AnalysisRequest } from './types/analysis';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<{
    stage?: string;
    message?: string;
    progress?: number;
    current_analyst?: string;
    analyst_progress?: string;
  }>({});
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (data: AnalysisRequest) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress({});

    try {
      const response = await fetch('/api/generate_analysis', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      });

      if (!response.ok) {
        throw new Error('Failed to generate analysis');
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        // Convert the chunk to text
        const chunk = new TextDecoder().decode(value);
        
        // Split the chunk into individual JSON messages
        const messages = chunk.split('\n').filter(msg => msg.trim());
        
        for (let message of messages) {
          try {
            message = message.replace('data: ', '')
            const data = JSON.parse(message);
            
            if (data.type === 'progress') {
              setProgress({
                stage: data.stage,
                message: data.message,
                progress: data.progress,
                current_analyst: data.current_analyst,
                analyst_progress: data.analyst_progress,
              });
            } else if (data.type === 'result') {
              setResult(data.data);
            } else if (data.type === 'error') {
              setError(data.message);
            }
          } catch (e) {
            console.error('Error parsing message:', e);
            console.error('Failed message:', message);
          }
        }
      }
    } catch (error) {
      console.error('Error:', error);
      setError(error instanceof Error ? error.message : 'An unknown error occurred');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="grid grid-rows-[20px_1fr_20px] items-center justify-items-center min-h-screen p-8 pb-20 gap-16 sm:p-20 font-[family-name:var(--font-geist-sans)]">
      <main className="flex flex-col gap-[32px] row-start-2 items-center sm:items-start w-full max-w-2xl">
        <h1 className="text-3xl font-bold">AI Hedge Fund Analysis</h1>
        <p className="text-gray-600">Generate investment analysis using AI-powered insights from legendary investors.</p>
        <AnalysisForm onSubmit={handleSubmit} isLoading={isLoading} />
        
        {isLoading && (
          <div className="w-full mt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium">
                {progress.current_analyst ? `${progress.current_analyst} Analysis` : progress.stage}
              </span>
              <span className="text-sm text-gray-500">{progress.analyst_progress}</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2.5">
              <div 
                className="bg-blue-600 h-2.5 rounded-full transition-all duration-300" 
                style={{ width: `${progress.progress || 0}%` }}
              ></div>
            </div>
            <p className="text-sm text-gray-600 mt-2">{progress.message}</p>
          </div>
        )}

        {error && (
          <div className="w-full mt-4 p-4 bg-red-50 border border-red-200 rounded-md">
            <p className="text-red-600">{error}</p>
          </div>
        )}

        {result && (
          <div className="w-full mt-4">
            <h2 className="text-xl font-semibold mb-4">Analysis Results</h2>
            <pre className="bg-gray-50 p-4 rounded-md overflow-auto">
              {JSON.stringify(result, null, 2)}
            </pre>
          </div>
        )}
      </main>
    </div>
  );
}

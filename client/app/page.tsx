'use client';

import { AnalysisForm } from './components/AnalysisForm';
import { AnalysisResults } from './components/AnalysisResults';
import { AnalysisRequest, ReturnData } from './types/analysis';
import { useStreamProcessor } from './utils/useStreamProcessor';

export default function Home() {
  const { isLoading, progress, result, error, processStream } = useStreamProcessor<ReturnData>();

  const handleSubmit = async (data: AnalysisRequest) => {
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

      await processStream(response);
    } catch (error) {
      console.error('Error:', error);
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
            <AnalysisResults data={result} />
          </div>
        )}
      </main>
    </div>
  );
}

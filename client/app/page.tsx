'use client';

import { useState } from 'react';
import { AnalysisForm } from './components/AnalysisForm';
import { AnalysisRequest } from './types/analysis';

export default function Home() {
  const [isLoading, setIsLoading] = useState(false);

  const handleSubmit = async (data: AnalysisRequest) => {
    setIsLoading(true);
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

      const result = await response.json();
      // Handle the analysis result here
      console.log(result);
    } catch (error) {
      console.error('Error:', error);
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
      </main>
    </div>
  );
}

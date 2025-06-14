import { useState } from 'react';

interface StreamProgress {
  stage?: string;
  message?: string;
  progress?: number;
  current_analyst?: string;
  analyst_progress?: string;
  node?: string;
  step?: number;
}

interface IntermediateResult {
  node: string;
  stage: string;
  messages: string[];
}

interface StreamProcessorResult<T> {
  isLoading: boolean;
  progress: StreamProgress;
  result: T | null;
  error: string | null;
  intermediateResults: IntermediateResult[];
  processStream: (response: Response) => Promise<void>;
}

export function useStreamProcessor<T>(): StreamProcessorResult<T> {
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState<StreamProgress>({});
  const [result, setResult] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [intermediateResults, setIntermediateResults] = useState<IntermediateResult[]>([]);

  const processStream = async (response: Response) => {
    setIsLoading(true);
    setError(null);
    setResult(null);
    setProgress({});
    setIntermediateResults([]);

    try {
      const reader = response.body?.getReader();
      if (!reader) throw new Error('No reader available');

      console.log('Starting to read stream...');
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          console.log('Stream reading completed');
          break;
        }

        // Convert the chunk to text
        const chunk = new TextDecoder().decode(value);
        console.log('Received chunk:', chunk);
        
        // Split the chunk into individual JSON messages
        const messages = chunk.split('\n').filter(msg => msg.trim());
        console.log('Parsed messages:', messages);
        
        for (let message of messages) {
          try {
            message = message.replace('data: ', '');
            console.log('Processing message:', message);
            
            // Replace NaN with null before parsing
            const sanitizedMessage = message.replace(/: NaN/g, ': null');
            console.log('Sanitized message:', sanitizedMessage);
            
            const data = JSON.parse(sanitizedMessage);
            console.log('Parsed data:', data);
            
            if (data.type === 'progress') {
              console.log('Progress update:', {
                stage: data.stage,
                message: data.message,
                progress: data.progress,
                current_analyst: data.current_analyst,
                analyst_progress: data.analyst_progress,
                node: data.node,
                step: data.step,
              });
              setProgress({
                stage: data.stage,
                message: data.message,
                progress: data.progress,
                current_analyst: data.current_analyst,
                analyst_progress: data.analyst_progress,
                node: data.node,
                step: data.step,
              });
            } else if (data.type === 'intermediate') {
              console.log('Intermediate result:', data);
              const intermediateResult: IntermediateResult = {
                node: data.node,
                stage: data.stage,
                messages: data.messages,
              };
              setIntermediateResults(prev => [...prev, intermediateResult]);
            } else if (data.type === 'result') {
              console.log('Final result received:', data.data);
              setResult(data.data);
            } else if (data.type === 'error') {
              console.error('Error in stream:', data.message);
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

  return {
    isLoading,
    progress,
    result,
    error,
    intermediateResults,
    processStream,
  };
} 
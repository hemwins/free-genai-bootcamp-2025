
import React, { useState } from 'react';
import { cn } from '@/lib/utils';
import AnimatedContainer from './AnimatedContainer';

interface InputSectionProps {
  onSubmit: (word: string) => void;
  isLoading: boolean;
  className?: string;
}

const InputSection: React.FC<InputSectionProps> = ({ 
  onSubmit, 
  isLoading, 
  className 
}) => {
  const [inputWord, setInputWord] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (inputWord.trim()) {
      onSubmit(inputWord.trim());
    }
  };

  return (
    <AnimatedContainer 
      animation="slide-up" 
      className={cn('w-full max-w-md mx-auto', className)}
    >
      <div className="glass-panel p-6">
        <h2 className="text-xl font-display font-medium mb-4">Enter a word for inspiration</h2>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="relative">
            <input
              type="text"
              value={inputWord}
              onChange={(e) => setInputWord(e.target.value)}
              className="input-field"
              placeholder="Type a word in English or Japanese..."
              disabled={isLoading}
            />
            {inputWord && (
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                onClick={() => setInputWord('')}
                aria-label="Clear input"
              >
                <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                </svg>
              </button>
            )}
          </div>
          <button
            type="submit"
            className={cn(
              'btn-primary w-full flex items-center justify-center',
              isLoading ? 'opacity-70 cursor-not-allowed' : ''
            )}
            disabled={isLoading || !inputWord.trim()}
          >
            {isLoading ? (
              <>
                <svg className="animate-spin -ml-1 mr-2 h-4 w-4 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
                Generating...
              </>
            ) : (
              'Generate Haiku & Image'
            )}
          </button>
        </form>
      </div>
    </AnimatedContainer>
  );
};

export default InputSection;

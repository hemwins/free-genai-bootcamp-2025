
import React from 'react';
import { cn } from '@/lib/utils';
import AnimatedContainer from './AnimatedContainer';

interface HaikuDisplayProps {
  haiku: string[];
  language: 'en' | 'jp';
  className?: string;
}

const HaikuDisplay: React.FC<HaikuDisplayProps> = ({ 
  haiku, 
  language, 
  className 
}) => {
  const isJapanese = language === 'jp';
  
  return (
    <AnimatedContainer 
      animation="fade-in"
      delay={300}
      className={cn(
        'haiku-paper p-6 bg-white/80 backdrop-blur-sm border border-gray-200 rounded-xl shadow-sm flex items-center justify-center',
        className
      )}
    >
      <div className={cn(
        'haiku-text font-haiku',
        isJapanese ? 'text-2xl leading-loose' : 'text-lg leading-relaxed',
        isJapanese ? 'writing-vertical-rl' : ''
      )}>
        {haiku.map((line, index) => (
          <AnimatedContainer 
            key={index} 
            animation="slide-right" 
            delay={400 + (index * 200)}
            className="mb-3 last:mb-0"
          >
            <p className={isJapanese ? 'ml-6' : ''}>{line}</p>
          </AnimatedContainer>
        ))}
      </div>
    </AnimatedContainer>
  );
};

export default HaikuDisplay;

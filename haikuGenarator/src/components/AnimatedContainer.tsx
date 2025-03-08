
import React, { ReactNode } from 'react';
import { cn } from '@/lib/utils';

interface AnimatedContainerProps {
  children: ReactNode;
  animation?: 'fade-in' | 'slide-up' | 'slide-right' | 'scale-in' | 'none';
  className?: string;
  delay?: number;
  duration?: number;
  show?: boolean;
}

const AnimatedContainer: React.FC<AnimatedContainerProps> = ({
  children,
  animation = 'fade-in',
  className = '',
  delay = 0,
  duration = 600,
  show = true
}) => {
  const animationClass = show ? {
    'fade-in': 'animate-fade-in',
    'slide-up': 'animate-slide-up',
    'slide-right': 'animate-slide-right',
    'scale-in': 'animate-scale-in',
    'none': ''
  }[animation] : 'opacity-0';

  const style = {
    animationDelay: `${delay}ms`,
    animationDuration: `${duration}ms`
  };

  return (
    <div 
      className={cn(animationClass, className)} 
      style={show ? style : undefined}
    >
      {children}
    </div>
  );
};

export default AnimatedContainer;

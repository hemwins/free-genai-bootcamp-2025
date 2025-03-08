
import { useState, useEffect } from 'react';

interface AnimationProps {
  initialState?: boolean;
  delay?: number;
  duration?: number;
}

// Hook for controlled animations
export const useAnimatedState = ({
  initialState = false,
  delay = 0,
  duration = 600
}: AnimationProps = {}) => {
  const [isVisible, setIsVisible] = useState(initialState);
  const [isAnimating, setIsAnimating] = useState(initialState);

  useEffect(() => {
    let timer: NodeJS.Timeout;
    
    if (isVisible && !isAnimating) {
      timer = setTimeout(() => {
        setIsAnimating(true);
      }, delay);
    } else if (!isVisible && isAnimating) {
      timer = setTimeout(() => {
        setIsAnimating(false);
      }, duration);
    }
    
    return () => clearTimeout(timer);
  }, [isVisible, isAnimating, delay, duration]);

  const show = () => setIsVisible(true);
  const hide = () => setIsVisible(false);
  const toggle = () => setIsVisible(prev => !prev);

  return { isVisible, isAnimating, show, hide, toggle };
};

// Animation sequence utility
export const useSequentialAnimation = (itemCount: number, baseDelay = 100) => {
  return Array.from({ length: itemCount }).map((_, index) => ({
    className: `animate-delay-${(index + 1) * baseDelay}`,
    delay: baseDelay * index
  }));
};

// Staggered entrance animation
export const useStaggeredEntrance = (itemCount: number, initialDelay = 0, increment = 100) => {
  const [visibleItems, setVisibleItems] = useState<boolean[]>(Array(itemCount).fill(false));
  
  useEffect(() => {
    const timers: NodeJS.Timeout[] = [];
    
    for (let i = 0; i < itemCount; i++) {
      const timer = setTimeout(() => {
        setVisibleItems(prev => {
          const newState = [...prev];
          newState[i] = true;
          return newState;
        });
      }, initialDelay + (i * increment));
      
      timers.push(timer);
    }
    
    return () => timers.forEach(timer => clearTimeout(timer));
  }, [itemCount, initialDelay, increment]);
  
  return visibleItems;
};

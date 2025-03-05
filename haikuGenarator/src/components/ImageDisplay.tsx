
import React, { useState, useEffect } from 'react';
import { cn } from '@/lib/utils';
import AnimatedContainer from './AnimatedContainer';

interface ImageDisplayProps {
  imageUrl: string;
  altText: string;
  className?: string;
}

const ImageDisplay: React.FC<ImageDisplayProps> = ({ 
  imageUrl, 
  altText, 
  className 
}) => {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (imageUrl) {
      setLoading(true);
      setError(false);
      
      const img = new Image();
      img.src = imageUrl;
      
      img.onload = () => {
        setLoading(false);
      };
      
      img.onerror = () => {
        setLoading(false);
        setError(true);
      };
    }
  }, [imageUrl]);

  return (
    <AnimatedContainer 
      animation="scale-in"
      delay={600}
      className={cn(
        'relative overflow-hidden rounded-lg shadow-lg bg-haiku-light/30', 
        className
      )}
    >
      {loading ? (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="animate-pulse flex flex-col items-center">
            <div className="w-20 h-20 bg-gray-200 rounded-full mb-4"></div>
            <div className="h-4 w-32 bg-gray-200 rounded"></div>
          </div>
        </div>
      ) : error ? (
        <div className="absolute inset-0 flex items-center justify-center bg-gray-100">
          <div className="text-center text-gray-500">
            <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
            <p className="mt-2">Failed to load image</p>
          </div>
        </div>
      ) : (
        <img 
          src={imageUrl} 
          alt={altText} 
          className="w-full h-full object-cover transform transition-transform duration-700 hover:scale-105"
        />
      )}
    </AnimatedContainer>
  );
};

export default ImageDisplay;

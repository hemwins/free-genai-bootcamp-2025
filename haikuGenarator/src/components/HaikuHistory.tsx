
import React from 'react';
import { useDatabase, StoredHaiku } from '@/services/DatabaseService';
import AnimatedContainer from './AnimatedContainer';

const HaikuHistory: React.FC = () => {
  const { haikus, loading, error } = useDatabase();

  if (loading) {
    return (
      <div className="w-full flex justify-center items-center py-12">
        <div className="animate-spin h-8 w-8 border-4 border-haiku-dark border-t-transparent rounded-full"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-8 text-red-500">
        <p>{error}</p>
      </div>
    );
  }

  if (haikus.length === 0) {
    return (
      <div className="text-center py-12 glass-panel">
        <h3 className="text-xl font-display mb-4">No Haikus Yet</h3>
        <p className="text-gray-600">
          Generate your first haiku to see it here.
        </p>
      </div>
    );
  }

  return (
    <div className="w-full max-w-6xl mx-auto">
      <h2 className="text-2xl font-display mb-6 text-center">Your Haiku Collection</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {haikus.map((haiku) => (
          <AnimatedContainer key={haiku.id} animation="fade-in" className="h-full">
            <div className="glass-panel p-4 h-full flex flex-col">
              <div className="mb-3">
                <span className="text-xs text-gray-500">
                  {new Date(haiku.created_at).toLocaleString()}
                </span>
                <p className="text-sm font-medium mb-1">
                  Inspired by: <span className="italic">{haiku.input_word}</span>
                </p>
              </div>
              
              <div className="flex-grow">
                <div 
                  className={`mb-4 ${haiku.language === 'jp' ? 'font-jp writing-vertical h-40' : ''}`}
                >
                  {haiku.haiku_text.split("\n").map((line, index) => (
                    <p key={index} className="mb-1">{line}</p>
                  ))}
                </div>
                
                <div className="aspect-square overflow-hidden rounded-md">
                  <img 
                    src={haiku.image_data} 
                    alt={`Haiku illustration for ${haiku.input_word}`}
                    className="w-full h-full object-cover"
                  />
                </div>
              </div>
            </div>
          </AnimatedContainer>
        ))}
      </div>
    </div>
  );
};

export default HaikuHistory;

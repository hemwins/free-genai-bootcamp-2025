
import React, { useState } from 'react';
import HaikuGenerator from '@/components/HaikuGenerator';
import HaikuHistory from '@/components/HaikuHistory';
import AnimatedContainer from '@/components/AnimatedContainer';
import { useDatabase } from '@/services/DatabaseService';

const Index: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'create' | 'history'>('create');
  const { haikus, loading } = useDatabase();
  return (
    <div className="min-h-screen bg-gradient-to-b from-haiku-light to-white">
      {/* Background subtle pattern overlay */}
      <div className="absolute inset-0 bg-noise opacity-5 mix-blend-soft-light pointer-events-none"></div>
      
      {/* Main content */}
      <div className="container mx-auto px-4 py-16 relative z-10">
        {/* Header */}
        <AnimatedContainer animation="slide-up" className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl lg:text-6xl font-display font-medium mb-4">
            Haiku Image Muse
          </h1>
          <AnimatedContainer animation="fade-in" delay={300} className="max-w-2xl mx-auto">
            <p className="text-lg text-gray-700 mb-2">
              A haiku with an image that captures its essence.
            </p>
          </AnimatedContainer>
        </AnimatedContainer>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="inline-flex rounded-md shadow-sm bg-white p-1">
            { <button
              onClick={() => setActiveTab('create')}
              className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                activeTab === 'create'
                  ? 'bg-haiku-dark text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              }`}
            >
              Add New 
            </button> }
            {!loading && haikus.length > 0 && (
              <button
                onClick={() => setActiveTab('history')}
                className={`px-4 py-2 text-sm font-medium rounded-md transition-all ${
                  activeTab === 'history'
                    ? 'bg-haiku-dark text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                Your Collection
              </button>
            )}
          </div>
        </div>
        
        {/* Content based on active tab */}
        <AnimatedContainer animation="fade-in" className="mb-8">
          {activeTab === 'create' ? (
            <HaikuGenerator onSave={() => setActiveTab('history')} />
          ) : (
            <HaikuHistory />
          )}
        </AnimatedContainer>
        
        {/* Footer */}
        <AnimatedContainer animation="fade-in" delay={600} className="mt-16 text-center text-sm text-gray-500">
          <p>
            Inspired by traditional Japanese poetry
          </p>
        </AnimatedContainer>
      </div>
    </div>
  );
};

export default Index;

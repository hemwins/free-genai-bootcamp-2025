
import React from 'react';
import { cn } from '@/lib/utils';
import { useToast } from '@/components/ui/use-toast';

interface SaveButtonProps {
  onSave: () => Promise<void>;
  isSaving: boolean;
  disabled?: boolean;
  className?: string;
}

const SaveButton: React.FC<SaveButtonProps> = ({ 
  onSave, 
  isSaving, 
  disabled = false,
  className 
}) => {
  const { toast } = useToast();

  const handleSave = async () => {
    try {
      await onSave();
      toast({
        title: "Saved successfully",
        description: "Your haiku and image have been saved",
        variant: "default",
      });
    } catch (error) {
      console.error('Save error:', error);
      toast({
        title: "Save failed",
        description: "There was a problem saving your creation",
        variant: "destructive",
      });
    }
  };

  return (
    <button
      onClick={handleSave}
      disabled={disabled || isSaving}
      className={cn(
        'btn-secondary group flex items-center justify-center',
        (disabled || isSaving) ? 'opacity-50 cursor-not-allowed' : '',
        className
      )}
    >
      {isSaving ? (
        <>
          <svg className="animate-spin -ml-1 mr-2 h-4 w-4" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          Saving...
        </>
      ) : (
        <>
          <svg 
            xmlns="http://www.w3.org/2000/svg" 
            className="h-5 w-5 mr-2 transform transition-transform group-hover:-translate-y-1" 
            fill="none" 
            viewBox="0 0 24 24" 
            stroke="currentColor"
          >
            <path 
              strokeLinecap="round" 
              strokeLinejoin="round" 
              strokeWidth={2} 
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12" 
            />
          </svg>
          Save Creation
        </>
      )}
    </button>
  );
};

export default SaveButton;

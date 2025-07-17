"use client";

import { Zap, Loader2, Smartphone } from 'lucide-react';

interface TriggerButtonProps {
  onClick: () => void;
  isLoading: boolean;
  variant?: 'primary' | 'secondary';
}

export default function TriggerButton({ onClick, isLoading, variant = 'primary' }: TriggerButtonProps) {
  if (variant === 'secondary') {
    return (
      <button
        onClick={onClick}
        disabled={isLoading}
        className="w-full bg-white border border-gray-200 hover:border-gray-300 text-gray-700 hover:text-gray-900 px-4 py-3 rounded-[12px] font-medium text-sm transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
      >
        {isLoading ? (
          <>
            <Loader2 className="w-4 h-4 animate-spin" />
            Triggering...
          </>
        ) : (
          <>
            <Smartphone className="w-4 h-4" />
            Simulate NFC
          </>
        )}
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      disabled={isLoading}
      className={`
        inline-flex items-center gap-2 px-6 py-3 rounded-[16px] font-semibold text-sm
        transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed
        ${isLoading 
          ? 'bg-gradient-to-r from-purple-500 to-blue-600 text-white' 
          : 'bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white shadow-[0_4px_12px_rgba(59,130,246,0.3)] hover:shadow-[0_6px_16px_rgba(59,130,246,0.4)]'
        }
      `}
    >
      {isLoading ? (
        <>
          <Loader2 className="w-4 h-4 animate-spin" />
          Processing...
        </>
      ) : (
        <>
          <Zap className="w-4 h-4" />
          Simulate Meeting
        </>
      )}
    </button>
  );
}
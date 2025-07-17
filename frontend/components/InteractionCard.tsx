"use client";

import { Phone, Mail, Linkedin, Mic, Camera, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface InteractionCardProps {
  interaction: {
    id: string;
    type: 'whatsapp' | 'email' | 'linkedin' | 'audio' | 'selfie';
    contactName: string;
    contactEmail?: string;
    contactCompany?: string;
    timestamp: Date;
    status: 'pending' | 'success' | 'failed';
    details: {
      message?: string;
      audioTranscript?: string;
      selfieUrl?: string;
      platform?: string;
    };
  };
}

const typeConfig = {
  whatsapp: {
    icon: Phone,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200',
    label: 'WhatsApp'
  },
  email: {
    icon: Mail,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    label: 'Email'
  },
  linkedin: {
    icon: Linkedin,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200',
    label: 'LinkedIn'
  },
  audio: {
    icon: Mic,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200',
    label: 'Audio'
  },
  selfie: {
    icon: Camera,
    color: 'text-pink-600',
    bgColor: 'bg-pink-50',
    borderColor: 'border-pink-200',
    label: 'Selfie'
  }
};

const statusConfig = {
  pending: {
    icon: Loader2,
    color: 'text-orange-600',
    className: 'animate-spin'
  },
  success: {
    icon: CheckCircle,
    color: 'text-green-600',
    className: ''
  },
  failed: {
    icon: AlertCircle,
    color: 'text-red-600',
    className: ''
  }
};

export default function InteractionCard({ interaction }: InteractionCardProps) {
  const config = typeConfig[interaction.type];
  const statusConf = statusConfig[interaction.status];
  const Icon = config.icon;
  const StatusIcon = statusConf.icon;

  const formatTime = (date: Date) => {
    const now = new Date();
    const diff = now.getTime() - date.getTime();
    const minutes = Math.floor(diff / (1000 * 60));
    
    if (minutes < 1) return 'Just now';
    if (minutes < 60) return `${minutes}m ago`;
    const hours = Math.floor(minutes / 60);
    if (hours < 24) return `${hours}h ago`;
    return date.toLocaleDateString();
  };

  const getContent = () => {
    switch (interaction.type) {
      case 'audio':
        return interaction.details.audioTranscript?.substring(0, 60) + '...' || 'Audio recording captured';
      case 'selfie':
        return 'Meeting selfie captured';
      case 'email':
      case 'whatsapp':
      case 'linkedin':
        return interaction.details.message?.substring(0, 60) + '...' || `${config.label} message sent`;
      default:
        return 'Interaction completed';
    }
  };

  return (
    <div className={`bg-white rounded-[12px] border ${config.borderColor} shadow-[0_1px_4px_rgba(0,0,0,0.02)] p-4 hover:shadow-[0_2px_8px_rgba(0,0,0,0.08)] transition-all duration-200`}>
      <div className="flex items-start justify-between mb-3">
        <div className={`w-8 h-8 rounded-full ${config.bgColor} flex items-center justify-center`}>
          <Icon className={`w-4 h-4 ${config.color}`} />
        </div>
        <div className="flex items-center gap-1">
          <StatusIcon className={`w-3 h-3 ${statusConf.color} ${statusConf.className}`} />
        </div>
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center gap-2">
          <h4 className="font-medium text-gray-900 text-sm">{config.label}</h4>
        </div>
        
        <p className="text-xs text-gray-600 leading-relaxed">
          {getContent()}
        </p>
        
        <div className="flex items-center gap-1 text-xs text-gray-500">
          <Clock className="w-3 h-3" />
          <span>{formatTime(interaction.timestamp)}</span>
        </div>
      </div>
    </div>
  );
}
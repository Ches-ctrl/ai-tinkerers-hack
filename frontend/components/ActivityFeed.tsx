"use client";

import { Phone, Mail, Linkedin, Mic, Camera, Clock, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';

interface MeetingInteraction {
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
}

interface ActivityFeedProps {
  interactions: MeetingInteraction[];
}

const typeConfig = {
  whatsapp: {
    icon: Phone,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    label: 'WhatsApp'
  },
  email: {
    icon: Mail,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    label: 'Email'
  },
  linkedin: {
    icon: Linkedin,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    label: 'LinkedIn'
  },
  audio: {
    icon: Mic,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    label: 'Audio'
  },
  selfie: {
    icon: Camera,
    color: 'text-pink-600',
    bgColor: 'bg-pink-50',
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

export default function ActivityFeed({ interactions }: ActivityFeedProps) {
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

  const getActivityText = (interaction: MeetingInteraction) => {
    const config = typeConfig[interaction.type];
    
    switch (interaction.type) {
      case 'audio':
        return `Captured audio recording with ${interaction.contactName}`;
      case 'selfie':
        return `Took meeting selfie with ${interaction.contactName}`;
      case 'email':
        return `Sent follow-up email to ${interaction.contactName}`;
      case 'whatsapp':
        return `Sent WhatsApp message to ${interaction.contactName}`;
      case 'linkedin':
        return `Sent LinkedIn connection request to ${interaction.contactName}`;
      default:
        return `${config.label} interaction with ${interaction.contactName}`;
    }
  };

  const getActivityDetails = (interaction: MeetingInteraction) => {
    switch (interaction.type) {
      case 'audio':
        return interaction.details.audioTranscript;
      case 'email':
      case 'whatsapp':
      case 'linkedin':
        return interaction.details.message;
      case 'selfie':
        return 'Meeting photo captured';
      default:
        return null;
    }
  };

  if (interactions.length === 0) {
    return (
      <div className="bg-white rounded-[20px] border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-8 text-center">
        <div className="w-16 h-16 bg-gray-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Clock className="w-8 h-8 text-gray-400" />
        </div>
        <h3 className="font-medium text-gray-900 mb-2">No activity yet</h3>
        <p className="text-gray-600 text-sm">
          Trigger your first meeting automation to see activity here.
        </p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-[20px] border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] overflow-hidden">
      <div className="divide-y divide-gray-50">
        {interactions.map((interaction) => {
          const config = typeConfig[interaction.type];
          const statusConf = statusConfig[interaction.status];
          const Icon = config.icon;
          const StatusIcon = statusConf.icon;
          const details = getActivityDetails(interaction);

          return (
            <div key={interaction.id} className="p-6 hover:bg-gray-50/50 transition-colors duration-200">
              <div className="flex items-start gap-4">
                <div className={`w-10 h-10 rounded-full ${config.bgColor} flex items-center justify-center flex-shrink-0`}>
                  <Icon className={`w-5 h-5 ${config.color}`} />
                </div>
                
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <p className="font-medium text-gray-900">
                          {getActivityText(interaction)}
                        </p>
                        <StatusIcon className={`w-4 h-4 ${statusConf.color} ${statusConf.className} flex-shrink-0`} />
                      </div>
                      
                      {interaction.contactCompany && (
                        <p className="text-sm text-gray-600 mb-2">
                          {interaction.contactCompany}
                        </p>
                      )}
                      
                      {details && (
                        <p className="text-sm text-gray-700 leading-relaxed mb-3 bg-gray-50 rounded-lg p-3">
                          {details.length > 150 ? details.substring(0, 150) + '...' : details}
                        </p>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-2 text-xs text-gray-500">
                    <Clock className="w-3 h-3" />
                    <span>{formatTime(interaction.timestamp)}</span>
                    {interaction.contactEmail && (
                      <>
                        <span className="text-gray-300">•</span>
                        <span>{interaction.contactEmail}</span>
                      </>
                    )}
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
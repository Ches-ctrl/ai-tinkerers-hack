"use client";

import { Users, Mail, Linkedin, Mic, TrendingUp } from 'lucide-react';

interface StatsOverviewProps {
  stats: {
    totalMeetings: number;
    emailsSent: number;
    connectionsAdded: number;
    audiosCaptured: number;
  };
}

const statItems = [
  {
    key: 'totalMeetings' as const,
    label: 'Total Meetings',
    icon: Users,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200'
  },
  {
    key: 'emailsSent' as const,
    label: 'Emails Sent',
    icon: Mail,
    color: 'text-green-600',
    bgColor: 'bg-green-50',
    borderColor: 'border-green-200'
  },
  {
    key: 'connectionsAdded' as const,
    label: 'LinkedIn Connections',
    icon: Linkedin,
    color: 'text-indigo-600',
    bgColor: 'bg-indigo-50',
    borderColor: 'border-indigo-200'
  },
  {
    key: 'audiosCaptured' as const,
    label: 'Audio Recordings',
    icon: Mic,
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    borderColor: 'border-purple-200'
  }
];

export default function StatsOverview({ stats }: StatsOverviewProps) {
  return (
    <div className="mb-8">
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-xl font-semibold text-gray-900">Overview</h2>
        <div className="flex items-center gap-1 text-green-600">
          <TrendingUp className="w-4 h-4" />
          <span className="text-sm font-medium">All systems active</span>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statItems.map((item) => {
          const Icon = item.icon;
          const value = stats[item.key];
          
          return (
            <div
              key={item.key}
              className={`bg-white rounded-[16px] border ${item.borderColor} shadow-[0_2px_8px_rgba(0,0,0,0.04)] p-6 hover:shadow-[0_4px_12px_rgba(0,0,0,0.08)] transition-all duration-200`}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`w-12 h-12 rounded-full ${item.bgColor} flex items-center justify-center`}>
                  <Icon className={`w-6 h-6 ${item.color}`} />
                </div>
                <div className="text-right">
                  <div className="text-2xl font-bold text-gray-900">
                    {value.toLocaleString()}
                  </div>
                </div>
              </div>
              
              <div>
                <h3 className="font-medium text-gray-900 mb-1">{item.label}</h3>
                <div className="flex items-center gap-2">
                  <div className="flex items-center gap-1 text-xs text-green-600">
                    <div className="w-1.5 h-1.5 bg-green-500 rounded-full"></div>
                    <span>Active</span>
                  </div>
                  <span className="text-xs text-gray-400">•</span>
                  <span className="text-xs text-gray-500">Last 30 days</span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
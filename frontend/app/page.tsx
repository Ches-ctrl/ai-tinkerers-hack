"use client";

import { useState, useEffect } from 'react';
import { Phone, Mail, Linkedin, Clock, CheckCircle } from 'lucide-react';
import InteractionCard from '@/components/InteractionCard';
import TriggerButton from '@/components/TriggerButton';
import ActivityFeed from '@/components/ActivityFeed';
import StatsOverview from '@/components/StatsOverview';
import MemoriesGallery from '@/components/MemoriesGallery';

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

export default function Home() {
  const [interactions, setInteractions] = useState<MeetingInteraction[]>([]);
  const [isTriggering, setIsTriggering] = useState(false);
  const [stats, setStats] = useState({
    totalMeetings: 0,
    emailsSent: 0,
    connectionsAdded: 0,
    audiosCaptured: 0
  });
  const [realTimeStats, setRealTimeStats] = useState({
    totalContacts: 0,
    contactsWithPhotos: 0,
    contactsWithEmails: 0,
    contactsWithPhones: 0
  });

  // Fetch real-time statistics
  const fetchRealTimeStats = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/contacts');
      if (response.ok) {
        const contacts = await response.json();
        setRealTimeStats({
          totalContacts: contacts.length,
          contactsWithPhotos: contacts.filter((c: any) => c.photo_file).length,
          contactsWithEmails: contacts.filter((c: any) => c.emails && c.emails.length > 0).length,
          contactsWithPhones: contacts.filter((c: any) => c.phone_numbers && c.phone_numbers.length > 0).length
        });
      }
    } catch (error) {
      console.error('Error fetching real-time stats:', error);
    }
  };

  // Mock data for demonstration
  useEffect(() => {
    fetchRealTimeStats();
    
    // Update stats every 5 seconds
    const interval = setInterval(() => {
      fetchRealTimeStats();
    }, 5000);
    
    const mockInteractions: MeetingInteraction[] = [
      {
        id: '1',
        type: 'selfie',
        contactName: 'Sarah Chen',
        contactEmail: 'sarah@techcorp.com',
        contactCompany: 'TechCorp',
        timestamp: new Date(Date.now() - 2 * 60 * 1000), // 2 minutes ago
        status: 'success',
        details: {
          selfieUrl: '/api/placeholder/300/400'
        }
      },
      {
        id: '2',
        type: 'audio',
        contactName: 'Sarah Chen',
        contactEmail: 'sarah@techcorp.com',
        contactCompany: 'TechCorp',
        timestamp: new Date(Date.now() - 3 * 60 * 1000), // 3 minutes ago
        status: 'success',
        details: {
          audioTranscript: 'We discussed the AI automation project and potential partnership opportunities. Sarah mentioned they\'re looking for innovative solutions.'
        }
      },
      {
        id: '3',
        type: 'email',
        contactName: 'Sarah Chen',
        contactEmail: 'sarah@techcorp.com',
        contactCompany: 'TechCorp',
        timestamp: new Date(Date.now() - 1 * 60 * 1000), // 1 minute ago
        status: 'success',
        details: {
          message: 'Great meeting you at TechCorp! Follow-up email sent with meeting notes and selfie.'
        }
      },
      {
        id: '4',
        type: 'linkedin',
        contactName: 'Sarah Chen',
        contactEmail: 'sarah@techcorp.com',
        contactCompany: 'TechCorp',
        timestamp: new Date(Date.now() - 1 * 60 * 1000), // 1 minute ago
        status: 'success',
        details: {
          message: 'Connection request sent with personalized note about our meeting.'
        }
      },
      {
        id: '5',
        type: 'whatsapp',
        contactName: 'Sarah Chen',
        contactEmail: 'sarah@techcorp.com',
        contactCompany: 'TechCorp',
        timestamp: new Date(Date.now() - 30 * 1000), // 30 seconds ago
        status: 'success',
        details: {
          message: 'WhatsApp message sent with meeting selfie and quick follow-up.'
        }
      }
    ];

    setInteractions(mockInteractions);
    setStats({
      totalMeetings: 12,
      emailsSent: 45,
      connectionsAdded: 38,
      audiosCaptured: 50
    });
    
    return () => clearInterval(interval);
  }, []);

  const handleTrigger = async () => {
    setIsTriggering(true);
    
    // Simulate NFC trigger process
    setTimeout(() => {
      const newInteraction: MeetingInteraction = {
        id: Date.now().toString(),
        type: 'audio',
        contactName: 'New Contact',
        contactEmail: 'contact@example.com',
        contactCompany: 'Example Corp',
        timestamp: new Date(),
        status: 'pending',
        details: {
          audioTranscript: 'Recording meeting context...'
        }
      };
      
      setInteractions(prev => [newInteraction, ...prev]);
      setIsTriggering(false);
    }, 2000);
  };

  const getLatestMeeting = () => {
    const meetingGroups = interactions.reduce((groups, interaction) => {
      const key = `${interaction.contactName}-${interaction.contactEmail}`;
      if (!groups[key]) {
        groups[key] = {
          contact: {
            name: interaction.contactName,
            email: interaction.contactEmail,
            company: interaction.contactCompany
          },
          interactions: [],
          timestamp: interaction.timestamp
        };
      }
      groups[key].interactions.push(interaction);
      return groups;
    }, {} as Record<string, {
      contact: {
        name: string;
        email?: string;
        company?: string;
      };
      interactions: MeetingInteraction[];
      timestamp: Date;
    }>);

    return Object.values(meetingGroups)[0] || null;
  };

  const latestMeeting = getLatestMeeting();

  return (
    <div className="min-h-screen bg-white flex flex-col">
      {/* Header */}
      <header className="border-b border-gray-100 bg-white/80 backdrop-blur-sm sticky top-0 z-50">
        <div className="container mx-auto px-6 py-6">
          <div className="flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3">
                <img src="/bumplogo.svg" alt="BUMP" className="h-8" />
                <h1 className="text-2xl font-semibold text-gray-900">AI Tinkerers Hack</h1>
              </div>
              <p className="text-gray-600 mt-1">Post-Meeting Automation Dashboard</p>
            </div>
            <div className="flex items-center gap-4">
              <div className="flex items-center gap-2 px-3 py-1 bg-green-50 rounded-full">
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span className="text-sm text-green-700 font-medium">All Systems Active</span>
              </div>
              <TriggerButton onClick={handleTrigger} isLoading={isTriggering} />
            </div>
          </div>
        </div>
      </header>

      <div className="container mx-auto px-6 py-8 max-w-7xl flex-1">
        {/* Stats Overview */}
        <StatsOverview stats={stats} realTimeStats={realTimeStats} />

        {/* Latest Meeting Section */}
        {latestMeeting && (
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-xl font-semibold text-gray-900">Latest Meeting</h2>
              <div className="flex items-center gap-2 px-2 py-1 bg-blue-50 rounded-full">
                <Clock className="w-3 h-3 text-blue-600" />
                <span className="text-xs text-blue-700 font-medium">
                  {new Date(latestMeeting.timestamp).toLocaleTimeString()}
                </span>
              </div>
            </div>
            
            <div className="bg-white rounded-[20px] border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
              <div className="flex items-start gap-4 mb-6">
                <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
                  {latestMeeting.contact.name.charAt(0)}
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 text-lg">{latestMeeting.contact.name}</h3>
                  <p className="text-gray-600">{latestMeeting.contact.email}</p>
                  {latestMeeting.contact.company && (
                    <p className="text-sm text-gray-500">{latestMeeting.contact.company}</p>
                  )}
                </div>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
                {latestMeeting.interactions.map((interaction: MeetingInteraction) => (
                  <InteractionCard key={interaction.id} interaction={interaction} />
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Meeting Memories Gallery */}
        <div className="mb-8">
          <MemoriesGallery />
        </div>

        {/* Activity Feed */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Recent Activity</h2>
            <ActivityFeed interactions={interactions} />
          </div>
          
          <div>
            <h2 className="text-xl font-semibold text-gray-900 mb-4">Quick Actions</h2>
            <div className="space-y-4">
              <div className="bg-white rounded-[16px] border border-gray-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)] p-4">
                <h3 className="font-medium text-gray-900 mb-3">Manual Meeting Simulation</h3>
                <p className="text-sm text-gray-600 mb-4">
                  Simulate the NFC trigger process for testing. In production, users tap their iPhone to an NFC tag to start automation.
                </p>
                <TriggerButton onClick={handleTrigger} isLoading={isTriggering} variant="secondary" />
              </div>
              
              <div className="bg-white rounded-[16px] border border-gray-100 shadow-[0_2px_8px_rgba(0,0,0,0.04)] p-4">
                <h3 className="font-medium text-gray-900 mb-3">System Status</h3>
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">Email Worker</span>
                    <div className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-xs text-green-600">Active</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">LinkedIn Worker</span>
                    <div className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-xs text-green-600">Active</span>
                    </div>
                  </div>
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-gray-600">WhatsApp Bridge</span>
                    <div className="flex items-center gap-1">
                      <CheckCircle className="w-4 h-4 text-green-500" />
                      <span className="text-xs text-green-600">Active</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t border-gray-100 bg-gray-50/50">
        <div className="container mx-auto px-6 py-8">
          <div className="flex items-center justify-center">
            <div className="flex items-center gap-6">
              <div className="flex items-center gap-2">
                <Mail className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-600">SendGrid</span>
              </div>
              <div className="text-gray-300">|</div>
              <div className="flex items-center gap-2">
                <Linkedin className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-600">LinkedIn API</span>
              </div>
              <div className="text-gray-300">|</div>
              <div className="flex items-center gap-2">
                <Phone className="w-5 h-5 text-gray-400" />
                <span className="text-sm text-gray-600">WhatsApp</span>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
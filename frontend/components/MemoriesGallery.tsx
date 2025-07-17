"use client";

import { useState, useEffect } from 'react';
import { Camera, Calendar, User, MapPin, Clock } from 'lucide-react';

interface ContactData {
  id: string;
  first_name: string;
  last_name: string;
  phone_numbers: string[];
  emails: string[];
  urls: string[];
  timestamp: string;
  audio_file: string | null;
  photo_file: string | null;
}

interface MemoryItem {
  id: string;
  contactName: string;
  photoUrl: string;
  timestamp: Date;
  contactInfo: {
    email?: string;
    phone?: string;
  };
}

export default function MemoriesGallery() {
  const [memories, setMemories] = useState<MemoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedMemory, setSelectedMemory] = useState<MemoryItem | null>(null);
  const [lastUpdateTime, setLastUpdateTime] = useState<Date>(new Date());

  useEffect(() => {
    fetchMemories();
    
    // Set up automatic refresh every 5 seconds
    const interval = setInterval(() => {
      fetchMemories();
    }, 5000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchMemories = async () => {
    try {
      // Don't show loading spinner on automatic refreshes
      const isInitialLoad = memories.length === 0;
      if (isInitialLoad) {
        setLoading(true);
      }
      
      // Fetch contact data from orchestrator
      const response = await fetch('http://localhost:8000/api/contacts');
      
      if (!response.ok) {
        throw new Error('Failed to fetch contacts');
      }
      
      const data = await response.json();
      const contacts: ContactData[] = Array.isArray(data) ? data : data.contacts || [];
      
      console.log('Fetched contacts:', contacts.length);
      console.log('Contacts with photos:', contacts.filter(contact => contact.photo_file).length);
      
      // Filter contacts that have photos and convert to memory items
      const memoryItems: MemoryItem[] = contacts
        .filter(contact => contact.photo_file)
        .map(contact => ({
          id: contact.id,
          contactName: `${contact.first_name} ${contact.last_name}`.trim(),
          photoUrl: `http://localhost:8000/api/media/${contact.photo_file.replace('data/media/', '')}`,
          timestamp: new Date(contact.timestamp),
          contactInfo: {
            email: contact.emails[0] || undefined,
            phone: contact.phone_numbers[0] || undefined
          }
        }))
        .sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
      
      // Check if we have new memories
      const hasNewMemories = memoryItems.length > memories.length;
      
      setMemories(memoryItems);
      setLastUpdateTime(new Date());
      
      // Show a subtle notification if new memories were added
      if (hasNewMemories && !isInitialLoad) {
        console.log('New memories added!');
      }
    } catch (error) {
      console.error('Error fetching memories:', error);
      // Don't clear existing memories on error, just log it
      if (memories.length === 0) {
        setMemories([]);
      }
    } finally {
      if (memories.length === 0) {
        setLoading(false);
      }
    }
  };

  const formatDate = (date: Date) => {
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      year: 'numeric'
    });
  };

  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <div className="bg-white rounded-[20px] border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
        <div className="flex items-center gap-3 mb-6">
          <Camera className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Meeting Memories</h2>
        </div>
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {[...Array(8)].map((_, i) => (
            <div key={i} className="aspect-square bg-gray-100 rounded-xl animate-pulse" />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-[20px] border border-gray-100 shadow-[0_2px_12px_rgba(0,0,0,0.04)] p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <Camera className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Meeting Memories</h2>
          <div className="px-3 py-1 bg-blue-50 rounded-full">
            <span className="text-sm font-medium text-blue-700">{memories.length}</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-500">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>Auto-updating every 5s</span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <div className="text-xs text-gray-500">
            Last update: {formatTime(lastUpdateTime)}
          </div>
          <button
            onClick={fetchMemories}
            className="px-3 py-1 bg-blue-100 hover:bg-blue-200 text-blue-700 rounded-lg text-sm font-medium transition-colors"
          >
            Refresh Now
          </button>
        </div>
      </div>

      {memories.length === 0 ? (
        <div className="text-center py-12">
          <Camera className="w-16 h-16 text-gray-300 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No memories yet</h3>
          <p className="text-gray-500">Meeting selfies will appear here after you connect with contacts.</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {memories.map((memory, index) => (
            <div
              key={memory.id}
              className="group relative aspect-square bg-gray-100 rounded-xl overflow-hidden cursor-pointer hover:shadow-lg transition-all duration-200 animate-fade-in"
              style={{
                animationDelay: `${index * 50}ms`
              }}
              onClick={() => setSelectedMemory(memory)}
            >
              <img
                src={memory.photoUrl}
                alt={`Meeting with ${memory.contactName}`}
                className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-200"
                onError={(e) => {
                  const target = e.target as HTMLImageElement;
                  target.src = '/api/placeholder/300/300';
                }}
              />
              
              {/* Overlay */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-200" />
              
              {/* Info overlay */}
              <div className="absolute bottom-0 left-0 right-0 p-3 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                <div className="flex items-center gap-2 mb-1">
                  <User className="w-4 h-4" />
                  <span className="text-sm font-medium truncate">{memory.contactName}</span>
                </div>
                <div className="flex items-center gap-2">
                  <Calendar className="w-3 h-3" />
                  <span className="text-xs">{formatDate(memory.timestamp)}</span>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Modal for selected memory */}
      {selectedMemory && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-hidden">
            <div className="p-6">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-semibold text-lg">
                    {selectedMemory.contactName.charAt(0)}
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{selectedMemory.contactName}</h3>
                    <div className="flex items-center gap-2 text-sm text-gray-500">
                      <Clock className="w-4 h-4" />
                      <span>{formatDate(selectedMemory.timestamp)} at {formatTime(selectedMemory.timestamp)}</span>
                    </div>
                  </div>
                </div>
                <button
                  onClick={() => setSelectedMemory(null)}
                  className="text-gray-400 hover:text-gray-600 p-2"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
              
              <div className="mb-4">
                <img
                  src={selectedMemory.photoUrl}
                  alt={`Meeting with ${selectedMemory.contactName}`}
                  className="w-full h-64 object-cover rounded-xl"
                  onError={(e) => {
                    const target = e.target as HTMLImageElement;
                    target.src = '/api/placeholder/600/400';
                  }}
                />
              </div>
              
              <div className="space-y-3">
                {selectedMemory.contactInfo.email && (
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 4.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Email</p>
                      <p className="text-sm text-gray-600">{selectedMemory.contactInfo.email}</p>
                    </div>
                  </div>
                )}
                
                {selectedMemory.contactInfo.phone && (
                  <div className="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
                    <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
                      <svg className="w-4 h-4 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 5a2 2 0 012-2h3.28a1 1 0 01.948.684l1.498 4.493a1 1 0 01-.502 1.21l-2.257 1.13a11.042 11.042 0 005.516 5.516l1.13-2.257a1 1 0 011.21-.502l4.493 1.498a1 1 0 01.684.949V19a2 2 0 01-2 2h-1C9.716 21 3 14.284 3 6V5z" />
                      </svg>
                    </div>
                    <div>
                      <p className="text-sm font-medium text-gray-900">Phone</p>
                      <p className="text-sm text-gray-600">{selectedMemory.contactInfo.phone}</p>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
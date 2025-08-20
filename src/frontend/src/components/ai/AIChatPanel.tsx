import { Fragment, useState, useRef, useEffect } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { XMarkIcon, PaperAirplaneIcon, ArrowPathIcon, LightBulbIcon } from '@heroicons/react/24/outline';
import { toast } from 'sonner';
import ReactMarkdown from 'react-markdown';
import api, { ClickHistory, DeviceStats, CountryStats } from '@/lib/api';

type Message = {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
};

type AIChatPanelProps = {
  isOpen: boolean;
  onClose: () => void;
};

export default function AIChatPanel({ isOpen, onClose }: AIChatPanelProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<{
    traffic: ClickHistory[];
    devices: DeviceStats[];
    countries: CountryStats[];
  } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const handleDiscoveryRequest = async (currentMessages: Message[]) => {
    try {
      const response = await api.askDiscovery(30);
      const { opportunities, alerts, projections } = response;
      
      let content = '## 🔍 SmartLinks Discovery Analysis\n\n';
      
      // Add opportunities
      if (opportunities && opportunities.length > 0) {
        content += '### 🚀 Opportunities\n';
        opportunities.forEach((opp: any) => {
          content += `- **${opp.segment}**: ${opp.reason}\n`;
        });
        content += '\n';
      }
      
      // Add alerts
      if (alerts && alerts.length > 0) {
        content += '### ⚠️ Alerts\n';
        alerts.forEach((alert: any) => {
          content += `- **${alert.issue}**: ${alert.details}\n`;
        });
        content += '\n';
      }
      
      // Add projections
      if (projections) {
        content += '### 📊 Projections (Next 7 Days)\n';
        content += `- **Expected Clicks**: ${projections.clicks_next_7_days?.toLocaleString() || 'N/A'}\n`;
        content += `- **Expected Revenue**: $${projections.expected_revenue?.toFixed(2) || '0.00'}\n`;
      }
      
      const assistantMessage: Message = {
        id: (Date.now() + 1).toString(),
        role: 'assistant',
        content: content,
        timestamp: new Date(),
      };
      
      setMessages([...currentMessages, assistantMessage]);
    } catch (error) {
      console.error('Error running discovery:', error);
      throw new Error('Failed to run discovery analysis');
    }
  };

  // Fetch analytics data when the panel opens
  useEffect(() => {
    if (isOpen && !analyticsData) {
      const fetchAnalyticsData = async () => {
        try {
          const [traffic, devices, countries] = await Promise.all([
            api.getClickHistory(30),
            api.getDeviceStats(),
            api.getCountryStats(),
          ]);
          setAnalyticsData({
            traffic,
            devices,
            countries,
          });
        } catch (error) {
          console.error('Error fetching analytics data:', error);
          // Continue without analytics data if there's an error
        }
      };
      fetchAnalyticsData();
    }
  }, [isOpen, analyticsData]);

  // Add initial system message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: '1',
          role: 'assistant',
          content: 'Hello! I\'m your SmartLinks Admin Assistant. How can I help you today?\n\nYou can ask me about:\n- Current system status and metrics\n- Recent click activities\n- How to perform actions like seeding the database\n- Explanation of different metrics and what they mean\n- Best practices for optimizing performance',
          timestamp: new Date(),
        },
      ]);
    }
  }, [isOpen, messages.length]);

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const handleSendMessage = async () => {
      if (!input.trim() || isLoading) return;

      const userMessage: Message = {
        id: Date.now().toString(),
        role: 'user',
        content: input,
        timestamp: new Date(),
      };

      const updatedMessages = [...messages, userMessage];
      setMessages(updatedMessages);
      setInput('');
      setIsLoading(true);

      try {
        // Check if user is asking for a discovery analysis
        if (input.toLowerCase().includes('analyse') || input.toLowerCase().includes('discovery')) {
          await handleDiscoveryRequest(updatedMessages);
          return;
        }

        // Use the DG AI for all other queries
        const response = await api.askDG(input);

        const assistantMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: response.answer || 'I apologize, but I encountered an issue processing your request.',
          timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
      } catch (error) {
        console.error('Error getting AI response:', error);
        toast.error('Failed to get response from AI assistant');
        
        const errorMessage: Message = {
          id: (Date.now() + 1).toString(),
          role: 'assistant',
          content: 'Sorry, I encountered an error while processing your request. Please try again later.',
          timestamp: new Date(),
        };
        
        setMessages(prev => [...prev, errorMessage]);
      } finally {
        setIsLoading(false);
      }
    };

    handleSendMessage();
  };

  const handleQuickAction = async (action: string, message: string) => {
    if (action === 'discovery') {
      setInput('Analyze traffic and find opportunities');
      // Trigger form submission after a small delay to allow input to update
      setTimeout(() => {
        const form = document.querySelector('form');
        if (form) {
          const submitEvent = new Event('submit', { cancelable: true, bubbles: true });
          form.dispatchEvent(submitEvent);
        }
      }, 100);
    } else {
      setInput(message);
      // Trigger form submission after a small delay to allow input to update
      setTimeout(() => {
        const form = document.querySelector('form');
        if (form) {
          const submitEvent = new Event('submit', { cancelable: true, bubbles: true });
          form.dispatchEvent(submitEvent);
        }
      }, 100);
    }
  };

  return (
    <Transition.Root show={isOpen} as={Fragment}>
      <Dialog as="div" className="relative z-50" onClose={onClose}>
        <div className="fixed inset-0" />
        <div className="fixed inset-0 overflow-hidden">
          <div className="absolute inset-0 overflow-hidden">
            <div className="pointer-events-none fixed inset-y-0 right-0 flex max-w-full pl-10 sm:pl-16">
              <Transition.Child
                as={Fragment}
                enter="transform transition ease-in-out duration-500 sm:duration-700"
                enterFrom="translate-x-full"
                enterTo="translate-x-0"
                leave="transform transition ease-in-out duration-500 sm:duration-700"
                leaveFrom="translate-x-0"
                leaveTo="translate-x-full"
              >
                <Dialog.Panel className="pointer-events-auto w-screen max-w-2xl">
                  <div className="flex h-full flex-col overflow-y-scroll bg-white dark:bg-gray-800 shadow-xl">
                    <div className="px-4 py-6 sm:px-6 bg-primary-700">
                      <div className="flex items-center justify-between">
                        <Dialog.Title className="text-lg font-medium text-white">
                          SmartLinks AI Assistant
                        </Dialog.Title>
                        <div className="ml-3 flex h-7 items-center">
                          <button
                            type="button"
                            className="rounded-md bg-primary-700 text-primary-200 hover:text-white focus:outline-none focus:ring-2 focus:ring-white"
                            onClick={onClose}
                          >
                            <span className="sr-only">Close panel</span>
                            <XMarkIcon className="h-5 w-5" aria-hidden="true" />
                          </button>
                        </div>
                      </div>
                      <div className="mt-1">
                        <p className="text-sm text-primary-200">
                          Ask me anything about your SmartLinks dashboard and metrics.
                        </p>
                      </div>
                    </div>
                    
                    {/* Quick action buttons */}
                    <div className="border-b border-gray-200 dark:border-gray-600 bg-gray-50 dark:bg-gray-700 px-4 py-3">
                      <div className="flex flex-wrap gap-2">
                        <button
                          type="button"
                          onClick={() => handleQuickAction('status', 'What is the current status of the system?')}
                          className="inline-flex items-center rounded-full bg-white dark:bg-gray-800 px-3 py-1 text-xs font-medium text-gray-700 dark:text-gray-100 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-600 hover:bg-gray-50 dark:hover:bg-gray-700"
                        >
                          System Status
                        </button>
                        <button
                          type="button"
                          onClick={() => handleQuickAction('metrics', 'Show me the latest metrics')}
                          className="inline-flex items-center rounded-full bg-white dark:bg-gray-900 px-3 py-1 text-xs font-medium text-gray-700 dark:text-gray-200 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          View Metrics
                        </button>
                        <button
                          type="button"
                          onClick={() => handleQuickAction('discovery', 'Analyze traffic and find opportunities')}
                          className="inline-flex items-center rounded-full bg-yellow-50 dark:bg-yellow-900/30 px-3 py-1 text-xs font-medium text-yellow-700 dark:text-yellow-300 shadow-sm ring-1 ring-inset ring-yellow-200 dark:ring-yellow-800 hover:bg-yellow-100 dark:hover:bg-yellow-900/50"
                        >
                          <LightBulbIcon className="h-3.5 w-3.5 mr-1" />
                          Find Opportunities
                        </button>
                        <button
                          type="button"
                          onClick={() => handleQuickAction('help', 'What can you help me with?')}
                          className="inline-flex items-center rounded-full bg-white dark:bg-gray-900 px-3 py-1 text-xs font-medium text-gray-700 dark:text-gray-200 shadow-sm ring-1 ring-inset ring-gray-300 dark:ring-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800"
                        >
                          Help
                        </button>
                      </div>
                    </div>

                    {/* Chat messages */}
                    <div className="flex-1 overflow-y-auto p-4">
                      <div className="space-y-4">
                        {messages.map((message) => (
                          <div
                            key={message.id}
                            className={`flex ${
                              message.role === 'user' ? 'justify-end' : 'justify-start'
                            }`}
                          >
                            <div
                              className={`max-w-3/4 rounded-lg px-4 py-2 ${
                                message.role === 'user'
                                  ? 'bg-primary-600 text-white rounded-br-none'
                                  : 'bg-gray-100 dark:bg-gray-700 text-gray-800 dark:text-gray-100 rounded-bl-none'
                              }`}
                            >
                              {message.role === 'assistant' ? (
                                <div className="prose prose-sm max-w-none">
                                  <ReactMarkdown>{message.content}</ReactMarkdown>
                                </div>
                              ) : (
                                <p>{message.content}</p>
                              )}
                              <p className="mt-1 text-xs opacity-70">
                                {message.timestamp.toLocaleTimeString([], {
                                  hour: '2-digit',
                                  minute: '2-digit',
                                })}
                              </p>
                            </div>
                          </div>
                        ))}
                        {isLoading && (
                          <div className="flex justify-start">
                            <div className="rounded-lg bg-gray-100 dark:bg-gray-700 px-4 py-2 text-gray-800 dark:text-gray-100">
                              <div className="flex items-center space-x-2">
                                <ArrowPathIcon className="h-3.5 w-3.5 animate-spin" />
                                <span>Thinking...</span>
                              </div>
                            </div>
                          </div>
                        )}
                        <div ref={messagesEndRef} />
                      </div>
                    </div>

                    {/* Input area */}
                    <div className="border-t border-gray-200 dark:border-gray-600 p-4">
                      <form onSubmit={handleSubmit}>
                        <div className="flex rounded-md shadow-sm">
                          <div className="relative flex flex-grow items-stretch focus-within:z-10">
                            <input
                              type="text"
                              className="block w-full rounded-none rounded-l-md border-0 py-3 px-4 text-gray-900 dark:text-gray-100 bg-white dark:bg-gray-800 ring-1 ring-inset ring-gray-300 dark:ring-gray-600 placeholder:text-gray-400 dark:placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-primary-600 sm:text-sm sm:leading-6"
                              placeholder="Ask me anything..."
                              value={input}
                              onChange={(e) => setInput(e.target.value)}
                              disabled={isLoading}
                            />
                          </div>
                          <button
                            type="submit"
                            disabled={!input.trim() || isLoading}
                            className={`relative -ml-px inline-flex items-center gap-x-1.5 rounded-r-md px-4 py-2 text-sm font-semibold text-white shadow-sm ${
                              !input.trim() || isLoading
                                ? 'bg-gray-400 cursor-not-allowed'
                                : 'bg-primary-600 hover:bg-primary-700'
                            }`}
                          >
                            <PaperAirplaneIcon className="-ml-0.5 h-4 w-4" aria-hidden="true" />
                            <span className="hidden sm:inline">Send</span>
                          </button>
                        </div>
                      </form>
                      <p className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                        SmartLinks AI may produce inaccurate information about people, places, or facts.
                      </p>
                    </div>
                  </div>
                </Dialog.Panel>
              </Transition.Child>
            </div>
          </div>
        </div>
      </Dialog>
    </Transition.Root>
  );
}

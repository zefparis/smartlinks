import { Fragment, useState } from 'react';
import { Menu, Transition } from '@headlessui/react';
import { Bars3Icon, BellIcon, SparklesIcon } from '@heroicons/react/24/outline';
import { useServiceStatus } from '@/contexts/ServiceStatusContext';
import { Moon, Sun } from 'lucide-react';
import { useTheme } from '@/contexts/ThemeContext';
import { useNavigate } from 'react-router-dom';

type HeaderProps = {
  setSidebarOpen: (open: boolean) => void;
};

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

export default function Header({ setSidebarOpen }: HeaderProps) {
  const { status } = useServiceStatus();
  const { theme, toggleTheme } = useTheme();
  const navigate = useNavigate();
  const [services] = useState([
    { id: 'router', name: 'Router', status: status.router },
    { id: 'autopilot', name: 'Autopilot', status: status.autopilot },
    { id: 'probes', name: 'Probes', status: status.probes },
  ]);

  return (
    <header className="sticky top-0 z-40 flex h-16 shrink-0 items-center gap-x-4 border-b border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-4 shadow-sm sm:gap-x-6 sm:px-6 lg:px-8">
      <button
        type="button"
        className="-m-2.5 p-2.5 text-gray-700 dark:text-gray-200 lg:hidden"
        onClick={() => setSidebarOpen(true)}
      >
        <span className="sr-only">Open sidebar</span>
        <Bars3Icon className="h-6 w-6" aria-hidden="true" />
      </button>

      {/* Separator */}
      <div className="h-6 w-px bg-gray-200 dark:bg-gray-700 lg:hidden" aria-hidden="true" />

      <div className="flex flex-1 gap-x-4 self-stretch lg:gap-x-6">
        <div className="flex-1"></div>
        <div className="flex items-center gap-x-4 lg:gap-x-6">
          {/* Theme toggle */}
          <button
            type="button"
            onClick={toggleTheme}
            className="-m-2.5 p-2.5 text-gray-700 dark:text-gray-200 hover:text-primary-600"
            aria-label="Toggle theme"
            title={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
          >
            {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          </button>
          {/* Service status indicators */}
          <div className="hidden md:flex items-center space-x-4">
            {services.map((service) => (
              <div key={service.id} className="flex items-center">
                <span
                  className={classNames(
                    service.status ? 'bg-green-400' : 'bg-gray-200',
                    'flex h-2.5 w-2.5 rounded-full mr-2'
                  )}
                  aria-hidden="true"
                />
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300">
                  {service.name}
                </span>
              </div>
            ))}
          </div>

          {/* AI Assistant Button */}
          <button
            type="button"
            onClick={() => navigate('/assistant')}
            className="-m-2.5 p-2.5 text-indigo-600 hover:text-indigo-700 dark:text-indigo-400 dark:hover:text-indigo-300"
            title="Ouvrir l'assistant IA"
          >
            <span className="sr-only">Assistant IA</span>
            <SparklesIcon className="h-6 w-6" aria-hidden="true" />
          </button>
          
          {/* Notifications */}
          <button
            type="button"
            className="-m-2.5 p-2.5 text-gray-400 hover:text-gray-500 dark:text-gray-400 dark:hover:text-gray-300"
          >
            <span className="sr-only">View notifications</span>
            <BellIcon className="h-6 w-6" aria-hidden="true" />
          </button>

          {/* Profile dropdown */}
          <Menu as="div" className="relative">
            <Menu.Button className="-m-1.5 flex items-center p-1.5">
              <span className="sr-only">Open user menu</span>
              <div className="h-8 w-8 rounded-full bg-primary-500 flex items-center justify-center text-white font-medium">
                A
              </div>
            </Menu.Button>
            <Transition
              as={Fragment}
              enter="transition ease-out duration-100"
              enterFrom="transform opacity-0 scale-95"
              enterTo="transform opacity-100 scale-100"
              leave="transition ease-in duration-75"
              leaveFrom="transform opacity-100 scale-100"
              leaveTo="transform opacity-0 scale-95"
            >
              <Menu.Items className="absolute right-0 z-10 mt-2.5 w-32 origin-top-right rounded-md bg-white dark:bg-gray-800 py-2 shadow-lg ring-1 ring-gray-900/5 focus:outline-none">
                <Menu.Item>
                  {({ active }) => (
                    <a
                      href="#"
                      className={classNames(
                        active ? 'bg-gray-50 dark:bg-gray-700' : '',
                        'block px-3 py-1 text-sm leading-6 text-gray-900 dark:text-gray-100'
                      )}
                    >
                      Your profile
                    </a>
                  )}
                </Menu.Item>
                <Menu.Item>
                  {({ active }) => (
                    <a
                      href="#"
                      className={classNames(
                        active ? 'bg-gray-50 dark:bg-gray-800' : '',
                        'block px-3 py-1 text-sm leading-6 text-gray-900 dark:text-gray-100'
                      )}
                    >
                      Sign out
                    </a>
                  )}
                </Menu.Item>
              </Menu.Items>
            </Transition>
          </Menu>
        </div>
      </div>
    </header>
  );
}

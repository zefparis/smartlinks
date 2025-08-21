import { Fragment } from 'react';
import { Dialog, Transition } from '@headlessui/react';
import { useLocation, NavLink } from 'react-router-dom';
import {
  HomeIcon,
  ChartBarIcon,
  CursorArrowRaysIcon,
  ClockIcon,
  Cog6ToothIcon,
  XMarkIcon,
  BanknotesIcon,
  DocumentMagnifyingGlassIcon,
} from '@heroicons/react/24/outline';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon },
  { name: 'Analytics', href: '/analytics', icon: ChartBarIcon },
  { name: 'Finance', href: '/dashboard/finance', icon: BanknotesIcon },
  { name: 'Clicks', href: '/clicks', icon: CursorArrowRaysIcon },
  { name: 'History', href: '/history', icon: ClockIcon },
  { name: 'Scraper', href: '/tools/scraper', icon: DocumentMagnifyingGlassIcon },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon },
];

function classNames(...classes: string[]) {
  return classes.filter(Boolean).join(' ');
}

type SidebarProps = {
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
};

export default function Sidebar({ sidebarOpen, setSidebarOpen }: SidebarProps) {
  return (
    <>
      <Transition.Root show={sidebarOpen} as={Fragment}>
        <Dialog as="div" className="relative z-50 lg:hidden" onClose={setSidebarOpen}>
          <Transition.Child
            as={Fragment}
            enter="transition-opacity ease-linear duration-300"
            enterFrom="opacity-0"
            enterTo="opacity-100"
            leave="transition-opacity ease-linear duration-300"
            leaveFrom="opacity-100"
            leaveTo="opacity-0"
          >
            <div className="fixed inset-0 bg-gray-900/80" />
          </Transition.Child>

          <div className="fixed inset-0 flex">
            <Transition.Child
              as={Fragment}
              enter="transition ease-in-out duration-300 transform"
              enterFrom="-translate-x-full"
              enterTo="translate-x-0"
              leave="transition ease-in-out duration-300 transform"
              leaveFrom="translate-x-0"
              leaveTo="-translate-x-full"
            >
              <Dialog.Panel className="relative mr-16 flex w-full max-w-xs flex-1">
                <div className="flex grow flex-col gap-y-5 overflow-y-auto bg-white dark:bg-gray-900 px-6 pb-4">
                  <div className="flex h-16 shrink-0 items-center">
                    <img
                      className="h-8 w-auto"
                      src="/logo.svg"
                      alt="SmartLinks"
                    />
                  </div>
                  <nav className="flex flex-1 flex-col">
                    <ul role="list" className="flex flex-1 flex-col gap-y-7">
                      <li>
                        <ul role="list" className="-mx-2 space-y-1">
                          {navigation.map((item) => (
                            <li key={item.name}>
                              <NavLink
                                to={item.href}
                                className={({ isActive }) =>
                                  classNames(
                                    isActive
                                      ? 'bg-gray-50 dark:bg-gray-700 text-primary-600'
                                      : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-700 hover:text-primary-600',
                                    'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                                  )
                                }
                              >
                                {({ isActive }) => (
                                  <>
                                    <item.icon
                                      className={classNames(
                                        isActive ? 'text-primary-600' : 'text-gray-400 dark:text-gray-500 group-hover:text-primary-600',
                                        'h-6 w-6 shrink-0'
                                      )}
                                      aria-hidden="true"
                                    />
                                    {item.name}
                                  </>
                                )}
                              </NavLink>
                            </li>
                          ))}
                        </ul>
                      </li>
                      <li className="mt-auto">
                        <a
                          href="#"
                          className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-primary-600"
                        >
                          <Cog6ToothIcon
                            className="h-6 w-6 shrink-0 text-gray-400 dark:text-gray-500 group-hover:text-primary-600"
                            aria-hidden="true"
                          />
                          Settings
                        </a>
                      </li>
                    </ul>
                  </nav>
                </div>
              </Dialog.Panel>
            </Transition.Child>
          </div>
        </Dialog>
      </Transition.Root>

      {/* Static sidebar for desktop */}
      <div className="hidden lg:fixed lg:inset-y-0 lg:z-50 lg:flex lg:w-64 lg:flex-col">
        <div className="flex grow flex-col gap-y-5 overflow-y-auto border-r border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-900 px-6 pb-4">
          <div className="flex h-16 shrink-0 items-center">
            <h1 className="text-xl font-bold text-primary-600">SmartLinks</h1>
          </div>
          <nav className="flex flex-1 flex-col">
            <ul role="list" className="flex flex-1 flex-col gap-y-7">
              <li>
                <ul role="list" className="-mx-2 space-y-1">
                  {navigation.map((item) => (
                    <NavLink
                      key={item.name}
                      to={item.href}
                      className={({ isActive }) =>
                        classNames(
                          isActive
                            ? 'bg-gray-50 dark:bg-gray-800 text-primary-600'
                            : 'text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-primary-600',
                          'group flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6'
                        )
                      }
                    >
                      {({ isActive }) => (
                        <>
                          <item.icon
                            className={classNames(
                              isActive ? 'text-primary-600' : 'text-gray-400 dark:text-gray-500 group-hover:text-primary-600',
                              'h-6 w-6 shrink-0'
                            )}
                            aria-hidden="true"
                          />
                          {item.name}
                        </>
                      )}
                    </NavLink>
                  ))}
                </ul>
              </li>
              <li className="mt-auto">
                <a
                  href="#"
                  className="group -mx-2 flex gap-x-3 rounded-md p-2 text-sm font-semibold leading-6 text-gray-700 dark:text-gray-200 hover:bg-gray-50 dark:hover:bg-gray-800 hover:text-primary-600"
                >
                  <Cog6ToothIcon
                    className="h-6 w-6 shrink-0 text-gray-400 dark:text-gray-500 group-hover:text-primary-600"
                    aria-hidden="true"
                  />
                  Settings
                </a>
              </li>
            </ul>
          </nav>
        </div>
      </div>
    </>
  );
}

'use client';

import { Transition } from '@headlessui/react';

export default function PageHeader() {
  return (
    <Transition
      show={true}
      appear={true}
      enter="transition-all duration-500"
      enterFrom="opacity-0 -translate-y-4"
      enterTo="opacity-100 translate-y-0"
    >
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <h1 className="text-2xl font-bold text-gray-900">Jobs Skills Explorer</h1>
          <p className="text-sm text-gray-600 mt-1">View and edit job skills with ML enrichment</p>
        </div>
      </header>
    </Transition>
  );
}

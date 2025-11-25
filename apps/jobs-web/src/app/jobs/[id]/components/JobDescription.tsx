import { Disclosure, DisclosureButton, DisclosurePanel, Transition } from '@headlessui/react';
import Link from 'next/link';
import { Button } from '@/components/ui/Button';
import { ChevronDown, ChevronLeft, ChevronRight } from 'lucide-react';

interface JobDescriptionProps {
  highlightedDescription: string;
  onTextSelection: () => void;
  clusterName?: string;
  previousJobId?: string | null;
  nextJobId?: string | null;
}

export default function JobDescription({ 
  highlightedDescription, 
  onTextSelection, 
  clusterName,
  previousJobId,
  nextJobId
}: JobDescriptionProps) {
  return (
    <div className="lg:col-span-2 space-y-6">
      {/* Cluster Badge */}
      {clusterName && (
        <div>
          <span className="inline-flex items-center px-3 py-1 rounded-full text-sm font-medium bg-purple-100 text-purple-800">
            {clusterName}
          </span>
        </div>
      )}

      {/* Job Description with Highlighted Skills */}
      <Disclosure defaultOpen as="div" className="bg-white rounded-lg shadow-sm">
        {({ open }) => (
          <>            
            {/* Navigation Buttons */}
            <div className="flex-1">
                <div className="flex justify-between gap-2 p-6">
                    <Button
                        as={previousJobId ? Link : 'button'}
                        href={previousJobId ? `/jobs/${previousJobId}` : undefined}
                        disabled={!previousJobId}
                        variant="outline"
                        size="sm"
                        className="items-center min-w-[32px] flex"
                        leftIcon={<ChevronLeft className="w-4 h-4" />}
                        title="Previous Job"
                    >
                        Previous
                    </Button>
                    <Button
                        as={nextJobId ? Link : 'button'}
                        href={nextJobId ? `/jobs/${nextJobId}` : undefined}
                        disabled={!nextJobId}
                        variant="outline"
                        size="sm"
                        className="items-center min-w-[32px] flex"
                        rightIcon={<ChevronRight className="w-4 h-4" />}
                        title="Next Job"
                    >
                    Next
                    </Button>
                </div>
            </div>

            <div className="p-6 pb-4">
              <DisclosureButton className="flex items-center gap-2 text-left group">
                <h2 className="text-lg font-semibold text-gray-900">Job Description</h2>
                <ChevronDown 
                  className={`w-5 h-5 text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`}
                />
              </DisclosureButton>
            </div>

            <Transition
              enter="transition duration-100 ease-out"
              enterFrom="transform scale-95 opacity-0"
              enterTo="transform scale-100 opacity-100"
              leave="transition duration-75 ease-out"
              leaveFrom="transform scale-100 opacity-100"
              leaveTo="transform scale-95 opacity-0"
            >
              <DisclosurePanel className="px-6 pb-6">
                <div className="text-gray-700 leading-relaxed">
                  <p className="text-sm text-gray-500 mb-4 italic">
                    Select text to add as a new skill, or click highlighted skills to edit
                  </p>
                  <div
                    onMouseUp={onTextSelection}
                    dangerouslySetInnerHTML={{ __html: highlightedDescription }}
                    className="prose prose-sm max-w-none 
                      prose-headings:font-semibold prose-headings:text-gray-900 prose-headings:mt-6 prose-headings:mb-3
                      prose-p:text-gray-700 prose-p:my-3 prose-p:leading-relaxed
                      prose-li:text-gray-700 prose-li:my-1
                      prose-ul:my-3 prose-ol:my-3
                      prose-strong:text-gray-900 prose-strong:font-semibold
                      [&>*:first-child]:mt-0"
                  />
                </div>
              </DisclosurePanel>
            </Transition>
          </>
        )}
      </Disclosure>
    </div>
  );
}

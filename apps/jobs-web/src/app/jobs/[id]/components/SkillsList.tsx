import { Fragment, useState, useMemo } from 'react';
import { Disclosure, DisclosureButton, DisclosurePanel, Transition, Menu, MenuButton, MenuItems, MenuItem, Button as HeadlessButton } from '@headlessui/react';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { Tag, ChevronDown, MoreVertical, Plus, CheckCheck, XCircle, ArrowUpDown } from 'lucide-react';
import { HandThumbUpIcon, HandThumbDownIcon } from '@heroicons/react/24/outline';
import { Skill, SkillType } from '@/types/skills';

type SkillListMode = 'suggested' | 'approved';
type SortOrder = 'confidence-desc' | 'confidence-asc' | 'name-asc' | 'name-desc';

interface SkillsListProps {
  mode: SkillListMode;
  // Suggested mode props
  skills?: Skill[];
  onApprove?: (skillId: string) => void;
  onReject?: (skillId: string) => void;
  onBatchApprove?: (skillIds: string[]) => void;
  onBatchReject?: (skillIds: string[]) => void;
  // Approved mode props
  skillsByCategory?: Record<string, Skill[]>;
  totalCount?: number;
  onEditSkill?: (skillId: string, skillType: SkillType) => void;
  onAddSkill?: () => void;
}

export default function SkillsList({
  mode,
  skills = [],
  onApprove,
  onReject,
  onBatchApprove,
  onBatchReject,
  skillsByCategory = {},
  totalCount = 0,
  onEditSkill,
  onAddSkill,
}: SkillsListProps) {
  const isSuggestedMode = mode === 'suggested';
  const [sortOrder, setSortOrder] = useState<SortOrder>('confidence-desc');

  // Helper function to get confidence badge color
  const getConfidenceBadge = (score: number) => {
    const percentage = Math.round(score * 100);
    if (score >= 0.85) return { variant: 'success' as const, label: `${percentage}%` };
    if (score >= 0.75) return { variant: 'primary' as const, label: `${percentage}%` };
    if (score >= 0.65) return { variant: 'warning' as const, label: `${percentage}%` };
    return { variant: 'secondary' as const, label: `${percentage}%` };
  };

  // Sort skills based on selected order
  const sortedSkills = useMemo(() => {
    if (!isSuggestedMode) return skills;
    
    const sorted = [...skills];
    switch (sortOrder) {
      case 'confidence-desc':
        return sorted.sort((a, b) => b.confidence_score - a.confidence_score);
      case 'confidence-asc':
        return sorted.sort((a, b) => a.confidence_score - b.confidence_score);
      case 'name-asc':
        return sorted.sort((a, b) => a.skill_name.localeCompare(b.skill_name));
      case 'name-desc':
        return sorted.sort((a, b) => b.skill_name.localeCompare(a.skill_name));
      default:
        return sorted;
    }
  }, [skills, sortOrder, isSuggestedMode]);

  // Calculate batch operation counts
  const highConfidenceSkills = skills.filter(s => s.confidence_score >= 0.85);
  const lowConfidenceSkills = skills.filter(s => s.confidence_score < 0.75);

  // Batch operation handlers
  const handleBatchApproveHigh = () => {
    if (onBatchApprove && highConfidenceSkills.length > 0) {
      onBatchApprove(highConfidenceSkills.map(s => s.skill_id));
    }
  };

  const handleBatchRejectLow = () => {
    if (onBatchReject && lowConfidenceSkills.length > 0) {
      onBatchReject(lowConfidenceSkills.map(s => s.skill_id));
    }
  };

  // Don't render suggested skills if empty
  if (isSuggestedMode && skills.length === 0) return null;

  const title = isSuggestedMode 
    ? `Suggested Skills (${skills.length})` 
    : `Approved Skills (${totalCount})`;

  const description = isSuggestedMode
    ? 'Smart skills. Approve to add to lexicon or reject to delete permanently.'
    : null;

  return (
    <Disclosure 
      defaultOpen 
      as="div" 
      className={isSuggestedMode ? 'mb-6 pb-6 border-b border-gray-200' : ''}
    >
      {({ open }) => (
        <>
          <div className="flex flex-1 items-center mb-4">
            <DisclosureButton className="flex items-center gap-2 text-left group">
              <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                <Tag className="w-5 h-5 text-gray-500" />
                {title}
              </h2>
              <ChevronDown 
                className={`w-5 h-5 text-gray-500 transition-transform ${open ? 'rotate-180' : ''}`}
              />
            </DisclosureButton>
            
            <div className="flex items-center gap-2">
              {isSuggestedMode && (
                <>
                  {/* Sort dropdown */}
                  <Menu as="div" className="relative">
                    <MenuButton as={Button} variant="outline" size="sm" leftIcon={<ArrowUpDown className="w-4 h-4" />}>
                      Sort
                    </MenuButton>
                    <Transition
                      as={Fragment}
                      enter="transition ease-out duration-100"
                      enterFrom="transform opacity-0 scale-95"
                      enterTo="transform opacity-100 scale-100"
                      leave="transition ease-in duration-75"
                      leaveFrom="transform opacity-100 scale-100"
                      leaveTo="transform opacity-0 scale-95"
                    >
                      <MenuItems className="absolute right-0 mt-2 w-56 origin-top-right rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                        <div className="py-1">
                          <MenuItem>
                            {({ active }) => (
                              <button
                                onClick={() => setSortOrder('confidence-desc')}
                                className={`${
                                  active ? 'bg-gray-100' : ''
                                } ${sortOrder === 'confidence-desc' ? 'font-semibold' : ''} block w-full text-left px-4 py-2 text-sm text-gray-700`}
                              >
                                Confidence: High to Low
                              </button>
                            )}
                          </MenuItem>
                          <MenuItem>
                            {({ active }) => (
                              <button
                                onClick={() => setSortOrder('confidence-asc')}
                                className={`${
                                  active ? 'bg-gray-100' : ''
                                } ${sortOrder === 'confidence-asc' ? 'font-semibold' : ''} block w-full text-left px-4 py-2 text-sm text-gray-700`}
                              >
                                Confidence: Low to High
                              </button>
                            )}
                          </MenuItem>
                          <MenuItem>
                            {({ active }) => (
                              <button
                                onClick={() => setSortOrder('name-asc')}
                                className={`${
                                  active ? 'bg-gray-100' : ''
                                } ${sortOrder === 'name-asc' ? 'font-semibold' : ''} block w-full text-left px-4 py-2 text-sm text-gray-700`}
                              >
                                Name: A to Z
                              </button>
                            )}
                          </MenuItem>
                          <MenuItem>
                            {({ active }) => (
                              <button
                                onClick={() => setSortOrder('name-desc')}
                                className={`${
                                  active ? 'bg-gray-100' : ''
                                } ${sortOrder === 'name-desc' ? 'font-semibold' : ''} block w-full text-left px-4 py-2 text-sm text-gray-700`}
                              >
                                Name: Z to A
                              </button>
                            )}
                          </MenuItem>
                        </div>
                      </MenuItems>
                    </Transition>
                  </Menu>
                  
                  {/* Batch approve high confidence */}
                  {highConfidenceSkills.length > 0 && (
                    <Button
                      onClick={handleBatchApproveHigh}
                      variant="success"
                      size="sm"
                      leftIcon={<CheckCheck className="w-4 h-4" />}
                      title={`Approve ${highConfidenceSkills.length} skills with ≥85% confidence`}
                    >
                      Approve High ({highConfidenceSkills.length})
                    </Button>
                  )}
                  
                  {/* Batch reject low confidence */}
                  {lowConfidenceSkills.length > 0 && (
                    <Button
                      onClick={handleBatchRejectLow}
                      variant="danger"
                      size="sm"
                      leftIcon={<XCircle className="w-4 h-4" />}
                      title={`Reject ${lowConfidenceSkills.length} skills with <75% confidence`}
                    >
                      Reject Low ({lowConfidenceSkills.length})
                    </Button>
                  )}
                </>
              )}
              
              {!isSuggestedMode && onAddSkill && (
                <Button
                  onClick={onAddSkill}
                  variant="outline"
                  size="sm"
                  leftIcon={<Plus className="w-4 h-4" />}
                >
                  Add Skill
                </Button>
              )}
            </div>
          </div>
          
          <Transition
            enter="transition duration-100 ease-out"
            enterFrom="transform scale-95 opacity-0"
            enterTo="transform scale-100 opacity-100"
            leave="transition duration-75 ease-out"
            leaveFrom="transform scale-100 opacity-100"
            leaveTo="transform scale-95 opacity-0"
          >
            <DisclosurePanel>
              {description && (
                <p className="text-sm text-gray-600 mb-4">{description}</p>
              )}

              {/* Suggested Mode - Flat list */}
              {isSuggestedMode && (
                <div className="space-y-2">
                  {sortedSkills.map(skill => {
                    const confidenceBadge = getConfidenceBadge(skill.confidence_score);
                    return (
                      <div
                        key={skill.skill_id}
                        className="flex items-center justify-between p-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                      >
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-2 mb-1">
                            <p className="text-sm font-medium text-gray-900 truncate">
                              {skill.skill_name}
                            </p>
                            <Badge variant={confidenceBadge.variant} size="sm">
                              {confidenceBadge.label}
                            </Badge>
                          </div>
                          <p className="text-xs text-gray-500 capitalize">
                            {skill.skill_category.replace(/_/g, ' ')}
                          </p>
                        </div>
                        <div className="flex gap-2 ml-4">
                          <HeadlessButton
                            onClick={() => onApprove?.(skill.skill_id)}
                            className="p-2 text-blue-600 hover:bg-blue-50 active:bg-blue-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                            title="Approve skill"
                          >
                            <HandThumbUpIcon className="w-5 h-5" />
                          </HeadlessButton>
                          <HeadlessButton
                            onClick={() => onReject?.(skill.skill_id)}
                            className="p-2 text-blue-600 hover:bg-blue-50 active:bg-blue-100 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-1"
                            title="Reject skill"
                          >
                            <HandThumbDownIcon className="w-5 h-5" />
                          </HeadlessButton>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}

              {/* Approved Mode - Grouped by category */}
              {!isSuggestedMode && (
                <div className="space-y-4">
                  {Object.entries(skillsByCategory).map(([category, categorySkills]) => (
                    <Disclosure key={category} defaultOpen as="div">
                      {({ open: categoryOpen }) => (
                        <>
                          <DisclosureButton className="w-full flex items-center justify-between text-left group">
                            <h3 className="text-sm font-medium text-gray-700 capitalize">
                              {category.replace(/_/g, ' ')} ({categorySkills.length})
                            </h3>
                            <ChevronDown 
                              className={`w-4 h-4 text-gray-400 transition-transform ${categoryOpen ? 'rotate-180' : ''}`}
                            />
                          </DisclosureButton>
                          
                          <Transition
                            enter="transition duration-100 ease-out"
                            enterFrom="transform scale-95 opacity-0"
                            enterTo="transform scale-100 opacity-100"
                            leave="transition duration-75 ease-out"
                            leaveFrom="transform scale-100 opacity-100"
                            leaveTo="transform scale-95 opacity-0"
                          >
                            <DisclosurePanel className="mt-2 space-y-2">
                              {categorySkills.map(skill => (
                                <div
                                  key={skill.skill_id}
                                  className="flex items-center justify-between p-2 bg-white border border-gray-200 rounded hover:bg-gray-50 transition-colors group"
                                >
                                  <div className="flex-1 min-w-0">
                                    <span className="text-sm text-gray-900">
                                      {skill.skill_name}
                                      {skill.skill_type && ` • ${skill.skill_type}`}
                                    </span>
                                  </div>
                                  
                                  <Menu as="div" className="relative">
                                    <MenuButton className="p-1 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded transition-colors">
                                      <MoreVertical className="w-4 h-4" />
                                    </MenuButton>
                                    
                                    <Transition
                                      as={Fragment}
                                      enter="transition ease-out duration-100"
                                      enterFrom="transform opacity-0 scale-95"
                                      enterTo="transform opacity-100 scale-100"
                                      leave="transition ease-in duration-75"
                                      leaveFrom="transform opacity-100 scale-100"
                                      leaveTo="transform opacity-0 scale-95"
                                    >
                                      <MenuItems className="absolute right-0 mt-1 w-32 origin-top-right rounded-lg bg-white shadow-lg ring-1 ring-black ring-opacity-5 focus:outline-none z-10">
                                        <div className="py-1">
                                          <MenuItem>
                                            {({ active }) => (
                                              <button
                                                onClick={() => onEditSkill?.(skill.skill_id, skill.skill_type || 'General')}
                                                className={`${
                                                  active ? 'bg-gray-100' : ''
                                                } block w-full text-left px-4 py-2 text-sm text-gray-700`}
                                              >
                                                Edit Type
                                              </button>
                                            )}
                                          </MenuItem>
                                        </div>
                                      </MenuItems>
                                    </Transition>
                                  </Menu>
                                </div>
                              ))}
                            </DisclosurePanel>
                          </Transition>
                        </>
                      )}
                    </Disclosure>
                  ))}
                </div>
              )}
            </DisclosurePanel>
          </Transition>
        </>
      )}
    </Disclosure>
  );
}

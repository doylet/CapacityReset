import { Dialog, DialogPanel, DialogTitle, Transition, TransitionChild, RadioGroup, RadioGroupOption, RadioGroupLabel, Button } from '@headlessui/react';
import { Fragment } from 'react';
import { Plus, Save } from 'lucide-react';
import { SkillType, SKILL_TYPES } from '@/types/skills';

interface SkillCategory {
  category: string;
  display_name: string;
  skill_count: number;
}

type SkillModalMode = 'add' | 'edit';

interface SkillModalProps {
  isOpen: boolean;
  mode: SkillModalMode;
  skillType: SkillType;
  onSkillTypeChange: (type: SkillType) => void;
  onSubmit: () => void;
  onCancel: () => void;
  // Add mode specific props
  skillName?: string;
  skillCategory?: string;
  skillCategories?: SkillCategory[];
  categoriesLoading?: boolean;
  onSkillNameChange?: (name: string) => void;
  onSkillCategoryChange?: (category: string) => void;
}

export default function SkillModal({
  isOpen,
  mode,
  skillType,
  onSkillTypeChange,
  onSubmit,
  onCancel,
  skillName = '',
  skillCategory = 'technical_skills',
  skillCategories = [],
  categoriesLoading = false,
  onSkillNameChange,
  onSkillCategoryChange,
}: SkillModalProps) {
  const isAddMode = mode === 'add';
  const title = isAddMode ? 'Add New Skill' : 'Edit Skill Type';
  const submitLabel = isAddMode ? 'Add Skill' : 'Save Changes';
  const SubmitIcon = isAddMode ? Plus : Save;

  return (
    <Transition show={isOpen} as={Fragment}>
      <Dialog onClose={onCancel} className="relative z-50">
        {/* Backdrop */}
        <TransitionChild
          as={Fragment}
          enter="ease-out duration-300"
          enterFrom="opacity-0"
          enterTo="opacity-100"
          leave="ease-in duration-200"
          leaveFrom="opacity-100"
          leaveTo="opacity-0"
        >
          <div className="fixed inset-0 bg-black/50" aria-hidden="true" />
        </TransitionChild>

        {/* Full-screen container */}
        <div className="fixed inset-0 flex items-center justify-center p-4">
          <TransitionChild
            as={Fragment}
            enter="ease-out duration-300"
            enterFrom="opacity-0 scale-95"
            enterTo="opacity-100 scale-100"
            leave="ease-in duration-200"
            leaveFrom="opacity-100 scale-100"
            leaveTo="opacity-0 scale-95"
          >
            <DialogPanel className="bg-white rounded-lg p-6 max-w-md w-full mx-4 shadow-xl">
              <DialogTitle className="text-lg font-semibold text-gray-900 mb-4">
                {title}
              </DialogTitle>

              <div className="space-y-4">
                {/* Add mode specific fields */}
                {isAddMode && (
                  <>
                    <div>
                      <label htmlFor="skill-name" className="block text-sm font-medium text-gray-700 mb-1">
                        Skill Name
                      </label>
                      <input
                        id="skill-name"
                        type="text"
                        value={skillName}
                        onChange={(e) => onSkillNameChange?.(e.target.value)}
                        placeholder="e.g., React, Python, Project Management"
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                      />
                    </div>

                    <div>
                      <label htmlFor="skill-category" className="block text-sm font-medium text-gray-700 mb-1">
                        Category
                      </label>
                      {categoriesLoading ? (
                        <div className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50 text-gray-500">
                          Loading categories...
                        </div>
                      ) : (
                        <select
                          id="skill-category"
                          value={skillCategory}
                          onChange={(e) => onSkillCategoryChange?.(e.target.value)}
                          className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:border-blue-500 focus:ring-2 focus:ring-blue-500 focus:outline-none"
                        >
                          {skillCategories.map((cat) => (
                            <option key={cat.category} value={cat.category}>
                              {cat.display_name}
                            </option>
                          ))}
                        </select>
                      )}
                    </div>
                  </>
                )}

                {/* Skill Type Selection (both modes) */}
                <div>
                  <RadioGroup value={skillType} onChange={onSkillTypeChange}>
                    <RadioGroupLabel className="block text-sm font-medium text-gray-700 mb-2">
                      Skill Type
                    </RadioGroupLabel>
                    <div className="space-y-2">
                      {SKILL_TYPES.map((type) => (
                        <RadioGroupOption
                          key={type}
                          value={type}
                          className={({ checked }) =>
                            `flex items-center gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${
                              checked ? 'border-blue-600 bg-blue-50' : 'border-gray-300 hover:bg-gray-50'
                            }`
                          }
                        >
                          {({ checked }) => (
                            <>
                              <div className={`h-4 w-4 rounded-full border-2 flex items-center justify-center ${
                                checked ? 'border-blue-600' : 'border-gray-300'
                              }`}>
                                {checked && <div className="h-2 w-2 rounded-full bg-blue-600" />}
                              </div>
                              <span className="text-sm font-medium text-gray-900">{type}</span>
                            </>
                          )}
                        </RadioGroupOption>
                      ))}
                    </div>
                  </RadioGroup>
                </div>
              </div>

              {/* Actions */}
              <div className="flex gap-3 mt-6">
                <Button
                  onClick={onSubmit}
                  className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 active:bg-blue-800 transition-colors shadow-sm hover:shadow focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2"
                >
                  <SubmitIcon className="w-4 h-4" />
                  {submitLabel}
                </Button>
                <Button
                  onClick={onCancel}
                  className="flex-1 px-4 py-2 bg-gray-200 text-gray-700 rounded-lg hover:bg-gray-300 active:bg-gray-400 transition-colors focus:outline-none focus:ring-2 focus:ring-gray-500 focus:ring-offset-2"
                >
                  Cancel
                </Button>
              </div>
            </DialogPanel>
          </TransitionChild>
        </div>
      </Dialog>
    </Transition>
  );
}

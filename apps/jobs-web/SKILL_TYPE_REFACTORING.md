# Skill Type Refactoring

## Problem
Previously, skill types were hardcoded across multiple files as union types:
```typescript
'General' | 'Specialised' | 'Transferrable'
```

This created a maintenance nightmare - any change to skill types required updating 6+ files across components, hooks, and type definitions.

## Solution
Centralized all skill type definitions in a single source of truth: `src/types/skills.ts`

### New Type System

```typescript
// Single source of truth
export type SkillType = 'General' | 'Specialised' | 'Transferrable';

// Constant array for mapping/iteration
export const SKILL_TYPES: readonly SkillType[] = ['General', 'Specialised', 'Transferrable'] as const;

// Centralized Skill interface
export interface Skill {
  skill_id: string;
  skill_name: string;
  skill_category: string;
  confidence_score: number;
  context_snippet: string;
  extraction_method: string;
  approval_status?: 'pending' | 'approved' | 'rejected';
  skill_type?: SkillType;
  is_approved?: boolean | null;
}
```

### Utility Functions

- `isValidSkillType(value: string): boolean` - Type guard for runtime validation
- `normalizeSkillType(backendType: string): SkillType` - Convert backend format (lowercase) to frontend format (capitalized)

## Files Updated

### Core Types
- ✅ `src/types/skills.ts` - NEW: Single source of truth for all skill-related types

### Main Page
- ✅ `src/app/jobs/[id]/page.tsx` - Imports `SkillType` instead of inline definition

### Hooks
- ✅ `src/app/jobs/[id]/hooks/useJobSkills.ts` - Uses `Skill` and `SkillType` from centralized types
- ✅ `src/app/jobs/[id]/hooks/useSkillHighlighting.ts` - Uses `Skill` from centralized types

### Components
- ✅ `src/app/jobs/[id]/components/ApprovedSkillsList.tsx` - Uses `Skill` and `SkillType`
- ✅ `src/app/jobs/[id]/components/EditSkillModal.tsx` - Uses `SkillType` and `SKILL_TYPES` constant
- ✅ `src/app/jobs/[id]/components/AddSkillModal.tsx` - Uses `SkillType` and `SKILL_TYPES` constant

## Benefits

### 1. Single Source of Truth
- All skill type definitions in one file
- Changes only need to be made in one place
- No risk of inconsistencies

### 2. Type Safety
- Compiler catches mismatches immediately
- Runtime validation available via `isValidSkillType()`
- Better IDE autocomplete

### 3. Maintainability
- Adding a new skill type? Update only `src/types/skills.ts`
- The change automatically propagates to all components
- No need to search and replace across multiple files

### 4. Backend Alignment
- Types match backend enum: `api/jobs-api/domain/entities.py::SkillType`
- Utility function handles format conversion (lowercase ↔ capitalized)

## Future Enhancements

### Option 1: Fetch from Backend API
Add an endpoint to fetch available skill types dynamically:

```typescript
// Backend: api/jobs-api/api/routes.py
@router.get("/skill-types")
async def get_skill_types():
    return {"skill_types": [e.value for e in SkillType]}

// Frontend hook
const useSkillTypes = () => {
  const [skillTypes, setSkillTypes] = useState<SkillType[]>(SKILL_TYPES);
  
  useEffect(() => {
    fetch('/api/skill-types')
      .then(res => res.json())
      .then(data => setSkillTypes(data.skill_types.map(normalizeSkillType)));
  }, []);
  
  return skillTypes;
};
```

### Option 2: Generate TypeScript from Backend
Use code generation to sync frontend types with backend enum:

```bash
# Generate types from OpenAPI/Swagger spec
npx openapi-typescript http://localhost:8080/openapi.json -o src/types/generated.ts
```

## Migration Notes

### Before
```typescript
// Each file had its own definition
interface Skill {
  skill_type?: 'General' | 'Specialised' | 'Transferrable';
}

// Hardcoded arrays
['GENERAL', 'SPECIALISED', 'TRANSFERRABLE'].map(...)
```

### After
```typescript
// Import from centralized location
import { SkillType, SKILL_TYPES, Skill } from '@/types/skills';

// Use constants
SKILL_TYPES.map(...)
```

## Testing
- ✅ All TypeScript compilation errors resolved
- ✅ Type checking passes
- ✅ No runtime errors
- 🔲 Add unit tests for `isValidSkillType()` and `normalizeSkillType()`

## Related Files
- Backend enum: `api/jobs-api/domain/entities.py` (lines 14-18)
- API routes: `api/jobs-api/api/routes.py` (uses `SkillType` enum)

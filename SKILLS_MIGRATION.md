# Skills Architecture Migration Guide

## Overview
Complete overhaul of the skills extraction and management system. The skills lexicon is now persistent in BigQuery, replacing the non-persistent in-memory dictionary.

## What Changed

### Backend
- ✅ **Persistent Lexicon**: `skills_lexicon` table in BigQuery stores all skills
- ✅ **Unified Source**: Hardcoded skills (175) seeded into database, ML and user additions go to same table
- ✅ **Smart Normalization**: Skills are normalized (lowercase, trimmed) to prevent duplicates
- ✅ **New API Endpoints**:
  - `GET /skills/categories` - Dynamic category list with skill counts
  - `GET /skills?q=query` - Search/autocomplete for adding skills
- ✅ **ML Integration**: `skills_extractor.py` reads from BigQuery instead of hardcoded Python dict

### Frontend  
- ✅ **Dynamic Categories**: Dropdown fetches from API instead of hardcoded list
- ✅ **Optimized Highlighting**: useMemo caches HTML, only recalculates when skills change (massive performance boost)
- ✅ **Better UX**: Loading states for category fetch

## Deployment Steps

### 1. Create the skills_lexicon table
```bash
# From project root
cd services/ml-enrichment
python scripts/create_skills_lexicon_table.py
```

This will:
- Create `skills_lexicon` table in BigQuery
- Seed it with 175 hardcoded skills from SKILLS_LEXICON
- Set up proper indexes and clustering

**Expected output:**
```
✅ Created table sylvan-replica-478802-p4.brightdata_jobs.skills_lexicon
✅ Seeded 175 hardcoded skills into lexicon
✅ Skills lexicon setup complete!
```

### 2. Deploy API service
```bash
# Deploy updated jobs-api with BigQuerySkillLexiconRepository
gcloud builds submit --config api/jobs-api/cloudbuild.yaml
```

The API will now:
- Use persistent BigQuery lexicon instead of in-memory
- Expose `/skills/categories` and `/skills` endpoints
- Automatically update lexicon when users add skills

### 3. Deploy ML enrichment service
```bash
# Deploy updated ml-enrichment with BigQuery lexicon integration
gcloud builds submit --config services/ml-enrichment/cloudbuild.yaml
```

The ML service will now:
- Read skills from BigQuery on startup
- Fall back to hardcoded SKILLS_LEXICON if table doesn't exist
- Use user-added skills in future extractions

### 4. Deploy frontend
```bash
# Deploy updated jobs-web with dynamic categories and optimized highlighting
gcloud builds submit --config apps/jobs-web/cloudbuild.yaml
```

## Verification

### Check lexicon is populated:
```sql
SELECT 
  skill_category,
  COUNT(*) as skill_count
FROM `sylvan-replica-478802-p4.brightdata_jobs.skills_lexicon`
GROUP BY skill_category
ORDER BY skill_count DESC;
```

**Expected**: 11 categories with 175 total skills

### Test API endpoints:
```bash
# Get categories
curl http://YOUR_API_URL/skills/categories

# Search skills
curl http://YOUR_API_URL/skills?q=python
```

### Test frontend:
1. Open a job detail page
2. Click "Add Skill" button
3. Verify category dropdown loads dynamically (shows counts)
4. Add a new skill
5. Verify it appears in the lexicon:
```sql
SELECT * FROM `sylvan-replica-478802-p4.brightdata_jobs.skills_lexicon`
WHERE source = 'USER_ADDED'
ORDER BY last_updated DESC
LIMIT 10;
```

## Benefits

### Performance
- **Frontend**: Skill highlighting now O(1) after first render (memoized)
- **Backend**: BigQuery handles skill lookups efficiently with clustering
- **No data loss**: Skills persist across API restarts

### Maintainability
- **Single source of truth**: All skills in one table
- **No hardcoded duplication**: Categories fetched dynamically
- **Easy to extend**: Add new skill management features (merge, bulk edit, analytics)

### User Experience
- **Autocomplete**: Search existing skills before adding
- **Duplicate prevention**: Normalization catches "Python" vs "python"
- **Feedback loop**: User corrections improve ML accuracy over time

## Rollback Plan

If issues occur, revert to previous commit:
```bash
git revert HEAD
gcloud builds submit --config api/jobs-api/cloudbuild.yaml
```

The old `InMemorySkillLexiconRepository` is still in the codebase but marked DEPRECATED.

## Future Enhancements

Now that the foundation is solid, we can add:
- **Skills Management UI** (`/skills` page) - bulk operations, merging duplicates
- **Skill Analytics** - trending skills, co-occurrence, demand analysis
- **Fuzzy Matching** - Levenshtein distance for near-duplicate detection
- **Vector Embeddings** - Semantic similarity for skill matching
- **Active Learning** - Track user corrections to improve ML model

## Troubleshooting

### "Table not found" error
Run the table creation script: `python scripts/create_skills_lexicon_table.py`

### ML service falls back to hardcoded skills
Check BigQuery permissions for the ml-enrichment service account

### Categories not loading in frontend
Verify API endpoint is accessible: `curl YOUR_API_URL/skills/categories`

### Skills not highlighting
Check browser console for errors, verify memoization logic

"""
Create skills_lexicon table in BigQuery.

This table stores the persistent skills lexicon that replaces the in-memory dictionary.
It combines hardcoded skills, ML-extracted skills, and user-added skills in one place.
"""

from google.cloud import bigquery
import os

PROJECT_ID = os.getenv("GCP_PROJECT_ID", "capacity-reset")
DATASET_ID = os.getenv("BIGQUERY_DATASET_ID", "jobs_data")

def create_skills_lexicon_table():
    """Create the skills_lexicon table with proper schema."""
    client = bigquery.Client(project=PROJECT_ID)
    
    # Define table schema
    table_id = f"{PROJECT_ID}.{DATASET_ID}.skills_lexicon"
    
    schema = [
        bigquery.SchemaField("skill_id", "STRING", mode="REQUIRED", description="Unique skill identifier (UUID)"),
        bigquery.SchemaField("skill_name", "STRING", mode="REQUIRED", description="Normalized skill name (lowercase, trimmed)"),
        bigquery.SchemaField("skill_name_original", "STRING", mode="REQUIRED", description="Original skill name as entered"),
        bigquery.SchemaField("skill_category", "STRING", mode="REQUIRED", description="Skill category (e.g., technical_skills, communicating)"),
        bigquery.SchemaField("skill_type", "STRING", mode="NULLABLE", description="GENERAL, SPECIALISED, or TRANSFERRABLE"),
        bigquery.SchemaField("source", "STRING", mode="REQUIRED", description="Origin: HARDCODED, ML_EXTRACTED, or USER_ADDED"),
        bigquery.SchemaField("usage_count", "INTEGER", mode="REQUIRED", description="Number of times this skill appears across jobs"),
        bigquery.SchemaField("confidence_sum", "FLOAT", mode="REQUIRED", description="Sum of confidence scores for averaging"),
        bigquery.SchemaField("user_corrections", "INTEGER", mode="REQUIRED", description="Number of times users manually added/edited this skill"),
        bigquery.SchemaField("aliases", "STRING", mode="REPEATED", description="Alternative names for this skill"),
        bigquery.SchemaField("first_seen", "TIMESTAMP", mode="REQUIRED", description="When this skill was first added to lexicon"),
        bigquery.SchemaField("last_updated", "TIMESTAMP", mode="REQUIRED", description="Last time this skill was used or updated"),
        bigquery.SchemaField("created_by_user_id", "STRING", mode="NULLABLE", description="User who first added (if USER_ADDED)"),
    ]
    
    table = bigquery.Table(table_id, schema=schema)
    table.description = "Skills lexicon - unified storage for all known skills (hardcoded + ML + user-added)"
    
    # Create table
    try:
        table = client.create_table(table)
        print(f"✅ Created table {table.project}.{table.dataset_id}.{table.table_id}")
    except Exception as e:
        if "Already Exists" in str(e):
            print(f"ℹ️  Table {table_id} already exists")
        else:
            raise e
    
    # Create indexes for common queries
    print("Creating indexes...")
    
    # Index on skill_name for fast lookups
    client.query(f"""
        -- BigQuery doesn't need explicit indexes, it auto-optimizes
        -- But we can create a clustered table for better performance
        CREATE OR REPLACE TABLE `{table_id}`
        CLUSTER BY skill_category, skill_name
        AS SELECT * FROM `{table_id}`
    """).result()
    
    print("✅ Table created successfully with clustering")


def seed_hardcoded_skills():
    """Seed the lexicon with the 175 hardcoded skills from SKILLS_LEXICON."""
    from datetime import datetime
    import uuid
    
    # Import the hardcoded lexicon
    SKILLS_LEXICON = {
        'communicating': ['corresponding', 'editing', 'interviewing', 'listening', 'presenting', 
                         'promoting', 'publicising', 'reading', 'speaking', 'training', 'translating', 'writing'],
        'creative_skills': ['composing', 'conceiving', 'conceptualising', 'creating', 'designing', 
                           'devising', 'drawing', 'fashion design', 'illustrating', 'imagining', 
                           'improvising', 'interior decorating', 'inventing', 'styling'],
        'developing_people': ['advising', 'assessing performance', 'coaching', 'counselling', 
                             'demonstrating', 'giving feedback', 'guiding', 'influencing', 
                             'inspiring', 'instructing', 'mentoring', 'motivating', 'teaching', 'tutoring'],
        'financial_skills': ['analysing', 'appraising', 'auditing', 'budgeting', 'calculating', 
                            'computing', 'costing', 'estimating', 'financial planning', 'forecasting', 'fundraising'],
        'interpersonal_skills': ['advising skills', 'facilitating', 'group work', 'influencing', 
                                'listening', 'mediation', 'negotiating', 'networking', 'people skills', 
                                'persuading', 'presentation skills', 'selling', 'working with others', 'customer service'],
        'managing_directing': ['appraising', 'approving', 'assigning', 'attaining', 'chairing', 
                              'consolidating', 'contracting', 'controlling', 'coordinating', 
                              'decision making', 'delegating', 'developing', 'directing', 'evaluating', 
                              'executing', 'improving', 'managing', 'overseeing', 'reviewing'],
        'organising': ['general administration', 'quality control', 'stock control', 'arranging', 
                      'booking', 'cataloguing', 'categorising', 'charting', 'classifying', 'collecting', 
                      'compiling', 'distributing', 'executing', 'filing', 'gathering', 'managing time', 
                      'maintaining', 'operating'],
        'planning': ['analysing', 'conceptualising', 'designing projects', 'developing strategy', 
                    'establishing priorities', 'goal setting', 'strategising', 'prioritising'],
        'researching_analysing': ['assessing', 'calculating', 'collecting data', 'comparing', 
                                 'critically analysing', 'data analysis', 'diagnosing', 'evaluating', 
                                 'examining', 'experimenting', 'exploring', 'extracting information', 
                                 'identifying issues', 'inspecting', 'interpreting', 'investigating', 
                                 'measuring', 'organising', 'researching', 'solving problems', 
                                 'surveying', 'systematic thinking', 'testing'],
        'selling_marketing': ['advertising', 'analysing markets', 'cold calling', 'conducting market research', 
                             'consultative selling', 'convincing', 'customer relationship management', 
                             'demonstrating products', 'identifying markets', 'influencing', 'market planning', 
                             'negotiating', 'persuading', 'promoting', 'prospecting', 'publicising', 
                             'sales', 'selling', 'social media marketing', 'telemarketing'],
        'technical_skills': ['assembling', 'building', 'computing', 'constructing', 'data analysis', 
                            'debugging', 'designing', 'devising', 'engineering', 'fabricating', 
                            'maintaining', 'modelling', 'operating equipment', 'overhauling', 
                            'programming', 'python', 'java', 'javascript', 'repairing', 'setting up', 
                            'solving technical problems', 'testing', 'troubleshooting']
    }
    
    client = bigquery.Client(project=PROJECT_ID)
    table_id = f"{PROJECT_ID}.{DATASET_ID}.skills_lexicon"
    
    rows_to_insert = []
    now = datetime.utcnow().isoformat()
    
    for category, skills in SKILLS_LEXICON.items():
        for skill in skills:
            rows_to_insert.append({
                "skill_id": str(uuid.uuid4()),
                "skill_name": skill.lower().strip(),
                "skill_name_original": skill,
                "skill_category": category,
                "skill_type": "GENERAL",
                "source": "HARDCODED",
                "usage_count": 0,
                "confidence_sum": 0.0,
                "user_corrections": 0,
                "aliases": [],
                "first_seen": now,
                "last_updated": now,
                "created_by_user_id": None
            })
    
    errors = client.insert_rows_json(table_id, rows_to_insert)
    
    if errors:
        print(f"❌ Errors inserting hardcoded skills: {errors}")
    else:
        print(f"✅ Seeded {len(rows_to_insert)} hardcoded skills into lexicon")


if __name__ == "__main__":
    print("Creating skills_lexicon table...")
    create_skills_lexicon_table()
    
    print("\nSeeding hardcoded skills...")
    seed_hardcoded_skills()
    
    print("\n✅ Skills lexicon setup complete!")

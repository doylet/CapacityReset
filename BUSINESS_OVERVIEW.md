# CapacityReset: Business Overview

**Last Updated**: November 30, 2025

## What is CapacityReset?

CapacityReset is an intelligent job market research platform that automatically collects LinkedIn job postings and uses machine learning to extract valuable insights. Think of it as your personal job market analyst that works 24/7.

### The Problem We Solve

**Without CapacityReset:**
- Manually searching job boards takes 10-20 hours per week
- Copy-pasting job descriptions into spreadsheets
- No way to track skill trends across companies
- Missing opportunities because of non-standard job titles
- Can't tell which skills are "must-have" vs "nice-to-have"

**With CapacityReset:**
- Automatic job collection while you sleep
- ML extracts all skills from descriptions in seconds
- See patterns across hundreds of jobs instantly
- Find similar jobs even with different titles
- Data-driven answers to "what should I learn next?"

---

## How It Works (5 Simple Steps)

### 1. **Automated Job Collection** 
🤖 We scrape LinkedIn every day for specific roles and locations

- Set up search queries once (e.g., "Product Manager in Sydney")
- Cloud Scheduler runs scraping automatically
- BrightData API bypasses LinkedIn's anti-bot protection
- Raw job data saved to Google Cloud Storage
- **Result**: 1000+ jobs collected daily with zero manual effort

### 2. **Data Transformation**
📊 Raw JSON from scraping gets cleaned and organized

- ETL service loads jobs from cloud storage
- Extracts company info, salary, location, description
- Removes duplicates and invalid entries
- Stores in BigQuery database for fast querying
- **Result**: Clean, structured job data ready for analysis

### 3. **ML Enrichment** (The Magic Happens Here)
✨ Machine learning extracts insights from job descriptions

**Three types of enrichment:**

**A) Skills Extraction** (using spaCy NLP)
- Identifies technical skills: "Python", "AWS", "React"
- Finds soft skills: "leadership", "communication"
- Categorizes: programming languages, cloud tools, frameworks
- Assigns confidence scores based on how often mentioned
- **Example**: "5 years Python and AWS experience" → Extracts ["Python", "AWS"]

**B) Semantic Embeddings** (using Vertex AI)
- Converts job descriptions into mathematical vectors (768 numbers)
- Similar jobs get similar vectors
- Enables "find jobs like this one" search
- Works even if job titles are different
- **Example**: Find all data engineering roles, even if titled "Analytics Engineer"

**C) Job Clustering** (using K-means)
- Groups similar jobs automatically
- Generates cluster names from common keywords
- Reveals hidden job categories
- **Example**: Discovers "Senior Backend - Python/Django/AWS" cluster across companies

### 4. **Human Feedback Loop**
👥 Users improve the AI by validating results

- Review ML-extracted skills: ✓ Approve or ✗ Reject
- Highlight missed skills and add them manually
- Annotate job sections (responsibilities vs requirements)
- All feedback trains future ML models
- **Result**: System gets smarter the more you use it

### 5. **Interactive Analysis**
📈 Explore jobs through web interface or API

- Filter by location, skills, date, company
- Compare skill requirements across multiple jobs
- Generate reports: "Most in-demand skills for Data Engineers"
- Track favorites and hide irrelevant jobs
- Navigate between similar roles
- **Result**: Answer market questions in minutes instead of days

---

## Who Uses This Platform?

### 👔 Job Seekers & Career Changers
**Goal**: Figure out what skills to learn

**Typical Workflow:**
1. Search for target roles in desired location
2. Review skills extracted from 20-50 job postings
3. Generate report: "Top 10 skills for Product Managers"
4. Identify skill gaps: "I know SQL but need Tableau"
5. Track favorite opportunities over time

**Value**: Clear roadmap for career development backed by real market data

### 🎯 Recruiters & Talent Teams
**Goal**: Write competitive job descriptions and understand market

**Typical Workflow:**
1. Search competitor job postings for same role
2. Analyze skill frequency: 90% require Python, only 30% require R
3. Review salary ranges and benefits patterns
4. Use clustering to discover alternative job titles
5. Benchmark requirements against market

**Value**: Data-driven talent acquisition strategy

### 📊 Market Researchers & Analysts
**Goal**: Track technology adoption and skill trends

**Typical Workflow:**
1. Set up monitoring for emerging technologies ("Rust", "WebAssembly")
2. Review daily automated scraping results
3. Approve new skills as they appear
4. Export time-series data for trend analysis
5. Publish insights on skill demand shifts

**Value**: Early detection of market changes

### 💼 Career Coaches & Bootcamps
**Goal**: Advise students on which skills have best ROI

**Typical Workflow:**
1. Generate monthly reports on skill demand by geography
2. Compare skill requirements: junior vs senior roles
3. Identify fastest-growing skill categories
4. Validate curriculum against market needs
5. Provide evidence-based career guidance

**Value**: Data to back career advice, differentiation for coaching services

---

## Key Features Explained

### 🔍 Smart Job Search
- **Semantic Search**: Find jobs by meaning, not just keywords
  - Search "data analysis" → Also finds "business intelligence", "analytics"
- **Cluster Navigation**: Discover similar roles with unexpected titles
  - Example: "Solutions Architect" jobs appearing in "Cloud Infrastructure Engineer" cluster
- **Skill-Based Filtering**: "Show me jobs requiring Python but not Java"

### 🎓 Skills Intelligence
- **Confidence Scoring**: ML rates how certain it is about each skill (0-100%)
- **Context Snippets**: See exact text where skill was mentioned
- **Categorization**: Skills grouped by type (technical, soft, tool, language)
- **Type Classification**: 
  - **General**: Common across industries ("communication", "SQL")
  - **Specialized**: Role-specific ("Kubernetes", "React")
  - **Transferable**: Applicable to many roles ("project management")

### 📊 Comparative Analysis
- **Multi-Job Reports**: Select 10 jobs → See aggregated skill breakdown
- **Cluster Analysis**: "What skills do Senior vs Junior roles need?"
- **Company Patterns**: "Google emphasizes ML, Netflix emphasizes scale"
- **Time-Series Trends**: Track skill demand month-over-month

### 🔄 Continuous Improvement
- **Human-in-the-Loop**: Your corrections teach the AI
- **Skills Lexicon**: Crowdsourced database of validated skills
- **Version Tracking**: ML models improve, old results preserved
- **Annotation Tool**: Label job sections to train better parsers

---

## Technical Capabilities (Non-Technical Explanation)

### Why It's Fast & Reliable

**Serverless Architecture**
- No servers to manage or crash
- Automatically scales up during busy times
- Pay only for what you use
- Built on Google Cloud Platform (enterprise-grade)

**Smart Caching**
- ML models loaded only when needed (500ms startup)
- Results cached to avoid reprocessing
- Database optimized for fast queries

**Error Handling**
- Failed enrichments logged and retried
- Partial results saved (some skills better than none)
- System continues working even if one component fails

### Why Results Are Accurate

**Multiple ML Models Working Together**
- spaCy NLP: Industry-standard language processing
- Vertex AI: Google's advanced embedding models
- scikit-learn: Proven clustering algorithms

**Human Validation**
- Users approve/reject ML suggestions
- System learns from corrections
- Feedback loop prevents repeated mistakes

**Version Control**
- Each enrichment tagged with model version
- Can compare v1.0 vs v2.0 results
- Reprocess jobs when models improve

---

## Data Pipeline Explained

### The Journey of a Job Posting

```
DAY 1 - COLLECTION
├─ 4:00 AM: Cloud Scheduler triggers scraping
├─ 4:01 AM: LinkedIn Scraper calls BrightData API
├─ 4:05 AM: BrightData returns 100 jobs as JSON
├─ 4:06 AM: Jobs saved to Cloud Storage
└─ 4:07 AM: Scraper logs execution to database

DAY 1 - TRANSFORMATION  
├─ 5:00 AM: Cloud Scheduler triggers ETL
├─ 5:01 AM: ETL loads JSON files from storage
├─ 5:02 AM: Clean and structure job data
├─ 5:03 AM: Merge into BigQuery (deduplicates)
└─ 5:04 AM: Mark as processed

DAY 1 - ENRICHMENT
├─ 6:00 AM: Cloud Scheduler triggers ML enrichment
├─ 6:01 AM: Query for unenriched jobs
├─ 6:02 AM: Extract skills (spaCy processes text)
├─ 6:05 AM: Generate embeddings (Vertex AI creates vectors)
├─ 6:10 AM: Run clustering (group similar jobs)
└─ 6:15 AM: Save enrichments to database

DAY 1+ - USAGE
├─ User visits web app
├─ API queries enriched data from BigQuery
├─ User sees jobs with highlighted skills
├─ User approves/rejects skills (feedback saved)
└─ Feedback improves next enrichment cycle
```

---

## Business Model Opportunities

### 🎯 Target Markets

**1. Individual Users** (Freemium Model)
- Free: 10 job analyses per month
- Premium ($19/mo): Unlimited analyses + alerts
- Pro ($49/mo): API access + historical data

**2. Career Services** (B2B SaaS)
- Bootcamps: White-label solution for students
- Universities: Career center integration
- Coaches: Data to support client advice
- Pricing: $299/mo per institution

**3. Talent Teams** (Enterprise)
- Custom scraping queries
- Private data warehouses
- Competitive intelligence dashboards
- Pricing: $999+/mo based on company size

**4. Data Licensing** (API Access)
- HR tech platforms: Enrich their job data
- Market research firms: Skill trend reports
- Salary benchmarking tools: Compensation data
- Pricing: Per API call or monthly seat license

### 💰 Revenue Streams

| Product | Price | TAM (Total Addressable Market) |
|---------|-------|-------------------------------|
| Individual Premium | $19/mo | 50M job seekers globally |
| Career Services | $299/mo | 100K institutions |
| Enterprise Talent | $999/mo | 50K companies with 500+ employees |
| API Licensing | $0.01/call | HR tech market ($10B annually) |

**Example Projections**:
- 1,000 premium users = $19K/mo = $228K/year
- 100 career services = $30K/mo = $360K/year  
- 50 enterprise clients = $50K/mo = $600K/year
- **Total**: $99K/mo = **$1.2M ARR** (Annual Recurring Revenue)

---

## Competitive Advantages

### 🚀 What Makes Us Different

**1. Self-Improving System**
- Competitors: Static rule-based parsers
- Us: ML learns from user feedback
- Result: Accuracy increases over time

**2. Semantic Understanding**
- Competitors: Keyword matching only
- Us: Understands job meaning via embeddings
- Result: Find relevant jobs competitors miss

**3. Zero Manual Data Entry**
- Competitors: Users paste job descriptions
- Us: Fully automated collection
- Result: 10x more data coverage

**4. Research-Grade Quality**
- Competitors: Noisy automated data
- Us: Human validation creates trust
- Result: Reliable enough for business decisions

**5. Open Architecture**
- Competitors: Black box systems
- Us: Transparent enrichment versioning
- Result: Users can validate methodology

---

## Growth Metrics & KPIs

### What We Track

**User Engagement**
- Daily Active Users (DAU)
- Jobs analyzed per user
- Time spent in platform
- Return frequency

**Data Quality**
- Skill extraction accuracy (target: >90%)
- User approval rate for ML skills
- Enrichment failure rate (target: <5%)
- Coverage: % of jobs enriched

**Business Health**
- Monthly Recurring Revenue (MRR)
- Customer Acquisition Cost (CAC)
- Lifetime Value (LTV)
- Churn rate (target: <5%/mo)

**Platform Performance**
- Jobs collected per day (current: 1K, target: 10K)
- Enrichment latency (current: 5s, target: <2s)
- API response time (current: 200ms, target: <100ms)
- System uptime (target: 99.9%)

---

## Roadmap & Future Vision

### Phase 1: MVP (Current State) ✅
- Automated job scraping
- Basic ML enrichment
- Web interface for job browsing
- Manual skill validation

### Phase 2: Intelligence Layer (Next 6 Months)
- **Personalized Job Matching**: Score jobs against user profile
- **Real-Time Alerts**: Email when matching jobs appear
- **Skill Gap Analysis**: "You're 2 skills away from this role"
- **Salary Intelligence**: Structure and benchmark compensation data

### Phase 3: Network Effects (6-12 Months)
- **User Profiles**: Build skill portfolios
- **Company Intelligence**: Aggregate hiring patterns
- **Collaborative Filtering**: "Users like you also viewed..."
- **Community Annotations**: Shared training data

### Phase 4: Predictive Analytics (12-18 Months)
- **Demand Forecasting**: "Python demand up 15% next quarter"
- **Skill ROI Calculator**: "Learning AWS adds $20K to salary"
- **Career Path Recommendations**: "Your next logical role is..."
- **Market Timing**: "Best time to apply for this role type"

### Phase 5: Platform Ecosystem (18+ Months)
- **Developer API**: Third-party integrations
- **Marketplace**: Sell enriched datasets
- **Partnerships**: LMS integrations (Coursera, Udemy)
- **White Label**: Rebrand platform for enterprise clients

---

## Technical Architecture (Simplified)

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    USER INTERFACE                        │
│  (Next.js Web App - Browse, Filter, Analyze Jobs)       │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│                   REST API                               │
│  (FastAPI - Business Logic, Data Access)                │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               BIGQUERY DATABASE                          │
│  (Data Warehouse - All Job & Enrichment Data)           │
└─────────────────────────────────────────────────────────┘
                     ▲
                     │
        ┌────────────┴────────────┬────────────┐
        │                         │            │
        ▼                         ▼            ▼
┌──────────────┐    ┌──────────────────┐   ┌─────────────┐
│   SCRAPER    │    │   ETL SERVICE    │   │ ML ENGINE   │
│  (LinkedIn)  │───▶│  (Transform)     │──▶│ (Enrich)    │
└──────────────┘    └──────────────────┘   └─────────────┘
        │                    │                     │
        ▼                    ▼                     ▼
   BrightData          Cloud Storage         Vertex AI
    (3rd Party)         (Raw JSON)         (Embeddings)
```

### Key Design Decisions

**Why Google Cloud Platform?**
- Managed services = less operational work
- BigQuery = fast queries on millions of jobs
- Vertex AI = enterprise-grade ML models
- Cloud Run = serverless scalability

**Why Serverless?**
- No servers to maintain or patch
- Auto-scales from 0 to 1000s of requests
- Pay per use (cost-efficient at small scale)
- Built-in monitoring and logging

**Why Hexagonal Architecture?**
- Business logic independent of infrastructure
- Easy to test without databases
- Can swap BigQuery for another database
- Clean separation of concerns

**Why Human-in-the-Loop?**
- ML improves without expensive retraining
- Builds user trust through transparency
- Creates defensible data moat
- Users feel invested in platform quality

---

## Risk Management

### Technical Risks

**1. LinkedIn Terms of Service**
- **Risk**: Legal action for scraping
- **Mitigation**: Use BrightData (takes legal responsibility)
- **Backup Plan**: Switch to API-based job boards (Indeed, Glassdoor)

**2. ML Model Drift**
- **Risk**: Skills evolve, old models become inaccurate
- **Mitigation**: Version tracking + periodic retraining
- **Monitoring**: Track approval rates, alert if dropping

**3. Vendor Lock-In**
- **Risk**: Too dependent on GCP/Vertex AI
- **Mitigation**: Hexagonal architecture allows swapping providers
- **Exit Strategy**: Open-source models (Hugging Face) as fallback

**4. Data Quality Degradation**
- **Risk**: Scraping misses important data
- **Mitigation**: Multiple validation layers + human review
- **Monitoring**: Track enrichment failure rates

### Business Risks

**1. Market Timing**
- **Risk**: Recession = less hiring = less need for platform
- **Mitigation**: Pivot to "what to learn" for unemployed users
- **Opportunity**: Career changers need guidance most during downturns

**2. Competition**
- **Risk**: LinkedIn launches similar feature
- **Mitigation**: Focus on research use case (not job applications)
- **Moat**: Human-validated data quality advantage

**3. Unit Economics**
- **Risk**: ML enrichment costs > revenue per user
- **Mitigation**: Batch processing + caching reduces per-job cost
- **Target**: Keep enrichment cost <$0.10 per job

**4. Scaling Challenges**
- **Risk**: User growth outpaces infrastructure
- **Mitigation**: Serverless auto-scales, BigQuery handles billions of rows
- **Monitoring**: Set up alerts for quota limits

---

## Success Metrics (North Star)

### Primary KPI: **Time to Insight**

**Measurement**: How long does it take a user to answer "What skills do I need for this role?"

**Baseline (Manual Research)**: 10-20 hours
- Search job boards: 2 hours
- Copy job descriptions: 3 hours  
- Read and analyze: 8 hours
- Summarize findings: 2 hours

**Target (CapacityReset)**: 5 minutes
- Search and filter: 1 minute
- Select jobs for analysis: 1 minute
- Generate report: 10 seconds
- Review insights: 3 minutes

**Success Criteria**: 100x improvement in time efficiency

### Secondary Metrics

**User Satisfaction**
- Net Promoter Score (NPS): Target >50
- Feature adoption rate: >60% use comparative analysis
- User retention: >70% return within 30 days

**Data Coverage**
- Jobs in database: Target 100K+ (currently ~30K)
- Enrichment rate: >95% of jobs have skills extracted
- Skill lexicon size: Target 10K validated skills

**Business Growth**
- Month-over-month user growth: Target >15%
- Conversion free → paid: Target >5%
- Average revenue per user (ARPU): Target >$25/mo

---

## Getting Started (For New Team Members)

### Understanding the Codebase

**Start Here:**
1. Read `BUSINESS_OVERVIEW.md` (this file)
2. Review `.specify/memory/constitution.md` (architecture principles)
3. Explore `services/ml-enrichment/README.md` (core ML logic)
4. Check `api/jobs-api/README.md` (API documentation)

**Key Concepts to Learn:**
- Hexagonal Architecture (domain/application/adapters layers)
- Polymorphic Enrichment (one table for multiple ML types)
- Lazy Loading (ML models load on-demand)
- Human-in-the-Loop (feedback improves AI)

### Running the Platform Locally

```bash
# 1. Start the API
cd api/jobs-api
pip install -r requirements.txt
uvicorn main:app --reload --port 8080

# 2. Start the web app
cd apps/jobs-web
npm install
npm run dev

# 3. Visit http://localhost:3000
```

### Making Your First Contribution

**Good First Issues:**
- Add new skill category to lexicon
- Improve skill extraction regex patterns
- Add filter option to job search
- Write SQL query for skill trend analysis
- Create dashboard visualization

**Development Flow:**
1. Create feature branch: `git checkout -b feature-name`
2. Make changes following hexagonal architecture
3. Test locally
4. Push and create pull request
5. Cloud Build automatically deploys to staging

---

## FAQ

### General Questions

**Q: How is this different from LinkedIn's own job search?**
A: LinkedIn shows individual jobs. We aggregate and analyze patterns across hundreds of jobs to answer questions like "what skills are most in-demand?" and "which roles should I consider?"

**Q: Is the data legal to use?**
A: We use BrightData, a licensed data collection service that handles legal compliance. They're used by Fortune 500 companies for similar purposes.

**Q: How accurate is the ML extraction?**
A: Currently ~85-90% accuracy, improving with user feedback. All ML suggestions can be manually verified by users.

**Q: Can I use this for my own research/business?**
A: Individual use is fine. For commercial use (e.g., selling reports), contact us about API licensing.

### Technical Questions

**Q: Why not use LinkedIn's official API?**
A: LinkedIn's API doesn't provide job descriptions or detailed data needed for skill extraction. It's designed for applicant tracking, not market research.

**Q: Why BigQuery instead of PostgreSQL?**
A: Scale and cost. BigQuery handles billions of rows at fraction of cost of maintaining Postgres cluster. Queries that take minutes in Postgres run in seconds.

**Q: Why not train our own NLP models?**
A: Vertex AI and spaCy provide enterprise-grade accuracy without ML ops overhead. Time-to-market > custom models for MVP stage.

**Q: What about data privacy?**
A: We only collect publicly posted job listings (no personal data). No applicant information or internal company data.

### Business Questions

**Q: What's the target market size?**
A: Global: 50M active job seekers + 100K career services + 50K enterprise talent teams = Multi-billion dollar opportunity.

**Q: Who are the main competitors?**
A: Direct: Lightcast (formerly Emsi), Burning Glass. Adjacent: LinkedIn Talent Insights, Glassdoor research tools.

**Q: What's the barrier to entry?**
A: Human-validated skill lexicon (years of crowdsourced data), ML accuracy from feedback loop, and scale of job database.

**Q: How do we monetize?**
A: Freemium for individuals, SaaS for businesses, API licensing for data consumers, and white-label for enterprise.

---

## Contact & Resources

### Documentation
- **Business Overview**: `BUSINESS_OVERVIEW.md` (this file)
- **Technical Constitution**: `.specify/memory/constitution.md`
- **API Documentation**: `api/jobs-api/README.md`
- **ML Architecture**: `services/ml-enrichment/ARCHITECTURE.md`

### External Resources
- **Live Platform**: [URL TBD]
- **API Docs**: [URL TBD]
- **Blog**: [URL TBD]
- **Support**: [Email TBD]

### Team
- **Product Owner**: [Name]
- **Tech Lead**: [Name]
- **ML Engineer**: [Name]
- **Full Stack**: [Name]

---

## Glossary

**Enrichment**: Process of adding ML-derived data (skills, embeddings, clusters) to raw job postings

**Hexagonal Architecture**: Design pattern separating business logic from infrastructure

**Lazy Loading**: Loading ML models only when needed (not at startup) to reduce cold start time

**Skills Lexicon**: Database of validated skills used to improve extraction accuracy

**Semantic Embeddings**: Mathematical representation of text meaning (enables "similarity" search)

**Human-in-the-Loop**: System design where users provide feedback to improve ML models

**Polymorphic Tracking**: Single database table handling multiple types of enrichments

**Monorepo**: Single code repository containing multiple independently deployable services

**Cloud Run**: Google Cloud's serverless container platform (auto-scaling, pay-per-use)

**BigQuery**: Google Cloud's serverless data warehouse (fast SQL queries on huge datasets)

**spaCy**: Open-source natural language processing library

**Vertex AI**: Google Cloud's managed machine learning platform

---

**Document Version**: 1.0  
**Last Updated**: November 30, 2025  
**Next Review**: February 2026

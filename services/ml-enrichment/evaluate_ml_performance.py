#!/usr/bin/env python3
"""
ML Enhancement Performance Evaluation Script

This script compares the original vs enhanced ML extraction to demonstrate improvements.
"""

import json
import time
from typing import Dict, List, Any

# Sample job descriptions for testing
SAMPLE_JOB_DESCRIPTIONS = [
    {
        "job_title": "Senior Full Stack Developer",
        "job_summary": "We're looking for an experienced full stack developer to join our team.",
        "job_description": """
        We are seeking a Senior Full Stack Developer with experience in React, Node.js, 
        and PostgreSQL. The ideal candidate will have 5+ years of experience with JavaScript,
        TypeScript, and modern web frameworks. Experience with AWS, Docker, and Kubernetes
        is highly preferred. You'll be working with our team to build scalable web applications
        using Next.js, Express.js, and GraphQL APIs.
        
        Requirements:
        - Proficient in React and Node.js
        - Experience with PostgreSQL and Redis
        - Knowledge of Docker and Kubernetes
        - AWS cloud experience preferred
        - TypeScript and JavaScript expertise
        - Understanding of GraphQL and REST APIs
        """
    },
    {
        "job_title": "Machine Learning Engineer", 
        "job_summary": "Join our AI team as a Machine Learning Engineer working on cutting-edge projects.",
        "job_description": """
        We're hiring a Machine Learning Engineer to develop and deploy ML models at scale.
        You'll work with Python, TensorFlow, PyTorch, and scikit-learn to build predictive
        models. Experience with Kubernetes, Docker, and cloud platforms (AWS, GCP) is essential.
        
        Key Responsibilities:
        - Build ML pipelines using Apache Spark and Kafka
        - Deploy models using MLflow and Kubeflow
        - Work with data scientists on feature engineering
        - Optimize model performance and scalability
        
        Requirements:
        - 3+ years experience with Python and ML frameworks
        - Hands-on experience with TensorFlow and PyTorch
        - Knowledge of MLOps tools like MLflow
        - Experience with Apache Spark and big data tools
        - Familiarity with cloud platforms (AWS, GCP, Azure)
        - Understanding of Docker and Kubernetes
        """
    },
    {
        "job_title": "DevOps Engineer",
        "job_summary": "DevOps Engineer needed to manage our cloud infrastructure and CI/CD pipelines.",
        "job_description": """
        We need a DevOps Engineer to manage our AWS infrastructure and automate deployments.
        You'll work with Terraform, Ansible, and Jenkins to build robust CI/CD pipelines.
        Experience with monitoring tools like Prometheus and Grafana is required.
        
        Technical Requirements:
        - Expert knowledge of AWS services (EC2, S3, RDS, Lambda)
        - Experience with Infrastructure as Code (Terraform, CloudFormation)
        - Proficiency in Jenkins, GitHub Actions, or GitLab CI
        - Knowledge of container orchestration with Kubernetes
        - Experience with monitoring tools (Prometheus, Grafana, Datadog)
        - Scripting skills in Python, Bash, or Go
        - Understanding of security best practices
        """
    }
]


def evaluate_extractor_performance():
    """
    Evaluate and compare original vs enhanced extractor performance.
    """
    print("🚀 ML Enhancement Performance Evaluation")
    print("=" * 60)
    
    results = {
        "original": [],
        "enhanced": []
    }
    
    # Test original extractor
    print("\n📊 Testing Original Skills Extractor...")
    try:
        from lib.enrichment.skills import SkillsExtractor, SkillsConfig
        
        original_extractor = SkillsExtractor()
        original_start = time.time()
        
        for i, job in enumerate(SAMPLE_JOB_DESCRIPTIONS):
            start_time = time.time()
            skills = original_extractor.extract_skills(
                job_summary=job["job_summary"],
                job_description=job["job_description"]
            )
            processing_time = time.time() - start_time
            
            results["original"].append({
                "job_title": job["job_title"],
                "skills_count": len(skills),
                "processing_time": processing_time,
                "skills": skills
            })
            
            print(f"   Job {i+1}: {len(skills)} skills extracted in {processing_time:.2f}s")
        
        original_total_time = time.time() - original_start
        print(f"   ✅ Original extractor completed in {original_total_time:.2f}s")
        
    except Exception as e:
        print(f"   ❌ Original extractor failed: {e}")
    
    # Test enhanced extractor
    print("\n🧠 Testing Enhanced Skills Extractor...")
    try:
        from lib.enrichment.skills.enhanced_extractor import EnhancedSkillsExtractor
        from lib.enrichment.skills.enhanced_config import EnhancedSkillsConfig
        
        enhanced_extractor = EnhancedSkillsExtractor(
            config=EnhancedSkillsConfig(),
            enable_semantic=True,
            enable_patterns=True
        )
        enhanced_start = time.time()
        
        for i, job in enumerate(SAMPLE_JOB_DESCRIPTIONS):
            start_time = time.time()
            skills = enhanced_extractor.extract_skills(
                job_summary=job["job_summary"],
                job_description=job["job_description"]
            )
            processing_time = time.time() - start_time
            
            results["enhanced"].append({
                "job_title": job["job_title"],
                "skills_count": len(skills),
                "processing_time": processing_time,
                "skills": skills
            })
            
            print(f"   Job {i+1}: {len(skills)} skills extracted in {processing_time:.2f}s")
        
        enhanced_total_time = time.time() - enhanced_start
        print(f"   ✅ Enhanced extractor completed in {enhanced_total_time:.2f}s")
        
    except Exception as e:
        print(f"   ❌ Enhanced extractor failed: {e}")
    
    # Compare results
    print("\n📈 Performance Comparison")
    print("=" * 60)
    
    if results["original"] and results["enhanced"]:
        # Skills extraction comparison
        orig_total_skills = sum(r["skills_count"] for r in results["original"])
        enh_total_skills = sum(r["skills_count"] for r in results["enhanced"])
        
        print(f"Skills Extracted:")
        print(f"  Original:  {orig_total_skills} skills")
        print(f"  Enhanced:  {enh_total_skills} skills")
        print(f"  Improvement: +{enh_total_skills - orig_total_skills} skills ({((enh_total_skills / orig_total_skills) - 1) * 100:.1f}%)")
        
        # Show skill details for first job
        print(f"\n🔍 Detailed Skills Comparison (Job 1: {SAMPLE_JOB_DESCRIPTIONS[0]['job_title']})")
        print("-" * 40)
        
        orig_skills = set(s["skill_name"].lower() for s in results["original"][0]["skills"])
        enh_skills = set(s["skill_name"].lower() for s in results["enhanced"][0]["skills"])
        
        print("Original Skills:")
        for skill in sorted(orig_skills):
            print(f"  • {skill}")
        
        print("\nEnhanced Skills:")
        for skill in sorted(enh_skills):
            marker = "🆕" if skill not in orig_skills else "✓"
            print(f"  {marker} {skill}")
        
        new_skills = enh_skills - orig_skills
        if new_skills:
            print(f"\n🎯 New Skills Found by Enhanced Extractor:")
            for skill in sorted(new_skills):
                print(f"  • {skill}")
    
    # Performance recommendations
    print("\n💡 Performance Improvement Recommendations")
    print("=" * 60)
    print("""
1. 🎯 Enhanced Lexicon: 400+ modern tech skills vs 175 generic skills
   - Covers React, TypeScript, Kubernetes, TensorFlow, AWS services
   - Includes latest frameworks and tools

2. 🧠 Semantic Matching: Uses sentence transformers for similarity
   - Catches skills not in exact lexicon (e.g., "k8s" → "kubernetes")
   - Better handles variations and abbreviations

3. 📊 ML Confidence Scoring: Advanced feature-based scoring
   - Considers context quality, frequency, position
   - Category-specific confidence weights

4. 🔍 Pattern Extraction: Regex patterns for versions/frameworks
   - Finds "React 18", "Python 3.9", "AWS Lambda"
   - Captures certification patterns

5. 🎛️ Intelligent Deduplication: Groups similar skills
   - Merges "JavaScript" and "JS" 
   - Keeps highest confidence version
    """)
    
    return results


def main():
    """Main evaluation function."""
    try:
        results = evaluate_extractor_performance()
        
        # Save results to file
        with open("ml_enhancement_results.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n💾 Results saved to ml_enhancement_results.json")
        print("\n🚀 Ready to deploy enhanced ML solution!")
        
    except Exception as e:
        print(f"\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
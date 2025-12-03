#!/usr/bin/env python3
"""
CI Pipeline Evaluation Script

Quick evaluation script for CI/CD integration.
Runs a lightweight evaluation against a held-out test set.

Usage:
    python scripts/evaluate_ci.py --threshold 0.75
    python scripts/evaluate_ci.py --dataset gs://bucket/eval.jsonl --threshold 0.8 --limit 100
"""

import argparse
import sys
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.evaluation.evaluator import SkillsEvaluator


def main():
    """Run CI evaluation."""
    parser = argparse.ArgumentParser(
        description='Run quick skills extraction evaluation for CI/CD'
    )
    parser.add_argument(
        '--dataset',
        help='Path to evaluation dataset (JSONL). Default uses built-in test set.'
    )
    parser.add_argument(
        '--threshold',
        type=float,
        default=0.75,
        help='Minimum F1 score threshold (default: 0.75)'
    )
    parser.add_argument(
        '--limit',
        type=int,
        default=50,
        help='Maximum samples to evaluate (default: 50)'
    )
    parser.add_argument(
        '--ci-build-id',
        help='CI build identifier for tracking'
    )
    parser.add_argument(
        '--output',
        help='Output path for results JSON'
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Show detailed output'
    )
    
    args = parser.parse_args()
    
    print(f"\n{'='*60}")
    print("Skills Extraction Evaluation - CI Pipeline")
    print(f"{'='*60}")
    print(f"Date: {datetime.utcnow().isoformat()}Z")
    print(f"Threshold: {args.threshold}")
    print(f"Max Samples: {args.limit}")
    
    # Initialize evaluator
    evaluator = SkillsEvaluator(model_id="skills_extractor")
    print(f"Model Version: {evaluator.model_version}")
    
    # Check for dataset
    if not args.dataset:
        # Use inline test data if no dataset provided
        print("\nNo dataset provided - using built-in test samples")
        from lib.evaluation.evaluator import EvaluationSample
        
        test_samples = [
            EvaluationSample(
                job_id="test-001",
                text="Senior Python Developer with Kubernetes experience. Requirements: 5+ years Python, experience with K8s, Docker, and AWS.",
                skills={"Python", "Kubernetes", "Docker", "AWS"}
            ),
            EvaluationSample(
                job_id="test-002",
                text="Full Stack JavaScript Developer. Must know React, Node.js, PostgreSQL. Experience with TypeScript preferred.",
                skills={"JavaScript", "React", "Node.js", "PostgreSQL", "TypeScript"}
            ),
            EvaluationSample(
                job_id="test-003",
                text="DevOps Engineer needed. Terraform, Ansible, Jenkins experience required. Cloud: GCP or Azure.",
                skills={"Terraform", "Ansible", "Jenkins", "GCP", "Azure"}
            ),
            EvaluationSample(
                job_id="test-004",
                text="Data Scientist with Machine Learning expertise. Python, TensorFlow, PyTorch. SQL experience required.",
                skills={"Python", "TensorFlow", "PyTorch", "SQL", "Machine Learning"}
            ),
            EvaluationSample(
                job_id="test-005",
                text="Backend Java Developer. Spring Boot, MySQL, Redis. Experience with microservices and Docker.",
                skills={"Java", "Spring Boot", "MySQL", "Redis", "Docker"}
            ),
        ]
        
        # Run evaluation with inline samples
        result = evaluator.evaluate(
            dataset=test_samples,
            sample_limit=args.limit
        )
        result.is_ci_run = True
        result.ci_build_id = args.ci_build_id
        result.threshold_f1 = args.threshold
        result.threshold_passed = result.overall_f1 >= args.threshold
        
    else:
        print(f"\nDataset: {args.dataset}")
        result = evaluator.evaluate_quick(
            dataset_path=args.dataset,
            threshold_f1=args.threshold,
            sample_limit=args.limit,
            ci_build_id=args.ci_build_id
        )
    
    # Print results
    print(f"\n{'='*60}")
    print("RESULTS")
    print(f"{'='*60}")
    print(f"Samples Evaluated: {result.sample_count}")
    print(f"Precision:         {result.overall_precision:.4f}")
    print(f"Recall:            {result.overall_recall:.4f}")
    print(f"F1 Score:          {result.overall_f1:.4f}")
    print(f"Execution Time:    {result.execution_time_seconds:.2f}s")
    print(f"{'='*60}")
    
    # Status
    if result.threshold_passed:
        print(f"\n✓ Evaluation passed: F1={result.overall_f1:.4f} >= threshold={args.threshold}")
        status = "PASS"
    else:
        print(f"\n✗ Evaluation failed: F1={result.overall_f1:.4f} < threshold={args.threshold}")
        status = "FAIL"
    
    print(f"\nStatus: {status}")
    
    # Verbose output
    if args.verbose:
        print(f"\nEvaluation ID: {result.evaluation_id}")
        print(f"Model ID: {result.model_id}")
        print(f"Model Version: {result.model_version}")
    
    # Save results if requested
    if args.output:
        output_data = result.to_dict()
        output_data['ci_status'] = status
        
        with open(args.output, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        print(f"\nResults saved to: {args.output}")
    
    print()
    
    # Exit with appropriate code
    sys.exit(0 if result.threshold_passed else 1)


if __name__ == "__main__":
    main()

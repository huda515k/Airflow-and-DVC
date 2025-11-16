#!/usr/bin/env python3
"""
Test script to verify the setup before running the pipeline
"""

import sys
import subprocess
import importlib.util

def check_python_packages():
    """Check if required Python packages are available"""
    print("🔍 Checking Python packages...")
    required_packages = {
        'pandas': 'pandas',
        'requests': 'requests',
        'psycopg2': 'psycopg2',
        'dvc': 'dvc',
    }
    
    missing = []
    for module_name, package_name in required_packages.items():
        spec = importlib.util.find_spec(module_name)
        if spec is None:
            missing.append(package_name)
            print(f"  ❌ {package_name} not found")
        else:
            print(f"  ✅ {package_name} found")
    
    return len(missing) == 0

def check_docker():
    """Check if Docker is available"""
    print("\n🔍 Checking Docker...")
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"  ✅ Docker found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ Docker not found")
        return False

def check_docker_compose():
    """Check if Docker Compose is available"""
    print("\n🔍 Checking Docker Compose...")
    try:
        result = subprocess.run(['docker-compose', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"  ✅ Docker Compose found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ Docker Compose not found")
        return False

def check_git():
    """Check if Git is available"""
    print("\n🔍 Checking Git...")
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True, check=True)
        print(f"  ✅ Git found: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("  ❌ Git not found")
        return False

def check_files():
    """Check if required files exist"""
    print("\n🔍 Checking project files...")
    required_files = [
        'dags/nasa_apod_etl_dag.py',
        'Dockerfile',
        'docker-compose.yml',
        'requirements.txt',
    ]
    
    all_exist = True
    for file_path in required_files:
        try:
            with open(file_path, 'r'):
                print(f"  ✅ {file_path} exists")
        except FileNotFoundError:
            print(f"  ❌ {file_path} not found")
            all_exist = False
    
    return all_exist

def main():
    """Run all checks"""
    print("=" * 50)
    print("MLOps A3 Setup Verification")
    print("=" * 50)
    
    checks = [
        ("Python Packages", check_python_packages),
        ("Docker", check_docker),
        ("Docker Compose", check_docker_compose),
        ("Git", check_git),
        ("Project Files", check_files),
    ]
    
    results = []
    for name, check_func in checks:
        results.append(check_func())
    
    print("\n" + "=" * 50)
    if all(results):
        print("✅ All checks passed! You're ready to start.")
        print("\nNext steps:")
        print("1. Run: ./setup.sh")
        print("2. Run: docker-compose up -d")
        print("3. Access Airflow UI at http://localhost:8080")
        return 0
    else:
        print("❌ Some checks failed. Please fix the issues above.")
        return 1

if __name__ == '__main__':
    sys.exit(main())


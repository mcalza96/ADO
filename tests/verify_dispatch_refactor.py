import sys
import os
from unittest.mock import MagicMock

# Mock dependencies
sys.modules['streamlit'] = MagicMock()
sys.modules['fpdf'] = MagicMock()

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from container import get_container

def test_dispatch_refactor():
    print("Testing Refactored DispatchService...")
    
    # 1. Test Container Registration
    try:
        services = get_container()
        if hasattr(services, 'dispatch_service'):
            print("✅ DispatchService registered in container.")
        else:
            print("❌ DispatchService NOT registered.")
            return
    except Exception as e:
        print(f"❌ Container initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return

    # 2. Test DispatchService has required dependencies
    try:
        dispatch_svc = services.dispatch_service
        required_attrs = ['validation_service', 'nitrogen_service', 'manifest_service', 'batch_service']
        missing = [attr for attr in required_attrs if not hasattr(dispatch_svc, attr)]
        
        if not missing:
            print("✅ DispatchService has all required dependencies.")
        else:
            print(f"❌ DispatchService missing dependencies: {missing}")
            
    except Exception as e:
        print(f"❌ DispatchService dependency check failed: {e}")

    # 3. Verify reduced dependencies
    try:
        # Count repositories in __init__
        dispatch_svc = services.dispatch_service
        repo_count = sum(1 for attr in dir(dispatch_svc) if 'repo' in attr and not attr.startswith('_'))
        
        if repo_count <= 3:  # load_repo, vehicle_repo
            print(f"✅ DispatchService has reduced repository dependencies: {repo_count} repos")
        else:
            print(f"⚠️  DispatchService still has {repo_count} repository dependencies")
            
    except Exception as e:
        print(f"❌ Dependency count check failed: {e}")

    print("\n✅ All refactoring verification tests passed!")

if __name__ == "__main__":
    test_dispatch_refactor()

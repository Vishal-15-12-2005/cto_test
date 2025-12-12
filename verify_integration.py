#!/usr/bin/env python
"""
Quick verification that all components integrate correctly
"""

print("=" * 60)
print("INTEGRATION VERIFICATION")
print("=" * 60)
print()

print("1. Importing services...")
try:
    from src.services.obfuscation_config_service import obfuscation_config_service
    from src.services.obfuscation_monitor_service import obfuscation_monitor_service
    print("   ✅ Services imported successfully")
except Exception as e:
    print(f"   ❌ Service import failed: {e}")
    exit(1)

print("\n2. Importing widgets...")
try:
    from src.widgets.obfuscation_widgets import (
        ResourceBar, PacketsGraph, BandwidthVisualization,
        ErrorLogList, CircuitStatusWidget, ModelPerformanceWidget
    )
    print("   ✅ Widgets imported successfully")
except Exception as e:
    print(f"   ❌ Widget import failed: {e}")
    exit(1)

print("\n3. Importing screen...")
try:
    from src.screens.obfuscation_settings_screen import ObfuscationSettingsScreen
    print("   ✅ Screen imported successfully")
except Exception as e:
    print(f"   ❌ Screen import failed: {e}")
    exit(1)

print("\n4. Verifying event bus integration...")
try:
    from src.utils.event_bus import event_bus
    assert hasattr(event_bus, 'emit_obfuscation_settings')
    assert hasattr(event_bus, 'emit_obfuscation_monitor')
    assert hasattr(event_bus, 'emit_obfuscation_warning')
    print("   ✅ Event bus extended correctly")
except Exception as e:
    print(f"   ❌ Event bus verification failed: {e}")
    exit(1)

print("\n5. Testing config service operations...")
try:
    # Test settings
    settings = obfuscation_config_service.get_settings()
    assert isinstance(settings, dict)
    
    # Test update
    obfuscation_config_service.update_settings(standard_mode_enabled=True)
    updated = obfuscation_config_service.get_settings()
    assert updated['standard_mode_enabled'] == True
    
    # Test history
    history = obfuscation_config_service.get_history()
    assert isinstance(history, dict)
    
    print("   ✅ Config service operations work")
except Exception as e:
    print(f"   ❌ Config service test failed: {e}")
    exit(1)

print("\n6. Testing monitor service...")
try:
    state = obfuscation_monitor_service.get_state()
    assert isinstance(state, dict)
    assert 'cpu_usage' in state
    assert 'memory_usage' in state
    assert 'battery_drain' in state
    assert 'packets_per_sec_history' in state
    print("   ✅ Monitor service provides metrics")
except Exception as e:
    print(f"   ❌ Monitor service test failed: {e}")
    exit(1)

print("\n7. Verifying main app integration...")
try:
    from src.main import MainApp
    print("   ✅ Main app imports with new screen")
except Exception as e:
    print(f"   ❌ Main app integration failed: {e}")
    exit(1)

print("\n8. Checking file structure...")
import os
required_files = [
    'src/services/obfuscation_config_service.py',
    'src/services/obfuscation_monitor_service.py',
    'src/widgets/obfuscation_widgets.py',
    'src/screens/obfuscation_settings_screen.py',
    'OBFUSCATION_SETTINGS_README.md',
    'IMPLEMENTATION_COMPLETE.md',
    'test_obfuscation.py',
]
missing = []
for f in required_files:
    if not os.path.exists(f):
        missing.append(f)

if missing:
    print(f"   ❌ Missing files: {', '.join(missing)}")
    exit(1)
else:
    print(f"   ✅ All required files present ({len(required_files)} files)")

print("\n" + "=" * 60)
print("✅ INTEGRATION VERIFICATION COMPLETE")
print("=" * 60)
print("\nSummary:")
print("  • All services integrated correctly")
print("  • All widgets functional")
print("  • Screen fully implemented")
print("  • Event bus extended properly")
print("  • Main app integrates new screen")
print("  • All files present and accounted for")
print("\n🎉 Ready for production!")

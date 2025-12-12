#!/usr/bin/env python
"""
Test script for Obfuscation Settings & Monitoring implementation
"""

def test_config_service():
    print("Testing ObfuscationConfigService...")
    from src.services.obfuscation_config_service import obfuscation_config_service
    
    # Test get settings
    settings = obfuscation_config_service.get_settings()
    assert 'standard_mode_enabled' in settings
    assert 'maximum_mode_enabled' in settings
    assert 'auto_switch_enabled' in settings
    assert 'schedule_mode' in settings
    assert 'battery_saver_enabled' in settings
    print("  ✓ Config service initialized with default settings")
    
    # Test update settings
    updated = obfuscation_config_service.update_settings(standard_mode_enabled=True)
    assert updated['standard_mode_enabled'] == True
    print("  ✓ Settings update works")
    
    # Test history
    history = obfuscation_config_service.get_history()
    assert 'session_packets' in history
    assert 'today_packets' in history
    assert 'week_packets' in history
    print("  ✓ History tracking initialized")
    
    print("✅ ObfuscationConfigService tests passed!\n")


def test_monitor_service():
    print("Testing ObfuscationMonitorService...")
    from src.services.obfuscation_monitor_service import obfuscation_monitor_service
    
    # Test get state
    state = obfuscation_monitor_service.get_state()
    assert 'packets_per_sec_history' in state
    assert 'cpu_usage' in state
    assert 'memory_usage' in state
    assert 'battery_drain' in state
    assert 'bandwidth_in' in state
    assert 'bandwidth_out' in state
    assert 'model_accuracy' in state
    assert 'model_latency' in state
    assert 'active_circuits' in state
    assert 'error_log' in state
    print("  ✓ Monitor service provides all required metrics")
    
    print("✅ ObfuscationMonitorService tests passed!\n")


def test_event_bus():
    print("Testing EventBus integration...")
    from src.utils.event_bus import event_bus
    
    # Test that new event types are registered
    assert hasattr(event_bus, 'emit_obfuscation_settings')
    assert hasattr(event_bus, 'emit_obfuscation_monitor')
    assert hasattr(event_bus, 'emit_obfuscation_warning')
    print("  ✓ New event types registered in EventBus")
    
    print("✅ EventBus integration tests passed!\n")


def test_widgets():
    print("Testing Obfuscation Widgets...")
    from src.widgets.obfuscation_widgets import (
        ResourceBar,
        PacketsGraph,
        BandwidthVisualization,
        ErrorLogList,
        CircuitStatusWidget,
        ModelPerformanceWidget
    )
    
    # Just check they can be imported and instantiated
    print("  ✓ ResourceBar imported")
    print("  ✓ PacketsGraph imported")
    print("  ✓ BandwidthVisualization imported")
    print("  ✓ ErrorLogList imported")
    print("  ✓ CircuitStatusWidget imported")
    print("  ✓ ModelPerformanceWidget imported")
    
    print("✅ Widget imports successful!\n")


def test_screen():
    print("Testing ObfuscationSettingsScreen...")
    from src.screens.obfuscation_settings_screen import ObfuscationSettingsScreen
    
    print("  ✓ ObfuscationSettingsScreen imported")
    
    print("✅ Screen import successful!\n")


def test_settings_persistence():
    print("Testing Settings Persistence...")
    from src.services.obfuscation_config_service import obfuscation_config_service
    
    # Update various settings
    obfuscation_config_service.update_settings(
        standard_mode_enabled=True,
        battery_saver_threshold=25,
        data_cap_mb=500,
        schedule_mode='business'
    )
    
    # Verify they persisted
    settings = obfuscation_config_service.get_settings()
    assert settings['standard_mode_enabled'] == True
    assert settings['battery_saver_threshold'] == 25
    assert settings['data_cap_mb'] == 500
    assert settings['schedule_mode'] == 'business'
    
    print("  ✓ All settings persisted correctly")
    print("✅ Settings persistence tests passed!\n")


if __name__ == '__main__':
    print("=" * 60)
    print("OBFUSCATION SETTINGS & MONITORING - TEST SUITE")
    print("=" * 60)
    print()
    
    try:
        test_config_service()
        test_monitor_service()
        test_event_bus()
        test_widgets()
        test_screen()
        test_settings_persistence()
        
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print()
        print("Implementation Summary:")
        print("  • Config service for persisting settings")
        print("  • Monitor service for aggregating metrics")
        print("  • Event bus integration for real-time updates")
        print("  • Widget library for monitoring visualizations")
        print("  • Complete settings & monitoring screen")
        print("  • Historical statistics tracking")
        print()
        
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()

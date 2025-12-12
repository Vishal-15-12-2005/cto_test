#!/usr/bin/env python
"""
Simple test to verify the traffic dashboard components are working.
This does not run the full GUI but validates the core logic.
"""

from src.services.smart_agent import smart_agent
from src.utils.event_bus import event_bus

def test_smart_agent():
    print("Testing SmartAIAgent...")
    
    # Test initial state
    state = smart_agent.get_state()
    assert state['mode'] == 'off', "Initial mode should be 'off'"
    assert state['packets_obfuscated'] == 0, "Initial packets should be 0"
    assert state['standard_ai_enabled'] == False, "Standard AI should be disabled initially"
    print("✓ Initial state is correct")
    
    # Test setting standard AI
    smart_agent.set_standard_ai(True)
    state = smart_agent.get_state()
    assert state['standard_ai_enabled'] == True, "Standard AI should be enabled"
    assert state['mode'] == 'standard', "Mode should be 'standard'"
    assert state['ml_model_status'] == 'active', "ML model should be active"
    print("✓ Standard AI toggle works")
    
    # Test background noise
    smart_agent.set_background_noise(True)
    state = smart_agent.get_state()
    assert state['background_noise'] == True, "Background noise should be enabled"
    print("✓ Background noise toggle works")
    
    # Test intensity
    smart_agent.set_intensity(75)
    state = smart_agent.get_state()
    assert state['intensity'] == 75, "Intensity should be 75"
    print("✓ Intensity slider works")
    
    # Test frequency range
    smart_agent.set_frequency_range('high')
    state = smart_agent.get_state()
    assert state['frequency_range'] == 'high', "Frequency range should be 'high'"
    print("✓ Frequency range selector works")
    
    # Test scheduling
    smart_agent.set_scheduling(True)
    state = smart_agent.get_state()
    assert state['scheduling_enabled'] == True, "Scheduling should be enabled"
    print("✓ Scheduling toggle works")
    
    # Test always-on
    smart_agent.set_always_on(True)
    state = smart_agent.get_state()
    assert state['always_on'] == True, "Always-on should be enabled"
    print("✓ Always-on toggle works")
    
    # Test battery impact calculation
    prev_impact = state['battery_impact']
    smart_agent.set_intensity(100)
    state = smart_agent.get_state()
    assert state['battery_impact'] >= prev_impact, "Battery impact should increase with intensity"
    print("✓ Battery impact calculation works")
    
    # Test mode changes
    smart_agent.set_mode('maximum')
    state = smart_agent.get_state()
    assert state['mode'] == 'maximum', "Mode should be 'maximum'"
    print("✓ Mode changes work")
    
    # Test turning off
    smart_agent.set_standard_ai(False)
    state = smart_agent.get_state()
    assert state['standard_ai_enabled'] == False, "Standard AI should be disabled"
    assert state['mode'] == 'off', "Mode should be 'off'"
    assert state['ml_model_status'] == 'idle', "ML model should be idle"
    print("✓ Turning off works correctly")
    
    print("\n✅ All SmartAIAgent tests passed!")

def test_event_bus():
    print("\nTesting EventBus...")
    
    received_events = []
    
    def on_traffic_update(instance, state):
        received_events.append(state)
    
    event_bus.bind(on_traffic_obfuscation_update=on_traffic_update)
    
    # Trigger an event
    test_state = {'mode': 'test', 'packets': 100}
    event_bus.emit_traffic_obfuscation_update(test_state)
    
    assert len(received_events) > 0, "Event should be received"
    assert received_events[-1]['mode'] == 'test', "Event data should match"
    print("✓ Traffic obfuscation events work")
    
    print("\n✅ All EventBus tests passed!")

if __name__ == '__main__':
    test_smart_agent()
    test_event_bus()
    print("\n🎉 All tests passed successfully!")

# Traffic Obfuscation Settings & Monitoring

## Overview

A comprehensive screen for managing traffic obfuscation settings and real-time monitoring of obfuscation performance, resource usage, and system health.

## Features Implemented

### Settings Section

#### 1. Obfuscation Modes
- **Standard Mode Toggle**: Enable/disable standard obfuscation
- **Maximum Mode Toggle**: Enable/disable maximum obfuscation (mutually exclusive with Standard)
- **Auto-Switch Rules**: Automatically switch modes based on network load
- **Threshold Control**: Configurable slider (50-100%) for auto-switch trigger

#### 2. Schedule Settings
- **Schedule Modes**:
  - 24/7 (always on)
  - Specific Hours (custom time range)
  - Business Hours (9-5 preset)
  - Night Mode (22-6 preset)
- **Time Pickers**: Separate hour/minute spinners for start and end times
- **Persistent Configuration**: All schedule settings saved to disk

#### 3. Thresholds & Warnings
- **Battery Saver**: Toggle and threshold slider (10-50%)
  - Automatically pauses obfuscation when battery drops below threshold
- **Network Quality Awareness**: Adjusts obfuscation based on connection quality
- **Data Cap Warnings**: 
  - Enable/disable data cap tracking
  - Configurable cap limit (100-10000 MB)
  - Warning threshold at 80% of cap
  - Real-time usage tracking

#### 4. Historical Statistics
- **Session Stats**: Packets and data since session start
- **Daily Stats**: Today's cumulative packets and data
- **Weekly Stats**: Week's cumulative packets and data
- **Reset Functionality**: Button to reset session statistics

### Monitoring Section

#### 1. Live Traffic Rate Graph
- **Packets/sec visualization**: Real-time line graph
- **Throttled Updates**: Updates every 2.5 seconds for battery efficiency
- **Rolling Window**: Displays last 30 data points
- **Auto-scaling**: Y-axis adjusts to data range

#### 2. Resource Usage Bars
- **CPU Usage**: Visual bar with percentage (color-coded: green/yellow/red)
- **Memory Usage**: Visual bar with percentage
- **Battery Drain Rate**: Shows impact on battery life

#### 3. Bandwidth Ratio Visualization
- **Inbound Traffic**: Green bar showing incoming Mbps
- **Outbound Traffic**: Blue bar showing outgoing Mbps
- **Real-time Updates**: Synchronized with monitoring service

#### 4. Model Performance Metrics
- **Model Accuracy**: ML model effectiveness percentage
- **Model Latency**: Processing time in milliseconds
- **Status Indicators**: Shows model health

#### 5. Tor Connection Pool Status
- **Active Circuits**: Number of active Tor circuits
- **Aggregated Data**: Pulls from TorManager service
- **Circuit Health**: Visual representation

#### 6. Error Log
- **Scrollable List**: Last 10 errors displayed
- **Timestamp Display**: Each entry shows HH:MM:SS
- **Color-coded**: Warning color for visibility
- **Auto-updates**: New errors appear in real-time

## Architecture

### Services

#### ObfuscationConfigService (`src/services/obfuscation_config_service.py`)
- **Purpose**: Persists all obfuscation settings to disk
- **Storage**: JsonStore in user data directory
- **Settings Managed**:
  - Mode toggles (standard/maximum)
  - Auto-switch configuration
  - Schedule settings
  - Battery saver configuration
  - Network quality awareness
  - Data cap settings
  - Historical statistics

#### ObfuscationMonitorService (`src/services/obfuscation_monitor_service.py`)
- **Purpose**: Aggregates monitoring data from multiple sources
- **Update Frequency**: 2.5 seconds (optimized for low-power devices)
- **Data Sources**:
  - TorManager (circuit information)
  - SmartAgent (traffic metrics)
  - Internal metrics (CPU, memory, battery)
- **Metrics Tracked**:
  - Packets per second history
  - Resource usage (CPU/memory/battery)
  - Bandwidth in/out
  - Model performance
  - Error logs
  - Active circuit count

### Event Bus Integration

New event types added to `src/utils/event_bus.py`:

```python
on_obfuscation_settings_update  # Fired when settings change
on_obfuscation_monitor_update   # Fired every 2.5s with monitoring data
on_obfuscation_warning         # Fired when thresholds are hit
```

### Widgets (`src/widgets/obfuscation_widgets.py`)

#### ResourceBar
- Visual progress bar for resource usage
- Color-coded thresholds (green < 40%, yellow < 70%, red >= 70%)
- Percentage label

#### PacketsGraph
- Line chart for packets/sec over time
- Canvas-based rendering with caching
- Responsive to window size changes

#### BandwidthVisualization
- Dual horizontal bars for inbound/outbound traffic
- Color-coded (green for in, blue for out)
- Mbps labels

#### ErrorLogList
- Scrollable error log display
- Timestamped entries
- Empty state handling

#### CircuitStatusWidget
- Displays active Tor circuit count
- Large bold number for visibility

#### ModelPerformanceWidget
- Two-row display: accuracy and latency
- Formatted percentages and milliseconds

### Screen (`src/screens/obfuscation_settings_screen.py`)

#### ObfuscationSettingsScreen
- **Responsive Layout**: Adapts to window size (1 or 2 columns)
- **Card-based UI**: Organized into logical sections
- **Real-time Updates**: Binds to event bus for live data
- **Persistent State**: All settings saved automatically
- **User-friendly Controls**: Switches, sliders, spinners

## Performance Optimizations

### 1. Throttled Updates
- Monitoring service updates every 2.5 seconds (not every frame)
- Reduces CPU usage and battery drain
- Configurable interval in service

### 2. Canvas Caching
- Graph widgets use canvas.before and canvas.after
- Background rectangles cached
- Only data lines redrawn on updates

### 3. Rolling Data Windows
- Limited history (30-50 data points)
- Old data automatically removed
- Prevents memory growth

### 4. Conditional Rendering
- Empty state handling (no errors = placeholder)
- Skip rendering when mode is off
- Lazy updates only when visible

### 5. Batched Event Emissions
- Single event emission per update cycle
- All metrics bundled in one dictionary
- Reduces event bus overhead

## Integration with Existing Services

### TorManager Integration
```python
event_bus.bind(on_tor_state_update=self._on_tor_state_update)
# Extracts active circuit count from Tor state
```

### SmartAgent Integration
```python
traffic_state = smart_agent.get_state()
mode = traffic_state.get('mode', 'off')
# Adjusts metrics based on current obfuscation mode
```

## Usage Examples

### Enable Standard Mode
```python
from src.services.obfuscation_config_service import obfuscation_config_service

obfuscation_config_service.update_settings(standard_mode_enabled=True)
```

### Set Schedule
```python
obfuscation_config_service.update_settings(
    schedule_mode='business',
    schedule_start_hour=9,
    schedule_start_minute=0,
    schedule_end_hour=17,
    schedule_end_minute=0
)
```

### Configure Data Cap
```python
obfuscation_config_service.update_settings(
    data_cap_enabled=True,
    data_cap_mb=5000,
    data_cap_warning_percent=80
)
```

### Monitor Resource Usage
```python
from src.services.obfuscation_monitor_service import obfuscation_monitor_service

state = obfuscation_monitor_service.get_state()
cpu = state['cpu_usage']
memory = state['memory_usage']
battery = state['battery_drain']
```

## Testing

Run the test suite:
```bash
python test_obfuscation.py
```

Tests cover:
- Config service persistence
- Monitor service metrics
- Event bus integration
- Widget instantiation
- Screen initialization
- Settings persistence

## User Workflows

### 1. Modify Settings
1. Navigate to "Obfuscation" tab
2. Toggle desired mode (Standard/Maximum)
3. Configure schedule and thresholds
4. Settings automatically persist to disk
5. Changes immediately reflected in monitoring

### 2. Monitor Performance
1. View live traffic graph for current activity
2. Check resource bars for system impact
3. Review bandwidth usage
4. Monitor model performance metrics
5. Check Tor circuit status
6. Review error log for issues

### 3. Receive Warnings
1. System monitors data cap usage
2. When threshold (80%) reached, warning emitted
3. Warning displayed in UI
4. User can adjust cap or reset statistics

### 4. View Historical Stats
1. Session stats show current session data
2. Today/Week stats show aggregate data
3. Reset button clears session stats
4. Historical data persists across app restarts

## File Structure

```
src/
├── services/
│   ├── obfuscation_config_service.py    # Settings persistence
│   └── obfuscation_monitor_service.py   # Monitoring metrics
├── widgets/
│   └── obfuscation_widgets.py          # UI components
├── screens/
│   └── obfuscation_settings_screen.py  # Main screen
└── utils/
    └── event_bus.py                    # Event system (updated)
```

## Acceptance Criteria ✅

- ✅ Users can enable/disable Standard & Maximum modes
- ✅ Auto-switch rules with configurable threshold
- ✅ Schedule editor with 24/7, specific hours, and smart presets
- ✅ Battery saver toggle with threshold control
- ✅ Network quality awareness setting
- ✅ Data cap warnings with configurable limits
- ✅ Historical stats (session/today/week)
- ✅ Live graph of packets/sec
- ✅ Resource usage bars (CPU/memory/battery)
- ✅ Bandwidth ratio visualization
- ✅ Model performance metrics
- ✅ Error log list
- ✅ Tor connection pool status (active circuits)
- ✅ Settings persist via config service
- ✅ Graphs optimized for low-power devices (throttled updates, canvas caching)
- ✅ Users can modify and persist each setting
- ✅ Warnings when thresholds hit
- ✅ Historical stats populate from mock history store
- ✅ Monitoring charts update smoothly without degrading FPS

## Future Enhancements

- Export historical data to CSV
- Custom threshold alerts
- Email/SMS notifications for warnings
- Advanced scheduling (day-of-week patterns)
- Circuit rotation strategies
- Performance profiling tools
- Real-time bandwidth shaping
- Machine learning model tuning UI

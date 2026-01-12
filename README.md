# FRC 2026 Launcher Trajectory Tool

An interactive Python application for optimizing launcher trajectories for the FRC 2026 competition. This tool helps teams visualize ball trajectories and tune launcher parameters to accurately hit the hub target.

## Features

- **Real-time Trajectory Visualization**: See the ball's arc instantly as you adjust parameters
- **Interactive Controls**: Both sliders and text input for precise parameter tuning
- **FRC 2026 Hub Model**: Accurate trapezoid/hexagon side profile representation
  - Top width: 48 inches (4 feet)
  - Bottom width: 27.5 inches
  - Top height: 72 inches (6 feet) from ground
  - Bottom height: 56.5 inches from ground
- **Hit Detection**: Instant feedback showing if trajectory hits or misses the hub
- **Time-to-Target**: Displays flight time when trajectory successfully hits the hub
- **Save & Compare**: Save multiple trajectory configurations and compare them side-by-side
- **Hub Position Tracking**: Saved trajectories include hub outline at the saved distance

## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Required Packages

```bash
pip install matplotlib numpy
```

## Usage

### Running the Application

```bash
python LauncherTrajecotryTool.py
```

Or on Windows with virtual environment:
```powershell
& ".venv/Scripts/python.exe" LauncherTrajecotryTool.py
```

### Interface Controls

#### Adjustable Parameters

1. **Velocity (50-600 in/s)**: Initial launch velocity of the ball
   - Adjust via slider or text input
   - Measured in inches per second

2. **Angle (0-90°)**: Launch angle relative to horizontal
   - Adjust via slider or text input
   - Measured in degrees

3. **Launch Height (0-80 in)**: Height of the launcher above ground
   - Adjust via slider or text input
   - Measured in inches

4. **Distance to Hub (20-250 in)**: Distance from launch point to front edge of hub
   - Adjust via slider or text input
   - Measured in inches
   - Note: Distance is measured to the **front edge** of the hub, not the center

#### Buttons

- **Save Trajectory**: Saves the current trajectory and hub position on the graph
  - Each saved trajectory appears as a dashed line with a unique color
  - The hub outline at the saved distance appears as a dotted line
  - Legend shows: Velocity (V), Angle (A), Launch Height (H), and Distance (D)

- **Clear Saved**: Removes all saved trajectories and hub outlines from the graph

### Understanding the Display

#### Visual Elements

- **Blue solid line**: Current trajectory arc
- **Green dot**: Launch point (position of the launcher)
- **Red filled trapezoid**: Current hub target position
- **Dashed lines**: Saved trajectories (various colors)
- **Dotted trapezoids**: Saved hub positions (matching trajectory colors)

#### Status Indicators

- **Green title "✓ HIT!"**: Current trajectory successfully passes through the hub
  - Displays time-to-target in seconds (e.g., "Time: 0.625s")
- **Red title "✗ MISS"**: Current trajectory does not hit the hub

## Physics Model

The tool uses standard projectile motion equations:

- **Horizontal position**: x = v₀ × cos(θ) × t
- **Vertical position**: y = h₀ + v₀ × sin(θ) × t - ½ × g × t²

Where:
- v₀ = initial velocity
- θ = launch angle
- h₀ = launch height
- g = 386.4 in/s² (gravity, converted from 32.2 ft/s²)
- t = time

## Use Cases

### Optimization Workflow

1. **Set Initial Position**: Enter your robot's typical shooting position (distance from hub)
2. **Set Launcher Height**: Input your launcher's height on the robot
3. **Tune Velocity & Angle**: Adjust until you achieve a hit
4. **Save Configuration**: Click "Save Trajectory" to keep this setting
5. **Test Variations**: Try different distances or heights
6. **Compare**: Visually compare multiple saved trajectories to find optimal settings

### Example Scenarios

**Close Range Shot**
- Distance: 60-100 inches
- Typical angle: 30-45°
- Considerations: Faster shot, less arc, easier to defend

**Long Range Shot**
- Distance: 150-250 inches
- Typical angle: 45-60°
- Considerations: Higher arc, more flight time, harder to defend

**Variable Height Testing**
- Save trajectories at multiple launch heights
- Determine optimal mounting position for your launcher

## Tips for FRC Teams

1. **Measure Accurately**: Use precise measurements for your launcher height and typical shooting positions
2. **Account for Robot Movement**: Consider that your robot may not be perfectly stationary
3. **Test Flight Time**: Use the time-to-target display to coordinate with intake/loading mechanisms
4. **Save Multiple Configurations**: Save trajectories for different field positions (close, mid, far)
5. **Print or Screenshot**: Save your optimized configurations for reference during competition
6. **Verify in Practice**: Always test your calculated trajectories with real hardware

## Troubleshooting

### Ball Not Hitting Hub

- Try increasing velocity
- Adjust angle (typically between 30-60° works best)
- Verify distance measurement is accurate
- Check that launch height is correctly set

### Trajectory Going Off Screen

- The graph automatically adjusts, but you can manually zoom if needed
- Very high velocities or angles may require larger distances

### Performance Issues

- Clear saved trajectories periodically if you have many saved
- Close and restart the application if it becomes slow

## Technical Specifications

- **Programming Language**: Python 3
- **GUI Framework**: Matplotlib with interactive widgets
- **Physics Engine**: Custom projectile motion calculations using NumPy
- **Graph Resolution**: 200 points per trajectory for smooth curves

## File Structure

```
Launcher Trajecotry Tool/
├── LauncherTrajecotryTool.py    # Main application file
├── README.md                     # This file
└── .venv/                        # Python virtual environment (if used)
```

## Contributing

This tool was created for FRC teams. Feel free to modify and enhance it for your team's needs!

## Version History

- **v1.0** (January 2026): Initial release
  - Interactive trajectory plotting
  - FRC 2026 hub specifications
  - Save/compare functionality
  - Hit detection with time-to-target
  - Trapezoid hub model

## Support

For issues or questions:
1. Check that all parameters are within valid ranges
2. Verify matplotlib and numpy are properly installed
3. Ensure Python version is 3.8 or higher

## License

Created for FRC teams. Use freely for educational and competition purposes.

---

**Good luck in FRC 2026!** 🤖🎯

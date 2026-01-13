import matplotlib.pyplot as plt
from matplotlib.widgets import Slider, TextBox, Button
import numpy as np
from matplotlib.patches import Polygon

# FRC 2026 Hub dimensions (in inches)
HUB_TOP_WIDTH = 48      # Width of the top of the hub (4 feet)
HUB_BOTTOM_WIDTH = 27.5 # Width of the bottom of the hub (2.29 feet)
HUB_TOP_HEIGHT = 72     # Height of the top of the hub from ground (6 feet)
HUB_BOTTOM_HEIGHT = 56.5  # Height of the bottom from ground
HUB_HEIGHT = (HUB_TOP_HEIGHT + HUB_BOTTOM_HEIGHT) / 2  # Center height for hit detection

# Physics constants
GRAVITY = 386.4  # inches per second squared (32.2 ft/s^2)
AIR_DENSITY = 0.0765  # lb/ft^3 at sea level
BALL_MASS = 0.27  # lb (approximate - typical FRC foam balls are 4-6 oz = 0.25-0.375 lb)
                  # Heavier ball = less affected by drag and Magnus
                  # 2022 Cargo: ~0.25 lb, 2020 Power Cell: ~0.31 lb

class LauncherTrajectoryTool:
    def __init__(self):
        # Initial parameters - Single-Wheel Hooded Shooter
        self.ball_diameter = 5.91  # inches (FRC 2026 game piece)
        self.flywheel_diameter = 4.0  # inches (typical flywheel size)
        self.flywheel_rpm = 3600  # RPM of the flywheel
        self.spin_efficiency = 0.70  # 70% of flywheel RPM transfers to ball spin (backspin)
        self.angle = 45      # degrees (hood angle)
        self.launch_height = 20  # inches 
        self.distance = 150  # inches from hub (12.5 feet)
        
        # Calculate derived values
        self.velocity = self.calculate_ball_velocity()
        self.spin_rate = self.calculate_ball_spin()
        
        # Physics model selector
        self.use_magnus = False  # False = simple projectile, True = Magnus effect
        
        # Store saved trajectories
        self.saved_trajectories = []
        self.saved_settings = []
        
        # Create the figure and axis
        self.fig, self.ax = plt.subplots(figsize=(14, 8))
        plt.subplots_adjust(left=0.1, bottom=0.35, right=0.95, top=0.95)
        
        # Initialize plot
        self.trajectory_line, = self.ax.plot([], [], 'b-', linewidth=2, label='Current Trajectory')
        self.launch_point, = self.ax.plot([], [], 'go', markersize=10, label='Launch Point')
        self.hub_rect = None
        self.hub_outline = None
        
        # Setup the plot
        self.setup_plot()
        self.setup_widgets()
        self.update_plot()
        
        plt.show()
    
    def setup_plot(self):
        """Setup the plot area with hub visualization"""
        self.ax.set_xlabel('Horizontal Distance (inches)', fontsize=12)
        self.ax.set_ylabel('Height (inches)', fontsize=12)
        self.ax.set_title('FRC 2026 Launcher Trajectory Tool - Single-Wheel Hooded Shooter', 
                         fontsize=14, fontweight='bold')
        self.ax.grid(True, alpha=0.3)
        self.ax.set_xlim(-20, 250)
        self.ax.set_ylim(0, 150)
        self.ax.legend(loc='upper right')
        self.ax.set_aspect('equal')
        
        # Draw the hub
        self.draw_hub()
    
    def draw_hub(self):
        """Draw the FRC 2026 hub as a trapezoid (hexagon side profile)"""
        # Remove old hub if exists
        if self.hub_rect:
            self.hub_rect.remove()
        if self.hub_outline:
            self.hub_outline.remove()
        
        # Hub position - distance is to the front edge, not center
        # The hub center is offset by the average width / 2
        average_width = (HUB_TOP_WIDTH + HUB_BOTTOM_WIDTH) / 2
        hub_center_x = self.distance + average_width / 2
        
        # Create trapezoid vertices (bottom-left, bottom-right, top-right, top-left)
        # The trapezoid is wider at the top than the bottom
        bottom_left = [hub_center_x - HUB_BOTTOM_WIDTH/2, HUB_BOTTOM_HEIGHT]
        bottom_right = [hub_center_x + HUB_BOTTOM_WIDTH/2, HUB_BOTTOM_HEIGHT]
        top_right = [hub_center_x + HUB_TOP_WIDTH/2, HUB_TOP_HEIGHT]
        top_left = [hub_center_x - HUB_TOP_WIDTH/2, HUB_TOP_HEIGHT]
        
        vertices = [bottom_left, bottom_right, top_right, top_left]
        
        # Draw filled trapezoid for hub
        self.hub_rect = Polygon(vertices, facecolor='red', edgecolor='darkred',
                               linewidth=3, alpha=0.6, label='Hub Target')
        self.ax.add_patch(self.hub_rect)
        
        # Draw outline for emphasis
        self.hub_outline = Polygon(vertices, facecolor='none', edgecolor='darkred',
                                   linewidth=4, linestyle='--')
        self.ax.add_patch(self.hub_outline)
    
    def calculate_ball_velocity(self):
        """Calculate ball velocity from flywheel surface speed"""
        # Surface speed of flywheel in inches per second
        # v = π × diameter × RPM / 60
        return np.pi * self.flywheel_diameter * self.flywheel_rpm / 60.0
    
    def calculate_ball_spin(self):
        """Calculate ball backspin from flywheel (single-wheel hooded shooter)"""
        # For a single wheel on bottom with hood on top, ball gets backspin
        # Backspin RPM is a fraction of flywheel RPM (typically 60-80%)
        return self.flywheel_rpm * self.spin_efficiency
    
    def calculate_trajectory(self, velocity, angle_deg, launch_height):
        """Calculate trajectory points using selected physics model"""
        if self.use_magnus:
            return self.calculate_trajectory_magnus(velocity, angle_deg, launch_height, self.spin_rate)
        else:
            return self.calculate_trajectory_simple(velocity, angle_deg, launch_height)
    
    def calculate_trajectory_simple(self, velocity, angle_deg, launch_height):
        """Calculate trajectory using simple projectile motion (no air resistance or Magnus)"""
        angle_rad = np.radians(angle_deg)
        
        # Initial velocity components
        vx = velocity * np.cos(angle_rad)
        vy = velocity * np.sin(angle_rad)
        
        # Time of flight (when ball hits ground or goes beyond distance)
        # Solve: y = launch_height + vy*t - 0.5*g*t^2 = 0
        if vy**2 + 2 * GRAVITY * launch_height < 0:
            t_max = 0
        else:
            t_max = (vy + np.sqrt(vy**2 + 2 * GRAVITY * launch_height)) / GRAVITY
        
        # Generate time points
        t = np.linspace(0, t_max, 200)
        
        # Calculate positions
        x = vx * t
        y = launch_height + vy * t - 0.5 * GRAVITY * t**2
        
        # Only keep points above ground
        valid = y >= 0
        x = x[valid]
        y = y[valid]
        
        return x, y
    
    def calculate_trajectory_magnus(self, velocity, angle_deg, launch_height, spin_rpm):
        """Calculate trajectory with Magnus effect and drag (single-wheel hooded shooter with backspin)"""
        angle_rad = np.radians(angle_deg)
        
        # Initial conditions
        vx = velocity * np.cos(angle_rad)
        vy = velocity * np.sin(angle_rad)
        x = 0
        y = launch_height
        
        # Convert units for calculations
        radius = (self.ball_diameter / 2) / 12  # feet
        area = np.pi * radius**2  # ft^2
        mass = BALL_MASS  # lb
        omega = spin_rpm * 2 * np.pi / 60  # rad/s (angular velocity)
        
        # Drag coefficient (sphere, approximate)
        Cd = 0.47
        
        # Magnus lift coefficient (dimensionless, empirical)
        # Conservative values for game balls: 0.05-0.15
        # This is MUCH smaller than I had before (was 0.5, way too high!)
        # Reference: Basketball is ~0.12, we'll use slightly less for foam balls
        Cl_magnus = 0.10  # Reduced significantly - backspin effect should be subtle, not dominant
        
        # Time step for numerical integration
        dt = 0.001  # seconds
        t_max = 5.0  # maximum simulation time
        
        # Arrays to store trajectory
        x_array = [x]
        y_array = [y]
        
        t = 0
        while y >= 0 and t < t_max:
            # Current speed (in inches/second, need to convert for force calculations)
            speed = np.sqrt(vx**2 + vy**2)
            speed_fps = speed / 12.0  # convert to feet per second
            
            if speed > 0.1:  # Avoid near-zero speeds
                # Drag force (opposes motion)
                # F_drag = 0.5 * rho * Cd * A * v^2
                drag_force = 0.5 * AIR_DENSITY * Cd * area * (speed_fps**2)  # lb
                drag_accel = (drag_force / mass) * 32.2  # ft/s^2
                drag_accel_in = drag_accel * 12.0  # in/s^2
                
                # Apply drag in direction opposite to velocity
                drag_ax = -(drag_accel_in) * (vx / speed)
                drag_ay = -(drag_accel_in) * (vy / speed)
                
                # Magnus force - CORRECTED FORMULA
                # Using well-established formula: F_L = Cl * (1/2) * rho * A * v^2
                # Where Cl depends on spin parameter: Cl = Cl_magnus * (omega * r / v)
                # This gives: F_L = Cl_magnus * (1/2) * rho * A * v * omega * r
                
                if abs(spin_rpm) > 10:  # Only apply if significant spin
                    # Spin parameter (dimensionless): S = ω*r / v
                    spin_parameter = abs(omega * radius / speed_fps)
                    
                    # Limit spin parameter to reasonable values (typically < 1.0 for sports)
                    # If S > 1, the surface speed of ball exceeds its translational speed
                    spin_parameter = min(spin_parameter, 1.0)
                    
                    # Magnus force using proper aerodynamic formula
                    # F = Cl_magnus * spin_param * (1/2) * rho * A * v^2
                    magnus_force = Cl_magnus * spin_parameter * 0.5 * AIR_DENSITY * area * (speed_fps**2)  # lb
                    magnus_accel = (magnus_force / mass) * 32.2  # ft/s^2
                    magnus_accel_in = magnus_accel * 12.0  # in/s^2
                    
                    # Direction perpendicular to velocity (90° CCW rotation for backspin = upward lift)
                    perp_x = -vy / speed
                    perp_y = vx / speed
                    
                    # Apply Magnus force (positive spin_rpm = backspin = upward lift)
                    magnus_ax = magnus_accel_in * perp_x * np.sign(spin_rpm)
                    magnus_ay = magnus_accel_in * perp_y * np.sign(spin_rpm)
                else:
                    magnus_ax = magnus_ay = 0
            else:
                drag_ax = drag_ay = 0
                magnus_ax = magnus_ay = 0
            
            # Total acceleration
            ax = drag_ax + magnus_ax
            ay = -GRAVITY + drag_ay + magnus_ay
            
            # Update velocity (Euler integration)
            vx += ax * dt
            vy += ay * dt
            
            # Update position
            x += vx * dt
            y += vy * dt
            
            # Store trajectory point
            x_array.append(x)
            y_array.append(y)
            
            t += dt
        
        return np.array(x_array), np.array(y_array)
    
    def update_plot(self):
        """Update the trajectory plot"""
        # Calculate current trajectory
        x, y = self.calculate_trajectory(self.velocity, self.angle, self.launch_height)
        
        # Update trajectory line
        self.trajectory_line.set_data(x, y)
        
        # Update launch point
        self.launch_point.set_data([0], [self.launch_height])
        
        # Redraw hub at new distance
        self.draw_hub()
        
        # Adjust plot limits if needed
        if len(x) > 0:
            max_x = max(max(x), self.distance + 50)
            max_y = max(max(y), HUB_HEIGHT + 30)
            self.ax.set_xlim(-20, max_x)
            self.ax.set_ylim(0, max_y)
        
        # Check if trajectory passes through hub
        self.check_hit()
        
        self.fig.canvas.draw_idle()
    
    def check_hit(self):
        """Check if trajectory passes through the trapezoidal hub"""
        x, y = self.calculate_trajectory(self.velocity, self.angle, self.launch_height)
        
        # Hub center position - distance is to the front edge, not center
        average_width = (HUB_TOP_WIDTH + HUB_BOTTOM_WIDTH) / 2
        hub_center_x = self.distance + average_width / 2
        
        # Calculate velocity components for time calculation
        angle_rad = np.radians(self.angle)
        vx = self.velocity * np.cos(angle_rad)
        vy = self.velocity * np.sin(angle_rad)
        
        # Check intersection with trapezoid
        hit = False
        hit_time = None
        hit_index = None
        
        for i in range(len(x)):
            # Calculate the width of the hub at this height
            if HUB_BOTTOM_HEIGHT <= y[i] <= HUB_TOP_HEIGHT:
                # Linear interpolation of width based on height
                height_ratio = (y[i] - HUB_BOTTOM_HEIGHT) / (HUB_TOP_HEIGHT - HUB_BOTTOM_HEIGHT)
                width_at_height = HUB_BOTTOM_WIDTH + height_ratio * (HUB_TOP_WIDTH - HUB_BOTTOM_WIDTH)
                
                # Check if x position is within the trapezoid at this height
                hub_x_min = hub_center_x - width_at_height / 2
                hub_x_max = hub_center_x + width_at_height / 2
                
                if hub_x_min <= x[i] <= hub_x_max:
                    hit = True
                    hit_index = i
                    # Calculate time to reach this point
                    if vx > 0:
                        hit_time = x[i] / vx
                    break
        
        # Update title with hit status and time
        if hit and hit_time is not None:
            self.ax.set_title(f'FRC 2026 - Single-Wheel Hooded Shooter - ✓ HIT! (Time: {hit_time:.3f}s)', 
                            fontsize=14, fontweight='bold', color='green')
        elif hit:
            self.ax.set_title('FRC 2026 - Single-Wheel Hooded Shooter - ✓ HIT!', 
                            fontsize=14, fontweight='bold', color='green')
        else:
            self.ax.set_title('FRC 2026 - Single-Wheel Hooded Shooter - ✗ MISS', 
                            fontsize=14, fontweight='bold', color='red')
    
    def save_trajectory(self, event):
        """Save current trajectory and hub position to display alongside new ones"""
        x, y = self.calculate_trajectory(self.velocity, self.angle, self.launch_height)
        
        # Generate a color for this trajectory
        colors = ['purple', 'orange', 'cyan', 'magenta', 'yellow', 'brown', 'pink', 'gray']
        color = colors[len(self.saved_trajectories) % len(colors)]
        
        # Plot saved trajectory
        line, = self.ax.plot(x, y, '--', linewidth=1.5, alpha=0.7, color=color,
                            label=f'Saved {len(self.saved_trajectories)+1}: '
                                  f'FW={self.flywheel_diameter:.1f}"@{self.flywheel_rpm:.0f}RPM, '
                                  f'A={self.angle:.0f}°, D={self.distance:.0f}"')
        
        # Save hub outline at current distance
        average_width = (HUB_TOP_WIDTH + HUB_BOTTOM_WIDTH) / 2
        hub_center_x = self.distance + average_width / 2
        
        # Create trapezoid vertices for saved hub
        bottom_left = [hub_center_x - HUB_BOTTOM_WIDTH/2, HUB_BOTTOM_HEIGHT]
        bottom_right = [hub_center_x + HUB_BOTTOM_WIDTH/2, HUB_BOTTOM_HEIGHT]
        top_right = [hub_center_x + HUB_TOP_WIDTH/2, HUB_TOP_HEIGHT]
        top_left = [hub_center_x - HUB_TOP_WIDTH/2, HUB_TOP_HEIGHT]
        
        vertices = [bottom_left, bottom_right, top_right, top_left]
        
        # Draw saved hub outline
        saved_hub = Polygon(vertices, facecolor='none', edgecolor=color,
                           linewidth=2, linestyle=':', alpha=0.5)
        self.ax.add_patch(saved_hub)
        
        self.saved_trajectories.append((line, saved_hub))
        self.saved_settings.append({
            'ball_diameter': self.ball_diameter,
            'flywheel_diameter': self.flywheel_diameter,
            'flywheel_rpm': self.flywheel_rpm,
            'spin_efficiency': self.spin_efficiency,
            'angle': self.angle,
            'launch_height': self.launch_height,
            'distance': self.distance
        })
        
        # Update legend
        self.ax.legend(loc='upper right', fontsize=8)
        self.fig.canvas.draw_idle()
    
    def clear_saved(self, event):
        """Clear all saved trajectories and hub outlines"""
        for items in self.saved_trajectories:
            if isinstance(items, tuple):
                # Remove both trajectory line and hub outline
                line, hub = items
                line.remove()
                hub.remove()
            else:
                # Legacy: just a line
                items.remove()
        self.saved_trajectories.clear()
        self.saved_settings.clear()
        self.ax.legend(loc='upper right')
        self.fig.canvas.draw_idle()
    
    def toggle_physics_model(self, event):
        """Toggle between simple projectile and Magnus effect"""
        self.use_magnus = not self.use_magnus
        
        # Update button appearance
        if self.use_magnus:
            self.physics_btn.label.set_text('Physics: Magnus Effect')
            self.physics_btn.color = 'lightblue'
            # Show spin efficiency slider
            self.spin_eff_slider.ax.set_visible(True)
        else:
            self.physics_btn.label.set_text('Physics: Simple Motion')
            self.physics_btn.color = 'lightgray'
            # Hide spin efficiency slider
            self.spin_eff_slider.ax.set_visible(False)
        
        self.update_plot()
        self.fig.canvas.draw_idle()
    
    def setup_widgets(self):
        """Setup interactive sliders and text boxes for single-wheel hooded shooter"""
        # Physics model toggle button
        ax_physics = plt.axes([0.60, 0.27, 0.20, 0.04])
        self.physics_btn = Button(ax_physics, 'Physics: Simple Motion', 
                                  color='lightgray', hovercolor='skyblue')
        self.physics_btn.on_clicked(self.toggle_physics_model)
        
        # Ball diameter slider
        ax_ball_diam_slider = plt.axes([0.15, 0.30, 0.3, 0.02])
        self.ball_diam_slider = Slider(ax_ball_diam_slider, 'Ball Diameter (in)', 3.0, 10.0, 
                                       valinit=self.ball_diameter, valstep=0.1)
        self.ball_diam_slider.on_changed(self.update_ball_diameter)
        
        # Flywheel diameter slider
        ax_flywheel_diam_slider = plt.axes([0.15, 0.25, 0.3, 0.02])
        self.flywheel_diam_slider = Slider(ax_flywheel_diam_slider, 'Flywheel Diameter (in)', 2.0, 8.0, 
                                           valinit=self.flywheel_diameter, valstep=0.25)
        self.flywheel_diam_slider.on_changed(self.update_flywheel_diameter)
        
        # Flywheel RPM slider
        ax_flywheel_rpm_slider = plt.axes([0.15, 0.20, 0.3, 0.02])
        self.flywheel_rpm_slider = Slider(ax_flywheel_rpm_slider, 'Flywheel RPM', 0, 5000, 
                                          valinit=self.flywheel_rpm, valstep=50)
        self.flywheel_rpm_slider.on_changed(self.update_flywheel_rpm)
        
        # Hood angle slider
        ax_angle_slider = plt.axes([0.15, 0.15, 0.3, 0.02])
        self.angle_slider = Slider(ax_angle_slider, 'Hood Angle (deg)', 0, 90, 
                                   valinit=self.angle, valstep=0.5)
        self.angle_slider.on_changed(self.update_angle)
        
        # Launch height slider
        ax_height_slider = plt.axes([0.15, 0.10, 0.3, 0.02])
        self.height_slider = Slider(ax_height_slider, 'Launch Height (in)', 0, 80, 
                                    valinit=self.launch_height, valstep=1)
        self.height_slider.on_changed(self.update_height)

        # Distance slider
        ax_dist_slider = plt.axes([0.15, 0.05, 0.3, 0.02])
        self.dist_slider = Slider(ax_dist_slider, 'Distance to Hub (in)', 20, 220, 
                                  valinit=self.distance, valstep=5)
        self.dist_slider.on_changed(self.update_distance)
        
        # Spin efficiency slider (initially hidden, for Magnus effect mode)
        ax_spin_eff_slider = plt.axes([0.60, 0.20, 0.3, 0.02])
        self.spin_eff_slider = Slider(ax_spin_eff_slider, 'Spin Efficiency (%)', 0, 100, 
                                      valinit=self.spin_efficiency * 100, valstep=1)
        self.spin_eff_slider.on_changed(self.update_spin_efficiency)
        self.spin_eff_slider.ax.set_visible(False)  # Hidden by default
        
        # Save button (moved to the right to avoid blocking by spin slider)
        ax_save = plt.axes([0.60, 0.04, 0.15, 0.04])
        self.save_btn = Button(ax_save, 'Save Trajectory', color='lightgreen', hovercolor='green')
        self.save_btn.on_clicked(self.save_trajectory)
        
        # Clear button (moved to the right to avoid blocking by spin slider)
        ax_clear = plt.axes([0.77, 0.04, 0.15, 0.04])
        self.clear_btn = Button(ax_clear, 'Clear Saved', color='lightcoral', hovercolor='red')
        self.clear_btn.on_clicked(self.clear_saved)
        
        # Info text
        info_text = (
            "Single-Wheel Hooded Shooter:\n"
            "• Flywheel on bottom, hood on top\n"
            "• Ball gets backspin from flywheel contact\n"
            "• Toggle physics to enable/disable Magnus effect\n"
            "• Spin Efficiency: % of flywheel RPM transferred to ball\n"
            "• Green title = Hit, Red title = Miss"
        )
        plt.figtext(0.60, 0.12, info_text, fontsize=9, 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        # Display calculated values
        self.info_text = plt.figtext(0.60, 0.32, '', fontsize=9,
                                     bbox=dict(boxstyle='round', facecolor='lightblue', alpha=0.5))
        self.update_info_display()
    
    def update_info_display(self):
        """Update the display showing calculated velocity and spin"""
        info_str = (
            f"Calculated Values:\n"
            f"Ball Velocity: {self.velocity:.1f} in/s ({self.velocity/12:.1f} ft/s)\n"
            f"Ball Backspin: {self.spin_rate:.0f} RPM"
        )
        self.info_text.set_text(info_str)
    
    def update_ball_diameter(self, val):
        self.ball_diameter = val
        self.update_plot()
    
    def update_flywheel_diameter(self, val):
        self.flywheel_diameter = val
        self.velocity = self.calculate_ball_velocity()
        self.spin_rate = self.calculate_ball_spin()
        self.update_info_display()
        self.update_plot()
    
    def update_flywheel_rpm(self, val):
        self.flywheel_rpm = val
        self.velocity = self.calculate_ball_velocity()
        self.spin_rate = self.calculate_ball_spin()
        self.update_info_display()
        self.update_plot()
    
    def update_spin_efficiency(self, val):
        self.spin_efficiency = val / 100.0  # Convert percentage to fraction
        self.spin_rate = self.calculate_ball_spin()
        self.update_info_display()
        self.update_plot()
    
    def update_angle(self, val):
        self.angle = val
        self.update_plot()
    
    def update_height(self, val):
        self.launch_height = val
        self.update_plot()
    
    def update_distance(self, val):
        self.distance = val
        self.update_plot()


if __name__ == "__main__":
    print("Starting FRC 2026 Launcher Trajectory Tool...")
    print("=" * 60)
    print("Shooter Type: Single-Wheel Hooded Shooter")
    print("  - Flywheel on bottom imparts backspin to ball")
    print("  - Hood on top directs launch angle")
    print("=" * 60)
    print("Hub Specifications (Trapezoid/Hexagon Side Profile):")
    print(f"  - Top Height: {HUB_TOP_HEIGHT} inches ({HUB_TOP_HEIGHT/12:.1f} feet)")
    print(f"  - Bottom Height: {HUB_BOTTOM_HEIGHT} inches ({HUB_BOTTOM_HEIGHT/12:.1f} feet)")
    print(f"  - Top Width: {HUB_TOP_WIDTH} inches ({HUB_TOP_WIDTH/12:.1f} feet)")
    print(f"  - Bottom Width: {HUB_BOTTOM_WIDTH} inches ({HUB_BOTTOM_WIDTH/12:.2f} feet)")
    print("=" * 60)
    print("Adjust flywheel parameters to control ball velocity and spin!")
    print("Toggle Magnus Effect to see the impact of backspin on trajectory.")
    print("=" * 60)
    
    app = LauncherTrajectoryTool()

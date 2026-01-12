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
BALL_DIAMETER = 5.91 # inches (FRC 2026 game piece - approximate)
BALL_MASS = 0.5  # lb (approximate)

class LauncherTrajectoryTool:
    def __init__(self):
        # Initial parameters
        self.velocity = 240  # inches per second (20 ft/s)
        self.angle = 45      # degrees
        self.launch_height = 20  # inches 
        self.distance = 150  # inches from hub (12.5 feet)
        self.spin_rate = 3000  # RPM (revolutions per minute)
        
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
        self.ax.set_title('FRC 2026 Launcher Trajectory Tool', fontsize=14, fontweight='bold')
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
        """Calculate trajectory with Magnus effect and drag"""
        angle_rad = np.radians(angle_deg)
        
        # Initial conditions
        vx = velocity * np.cos(angle_rad)
        vy = velocity * np.sin(angle_rad)
        x = 0
        y = launch_height
        
        # Convert units for calculations
        radius = (BALL_DIAMETER / 2) / 12  # feet
        area = np.pi * radius**2  # ft^2
        mass = BALL_MASS  # lb
        omega = spin_rpm * 2 * np.pi / 60  # rad/s
        
        # Drag coefficient (sphere, approximate)
        Cd = 0.47
        
        # Magnus coefficient (empirical, depends on spin and velocity)
        # Cl = lift coefficient due to Magnus effect
        Cl = 0.2  # approximate for spinning sphere
        
        # Time step for numerical integration
        dt = 0.001  # seconds
        t_max = 5.0  # maximum simulation time
        
        # Arrays to store trajectory
        x_array = [x]
        y_array = [y]
        
        t = 0
        while y >= 0 and t < t_max:
            # Current speed
            speed = np.sqrt(vx**2 + vy**2)
            
            if speed > 0:
                # Drag force (opposes motion)
                # F_drag = 0.5 * rho * Cd * A * v^2
                drag_force = 0.5 * AIR_DENSITY * Cd * area * speed**2
                drag_ax = -(drag_force / mass) * (vx / speed) * 386.4  # convert to in/s^2
                drag_ay = -(drag_force / mass) * (vy / speed) * 386.4
                
                # Magnus force (perpendicular to velocity, in direction of spin × velocity)
                # F_magnus = 0.5 * rho * Cl * A * v^2
                # For backspin, this creates upward lift
                magnus_force = 0.5 * AIR_DENSITY * Cl * area * speed**2
                
                # Magnus acceleration (perpendicular to velocity)
                # Assuming backspin, Magnus force is upward (perpendicular to velocity)
                magnus_accel = (magnus_force / mass) * 386.4  # in/s^2
                
                # Direction perpendicular to velocity (for backspin: rotates velocity vector 90° CCW)
                if speed > 0:
                    perp_x = -vy / speed
                    perp_y = vx / speed
                else:
                    perp_x = 0
                    perp_y = 0
                
                magnus_ax = magnus_accel * perp_x * np.sign(spin_rpm)
                magnus_ay = magnus_accel * perp_y * np.sign(spin_rpm)
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
            self.ax.set_title(f'FRC 2026 Launcher Trajectory Tool - ✓ HIT! (Time: {hit_time:.3f}s)', 
                            fontsize=14, fontweight='bold', color='green')
        elif hit:
            self.ax.set_title('FRC 2026 Launcher Trajectory Tool - ✓ HIT!', 
                            fontsize=14, fontweight='bold', color='green')
        else:
            self.ax.set_title('FRC 2026 Launcher Trajectory Tool - ✗ MISS', 
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
                                  f'V={self.velocity:.0f}, A={self.angle:.0f}°, '
                                  f'H={self.launch_height:.0f}, D={self.distance:.0f}')
        
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
            'velocity': self.velocity,
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
            # Show spin slider
            self.spin_slider.ax.set_visible(True)
            self.spin_text.ax.set_visible(True)
        else:
            self.physics_btn.label.set_text('Physics: Simple Motion')
            self.physics_btn.color = 'lightgray'
            # Hide spin slider
            self.spin_slider.ax.set_visible(False)
            self.spin_text.ax.set_visible(False)
        
        self.update_plot()
        self.fig.canvas.draw_idle()
    
    def setup_widgets(self):
        """Setup interactive sliders and text boxes"""
        # Physics model toggle button
        ax_physics = plt.axes([0.60, 0.27, 0.20, 0.04])
        self.physics_btn = Button(ax_physics, 'Physics: Simple Motion', 
                                  color='lightgray', hovercolor='skyblue')
        self.physics_btn.on_clicked(self.toggle_physics_model)
        
        # Velocity slider
        ax_vel_slider = plt.axes([0.15, 0.25, 0.3, 0.02])
        self.vel_slider = Slider(ax_vel_slider, 'Velocity (in/s)', 50, 600, 
                                 valinit=self.velocity, valstep=5)
        self.vel_slider.on_changed(self.update_velocity)
        
        # Velocity text box
        ax_vel_text = plt.axes([0.47, 0.245, 0.08, 0.03])
        self.vel_text = TextBox(ax_vel_text, '', initial=str(self.velocity))
        self.vel_text.on_submit(self.update_velocity_text)
        
        # Angle slider
        ax_angle_slider = plt.axes([0.15, 0.20, 0.3, 0.02])
        self.angle_slider = Slider(ax_angle_slider, 'Angle (deg)', 0, 90, 
                                   valinit=self.angle, valstep=0.5)
        self.angle_slider.on_changed(self.update_angle)
        
        # Angle text box
        ax_angle_text = plt.axes([0.47, 0.195, 0.08, 0.03])
        self.angle_text = TextBox(ax_angle_text, '', initial=str(self.angle))
        self.angle_text.on_submit(self.update_angle_text)
        
        # Launch height slider
        ax_height_slider = plt.axes([0.15, 0.15, 0.3, 0.02])
        self.height_slider = Slider(ax_height_slider, 'Launch Height (in)', 0, 80, 
                                    valinit=self.launch_height, valstep=1)
        self.height_slider.on_changed(self.update_height)
        
        # Launch height text box
        ax_height_text = plt.axes([0.47, 0.145, 0.08, 0.03])
        self.height_text = TextBox(ax_height_text, '', initial=str(self.launch_height))
        self.height_text.on_submit(self.update_height_text)
        
        # Distance slider
        ax_dist_slider = plt.axes([0.15, 0.10, 0.3, 0.02])
        self.dist_slider = Slider(ax_dist_slider, 'Distance to Hub (in)', 20, 250, 
                                  valinit=self.distance, valstep=5)
        self.dist_slider.on_changed(self.update_distance)
        
        # Distance text box
        ax_dist_text = plt.axes([0.47, 0.095, 0.08, 0.03])
        self.dist_text = TextBox(ax_dist_text, '', initial=str(self.distance))
        self.dist_text.on_submit(self.update_distance_text)
        
        # Spin rate slider (initially hidden)
        ax_spin_slider = plt.axes([0.15, 0.05, 0.3, 0.02])
        self.spin_slider = Slider(ax_spin_slider, 'Spin Rate (RPM)', -6000, 6000, 
                                  valinit=self.spin_rate, valstep=100)
        self.spin_slider.on_changed(self.update_spin)
        self.spin_slider.ax.set_visible(False)  # Hidden by default
        
        # Spin rate text box (initially hidden)
        ax_spin_text = plt.axes([0.47, 0.045, 0.08, 0.03])
        self.spin_text = TextBox(ax_spin_text, '', initial=str(self.spin_rate))
        self.spin_text.on_submit(self.update_spin_text)
        self.spin_text.ax.set_visible(False)  # Hidden by default
        
        # Save button
        ax_save = plt.axes([0.15, 0.04, 0.15, 0.04])
        self.save_btn = Button(ax_save, 'Save Trajectory', color='lightgreen', hovercolor='green')
        self.save_btn.on_clicked(self.save_trajectory)
        
        # Clear button
        ax_clear = plt.axes([0.32, 0.04, 0.15, 0.04])
        self.clear_btn = Button(ax_clear, 'Clear Saved', color='lightcoral', hovercolor='red')
        self.clear_btn.on_clicked(self.clear_saved)
        
        # Info text
        info_text = (
            "Instructions:\n"
            "• Toggle physics model to enable/disable Magnus effect\n"
            "• Adjust sliders or type values to tune trajectory\n"
            "• Spin Rate: + = backspin (lift), - = topspin (drop)\n"
            "• Click 'Save Trajectory' to keep current arc on graph\n"
            "• Click 'Clear Saved' to remove all saved trajectories\n"
            "• Green title = Hit, Red title = Miss"
        )
        plt.figtext(0.60, 0.12, info_text, fontsize=9, 
                   bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    def update_velocity(self, val):
        self.velocity = val
        self.vel_text.set_val(f"{val:.0f}")
        self.update_plot()
    
    def update_velocity_text(self, text):
        try:
            val = float(text)
            if 50 <= val <= 600:
                self.velocity = val
                self.vel_slider.set_val(val)
                self.update_plot()
        except ValueError:
            pass
    
    def update_angle(self, val):
        self.angle = val
        self.angle_text.set_val(f"{val:.1f}")
        self.update_plot()
    
    def update_angle_text(self, text):
        try:
            val = float(text)
            if 0 <= val <= 90:
                self.angle = val
                self.angle_slider.set_val(val)
                self.update_plot()
        except ValueError:
            pass
    
    def update_height(self, val):
        self.launch_height = val
        self.height_text.set_val(f"{val:.0f}")
        self.update_plot()
    
    def update_height_text(self, text):
        try:
            val = float(text)
            if 0 <= val <= 80:
                self.launch_height = val
                self.height_slider.set_val(val)
                self.update_plot()
        except ValueError:
            pass
    
    def update_distance(self, val):
        self.distance = val
        self.dist_text.set_val(f"{val:.0f}")
        self.update_plot()
    
    def update_distance_text(self, text):
        try:
            val = float(text)
            if 50 <= val <= 400:
                self.distance = val
                self.dist_slider.set_val(val)
                self.update_plot()
        except ValueError:
            pass
    
    def update_spin(self, val):
        self.spin_rate = val
        self.spin_text.set_val(f"{val:.0f}")
        self.update_plot()
    
    def update_spin_text(self, text):
        try:
            val = float(text)
            if -6000 <= val <= 6000:
                self.spin_rate = val
                self.spin_slider.set_val(val)
                self.update_plot()
        except ValueError:
            pass

if __name__ == "__main__":
    print("Starting FRC 2026 Launcher Trajectory Tool...")
    print("=" * 60)
    print("Hub Specifications (Trapezoid/Hexagon Side Profile):")
    print(f"  - Top Height: {HUB_TOP_HEIGHT} inches ({HUB_TOP_HEIGHT/12:.1f} feet)")
    print(f"  - Bottom Height: {HUB_BOTTOM_HEIGHT} inches ({HUB_BOTTOM_HEIGHT/12:.1f} feet)")
    print(f"  - Top Width: {HUB_TOP_WIDTH} inches ({HUB_TOP_WIDTH/12:.1f} feet)")
    print(f"  - Bottom Width: {HUB_BOTTOM_WIDTH} inches ({HUB_BOTTOM_WIDTH/12:.2f} feet)")
    print("=" * 60)
    print("Use the sliders or text boxes to adjust parameters in real-time!")
    print("Save trajectories to compare different configurations.")
    print("=" * 60)
    
    app = LauncherTrajectoryTool()

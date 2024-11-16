import os
import sys
import random
import subprocess
import time

# Function to check and install required libraries
def install_and_import(package):
    try:
        __import__(package)
    except ImportError:
        print(f"Installing {package}...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Install required libraries
install_and_import("matplotlib")
install_and_import("Pillow")

# Import libraries
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from PIL import Image

# Check for the image file
image_path = 'Screenshot.png'  # Replace with your image name or full path if needed
if not os.path.exists(image_path):
    print(f"Error: File '{image_path}' not found. Please ensure the image is in the same directory as this script.")
    input("Press Enter to exit...")
    sys.exit()

# Load and resize the image
background = Image.open(image_path)
background = background.resize((1024, 768), Image.LANCZOS)

# Create the plot
fig, ax = plt.subplots(figsize=(10, 7.5))
ax.set_xlim(0, 16)  # x-axis for columns (0 to 15)
ax.set_ylim(0, 16)  # y-axis for rows (0 to 15)

# Plot the background once
ax.imshow(background, extent=[0, 16, 0, 16], aspect='auto')

# Draw the grid once
for i in range(17):  # Gridlines at each km (block)
    ax.axhline(y=i, color='black', linewidth=0.5, alpha=0.7)
    ax.axvline(x=i, color='black', linewidth=0.5, alpha=0.7)

# Label the x-axis (0 to 15) and y-axis (A to P)
ax.set_xticks(range(16))  # x-axis will show numbers 0 to 15
ax.set_xticklabels([str(i) for i in range(16)])  # Labels for the x-axis (0 to 15)
ax.set_yticks(range(16))  # 16 ticks, not 17
ax.set_yticklabels([chr(ord('A') + i) for i in range(16)])  # Labels for the y-axis (A to P)

# Define spawn areas
spawn_areas = [
    (1, 1, 7),   
    (12, 3, 14),
    (1, 9, 3),  
]

# Hotspots
hotspots = [(5, 10), (9, 5), (8, 9), (10, 2), (8, 7), (10, 15), (1, 13),(1, 8), (2, 10), (7, 13)]  # (x, y) 

# Generate initial dots
dots = []
persistent_trails = []  # List to store all trails that should persist
death_positions = []  # To store the death positions for X markers
for _ in range(60):
    area = random.choice(spawn_areas)
    x = random.uniform(area[1], area[2]) if area[0] == 1 else area[0]  # Variable x for southern spawns
    y = area[0] if area[0] == 1 else random.uniform(area[1], area[2])  # Variable y for eastern spawns
    dots.append({"x": x, "y": y, "trail": [(x, y)], "last_death": None, "death_time": None})  # Add death_time

# The goal position (1, P) corresponds to (x = 1, y = 15)
goal_x, goal_y = 1, 15

# Function to move dots toward a target
def move_toward_target(dot, target_x, target_y):
    dx = target_x - dot["x"]
    dy = target_y - dot["y"]
    distance = (dx**2 + dy**2)**0.5
    if distance > 0:  # Avoid division by zero
        step = random.uniform(.5, .5)  # Control movement speed (500m movements)
        dot["x"] += step * (dx / distance)
        dot["y"] += step * (dy / distance)
    return dot

# Function to check if two dots are close enough to collide (within 100m)
def is_close(dot1, dot2):
    distance = ((dot1["x"] - dot2["x"]) ** 2 + (dot1["y"] - dot2["y"]) ** 2) ** 0.5
    return distance < 0.2  # If the distance is less than 0.2 km (200 meters)

# Function to check if a dot is within 700m (0.7 km) of a hotspot
def is_near_hotspot(dot, hotspot, radius=0.7):
    distance = ((dot["x"] - hotspot[0]) ** 2 + (dot["y"] - hotspot[1]) ** 2) ** 0.7
    return distance <= radius

# Function to update the simulation
def update(frame):
    global dots, persistent_trails, death_positions
    # Draw only the dynamic elements to optimize performance
    ax.clear()

    # Redraw the background and grid (static elements)
    ax.imshow(background, extent=[0, 16, 0, 16], aspect='auto')

    # Redraw grid lines
    for i in range(17):
        ax.axhline(y=i, color='black', linewidth=0.5, alpha=0.7)
        ax.axvline(x=i, color='black', linewidth=0.5, alpha=0.7)

    # Re-add the labels from A to P along the y-axis
    ax.set_yticks(range(16))
    ax.set_yticklabels([chr(ord('A') + i) for i in range(16)])

    # Re-add the labels from 0 to 15 along the x-axis
    ax.set_xticks(range(16))
    ax.set_xticklabels([str(i) for i in range(16)])

    # Draw persistent trails with 40% opacity
    for trail in persistent_trails:
        trail_x, trail_y = zip(*trail)
        ax.plot(trail_x, trail_y, color="red", linewidth=2, alpha=0.10)  # Trails with 40% opacity

    # Draw death markers (X) for dead dots (purple X with 20% opacity)
    for death_pos in death_positions:
        ax.plot(death_pos[0], death_pos[1], "X", color='purple', markersize=4, alpha=0.40)

    # Update dots and draw them
    new_dots = []
    current_time = time.time()  # Current time to check for death timeout
    for dot in dots:
        # Skip dead dots that haven't respawned yet (25 seconds timeout)
        if dot["death_time"] is not None and current_time - dot["death_time"] < 25:  # 25 seconds death timeout
            continue  # Do not draw the dot if it's still dead
        
        # 3% chance of random death
        if random.random() < 0.03:  
            persistent_trails.append(dot["trail"])  # Preserve the trail
            death_positions.append(dot["trail"][-1])  # Mark the death position with an X
            dot["last_death"] = (dot["x"], dot["y"])  # Record last death location
            dot["death_time"] = current_time  # Set the death time
            continue  # Do not draw the dead dot

        # 50% chance of dying when close to another dot (within 100 meters)
        for other_dot in dots:
            if other_dot != dot and is_close(dot, other_dot) and random.random() < 0.5:
                persistent_trails.append(dot["trail"])  # Preserve the trail
                death_positions.append(dot["trail"][-1])  # Mark the death position with an X
                dot["last_death"] = (dot["x"], dot["y"])  # Record last death location
                dot["death_time"] = current_time  # Set the death time
                break  # Do not draw the dead dot
        
        # If the dot is alive, move it toward a target
        if dot["death_time"] is None or current_time - dot["death_time"] >= 5:  # Only move if not dead or respawned
            visited_hotspots = []
            while random.random() < 0.60 and len(visited_hotspots) < len(hotspots):  # 60% chance to visit any hotspot
                hotspot = random.choice(hotspots)
                if hotspot not in visited_hotspots:
                    visited_hotspots.append(hotspot)
            
            # If hotspots are visited, target the last visited one, otherwise move to the goal
            if visited_hotspots:
                target_x, target_y = visited_hotspots[-1]
            else:
                target_x, target_y = goal_x, goal_y

            # Move dot toward the target
            dot = move_toward_target(dot, target_x, target_y)

            # Check if dot is near a hotspot (within 500m)
            for hotspot in hotspots:
                if is_near_hotspot(dot, hotspot):
                    if hotspot not in visited_hotspots:
                        visited_hotspots.append(hotspot)

            # Save the trail
            dot["trail"].append((dot["x"], dot["y"]))

        new_dots.append(dot)

    # Handle respawning of dead dots after 25 seconds
    while len(new_dots) < 60:  # Keep 60 dots alive
        area = random.choice(spawn_areas)
        x = random.uniform(area[1], area[2]) if area[0] == 1 else area[0]  # Variable x for southern spawns
        y = area[0] if area[0] == 1 else random.uniform(area[1], area[2])  # Variable y for eastern spawns
        new_dot = {"x": x, "y": y, "trail": [(x, y)], "last_death": None, "death_time": None}  # Respawn a new dot
        new_dots.append(new_dot)

    dots = new_dots

    # Draw the dots and their trails
    for dot in dots:
        trail_x, trail_y = zip(*dot["trail"])
        ax.plot(trail_x, trail_y, color="blue", linewidth=0.5, alpha=0.6)  # Trails with 40% opacity
        if dot["death_time"] is None or current_time - dot["death_time"] >= 25:  # Only draw if alive
            ax.plot(dot["x"], dot["y"], "ro", markersize=4)

    # Stop simulation after 10 minutes
    if frame >= 200:
        ax.text(7, 16, "Sim Finished", color='black', fontsize=12, ha='center')
        plt.draw()

# Use FuncAnimation for smooth updates
ani = FuncAnimation(fig, update, frames=200, interval=300)

# Show the plot
plt.show()

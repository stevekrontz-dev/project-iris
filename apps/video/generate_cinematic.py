#!/usr/bin/env python3
"""
IRIS Cinematic Demo - Photorealistic Version
Uses real iris photography with animated network overlays
90 seconds, 1920x1080 @ 30fps
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance
import os
import math
from pathlib import Path

# ============================================================================
# CONFIGURATION
# ============================================================================

WIDTH, HEIGHT = 1920, 1080
FPS = 30
TOTAL_DURATION = 90

# KSU Brand Colors
KSU_GOLD = (253, 187, 48)
KSU_BLACK = (11, 19, 21)
WHITE = (255, 255, 255)
CYAN = (0, 220, 255)
WARM_WHITE = (255, 248, 240)

# Paths
SCRIPT_DIR = Path(__file__).parent
ASSETS_DIR = SCRIPT_DIR / "assets"
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "docs" / "videos"
FRAMES_DIR = SCRIPT_DIR / "frames_cinematic"
OUTPUT_FILE = OUTPUT_DIR / "iris-demo-cinematic.mp4"
IRIS_IMAGE = ASSETS_DIR / "iris_photo.jpg"

# Scene timings
SCENES = {
    'opening': (0, 8),           # Fade in on iris, title
    'zoom_to_iris': (8, 18),     # Slow zoom into iris, nodes appear
    'network_emerge': (18, 35),  # Network emerges from iris fibers
    'pulse_discovery': (35, 50), # AI discovery pulses through network
    'connections': (50, 65),     # Connections form, matches revealed
    'pull_back': (65, 78),       # Pull back to full iris with network
    'finale': (78, 90),          # Stats, tagline, fade
}

NUM_NODES = 1289

# ============================================================================
# UTILITIES
# ============================================================================

def ease_in_out_cubic(t):
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2

def ease_out_expo(t):
    return 1 if t == 1 else 1 - pow(2, -10 * t)

def ease_in_quad(t):
    return t * t

def lerp(a, b, t):
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def get_font(size, bold=False):
    try:
        fonts = [
            "C:/Windows/Fonts/segoeuil.ttf",  # Segoe UI Light
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
        ]
        if bold:
            fonts = [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
            ] + fonts
        for f in fonts:
            if os.path.exists(f):
                return ImageFont.truetype(f, size)
    except:
        pass
    return ImageFont.load_default()

# ============================================================================
# IRIS IMAGE PROCESSING
# ============================================================================

class IrisProcessor:
    def __init__(self, image_path):
        self.original = Image.open(image_path).convert('RGB')
        self.width, self.height = self.original.size

        # Find iris center (approximate - the eye is roughly centered)
        # In this image, the iris is slightly left of center
        self.iris_center = (int(self.width * 0.42), int(self.height * 0.48))
        self.iris_radius = int(min(self.width, self.height) * 0.18)
        self.pupil_radius = int(self.iris_radius * 0.35)

    def get_frame(self, zoom=1.0, offset=(0, 0), brightness=1.0, contrast=1.0):
        """Get a processed frame of the iris at given zoom and offset"""
        img = self.original.copy()

        # Apply color adjustments
        if brightness != 1.0:
            enhancer = ImageEnhance.Brightness(img)
            img = enhancer.enhance(brightness)
        if contrast != 1.0:
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(contrast)

        # Calculate crop for zoom effect
        if zoom != 1.0:
            new_w = int(self.width / zoom)
            new_h = int(self.height / zoom)

            # Center on iris with offset
            cx = self.iris_center[0] + offset[0]
            cy = self.iris_center[1] + offset[1]

            left = max(0, cx - new_w // 2)
            top = max(0, cy - new_h // 2)
            right = min(self.width, left + new_w)
            bottom = min(self.height, top + new_h)

            # Adjust if we hit edges
            if right - left < new_w:
                left = max(0, right - new_w)
            if bottom - top < new_h:
                top = max(0, bottom - new_h)

            img = img.crop((left, top, right, bottom))

        # Resize to output dimensions
        img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)

        return img

    def get_iris_node_positions(self, n_nodes, zoom=1.0, offset=(0, 0)):
        """Generate node positions that follow the iris fiber structure"""
        positions = []

        # Transform iris center based on zoom
        # When zoomed, the iris center moves toward screen center
        base_cx = WIDTH // 2
        base_cy = HEIGHT // 2

        # Iris radius in screen space
        screen_radius = self.iris_radius * zoom * (HEIGHT / self.height)
        pupil_screen_radius = self.pupil_radius * zoom * (HEIGHT / self.height)

        # Generate positions in concentric rings following iris structure
        np.random.seed(42)

        # Iris has radial fibers - place nodes along these
        num_rays = 60  # Number of radial "fibers"
        nodes_per_ring = [30, 50, 70, 90, 110, 130, 150, 170, 180, 200, 189]

        ring_radii = np.linspace(pupil_screen_radius * 1.1, screen_radius * 0.95, len(nodes_per_ring))

        node_idx = 0
        for ring_idx, (radius, count) in enumerate(zip(ring_radii, nodes_per_ring)):
            if node_idx >= n_nodes:
                break

            for i in range(count):
                if node_idx >= n_nodes:
                    break

                # Base angle with slight offset per ring
                angle = (2 * math.pi * i / count) + (ring_idx * 0.1)

                # Add organic variation
                angle_jitter = np.random.normal(0, 0.03)
                radius_jitter = np.random.normal(0, radius * 0.05)

                r = radius + radius_jitter
                a = angle + angle_jitter

                x = base_cx + r * math.cos(a)
                y = base_cy + r * math.sin(a)

                positions.append((x, y, ring_idx / len(nodes_per_ring)))  # Include depth
                node_idx += 1

        # Fill remaining with scattered positions in iris
        while len(positions) < n_nodes:
            angle = np.random.random() * 2 * math.pi
            r = pupil_screen_radius * 1.1 + np.random.random() * (screen_radius * 0.85 - pupil_screen_radius * 1.1)
            x = base_cx + r * math.cos(angle)
            y = base_cy + r * math.sin(angle)
            positions.append((x, y, np.random.random()))

        return positions[:n_nodes]

# ============================================================================
# SCENE RENDERERS
# ============================================================================

def render_opening(iris: IrisProcessor, frame_num, total_frames):
    """Opening: Fade from black, reveal iris, title appears"""
    progress = frame_num / total_frames

    # Subtle zoom during opening
    zoom = 1.0 + progress * 0.1

    # Get base iris image
    fade = ease_in_out_cubic(min(progress * 1.5, 1.0))
    img = iris.get_frame(zoom=zoom, brightness=0.9 + progress * 0.1)

    # Fade from black
    if fade < 1.0:
        black = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
        img = Image.blend(black, img, fade)

    draw = ImageDraw.Draw(img)

    # Title appears
    if progress > 0.3:
        title_fade = ease_in_out_cubic(min((progress - 0.3) / 0.4, 1.0))

        # "IRIS" - large, elegant
        font_title = get_font(120, bold=True)
        title = "IRIS"
        bbox = draw.textbbox((0, 0), title, font=font_title)
        title_w = bbox[2] - bbox[0]

        # Position at bottom third
        title_x = WIDTH // 2 - title_w // 2
        title_y = HEIGHT - 280

        # Glow effect
        for offset in range(8, 0, -2):
            glow_alpha = int(255 * title_fade * 0.15 * (offset / 8))
            glow_color = (*KSU_GOLD, glow_alpha)
            # Simulate glow with multiple draws
            for dx in [-offset, 0, offset]:
                for dy in [-offset, 0, offset]:
                    draw.text((title_x + dx, title_y + dy), title,
                             fill=lerp_color(KSU_BLACK, KSU_GOLD, title_fade * 0.3), font=font_title)

        draw.text((title_x, title_y), title, fill=lerp_color(KSU_BLACK, KSU_GOLD, title_fade), font=font_title)

        # Subtitle
        if progress > 0.5:
            sub_fade = ease_in_out_cubic(min((progress - 0.5) / 0.3, 1.0))
            font_sub = get_font(32)
            subtitle = "Intelligent Research Information System"
            bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
            sub_w = bbox[2] - bbox[0]
            sub_color = lerp_color(KSU_BLACK, WARM_WHITE, sub_fade * 0.9)
            draw.text((WIDTH // 2 - sub_w // 2, title_y + 130), subtitle, fill=sub_color, font=font_sub)

    return img

def render_zoom_to_iris(iris: IrisProcessor, frame_num, total_frames):
    """Zoom into the iris, first nodes appear"""
    progress = frame_num / total_frames
    eased = ease_in_out_cubic(progress)

    # Zoom from 1.1 to 2.5
    zoom = 1.1 + eased * 1.4

    img = iris.get_frame(zoom=zoom, brightness=0.95, contrast=1.05)
    draw = ImageDraw.Draw(img)

    # Nodes start appearing
    if progress > 0.3:
        node_progress = (progress - 0.3) / 0.7
        positions = iris.get_iris_node_positions(NUM_NODES, zoom=zoom)

        # Only show a portion of nodes, fading in
        visible_nodes = int(node_progress * 200)

        for i in range(min(visible_nodes, len(positions))):
            x, y, depth = positions[i]

            # Stagger appearance
            node_fade = min(1, (node_progress - i / 500) * 3)
            if node_fade <= 0:
                continue

            # Size based on depth and fade
            size = int(2 + depth * 2 + node_fade * 2)

            # Color: cyan for early nodes transitioning to gold
            color = lerp_color(CYAN, KSU_GOLD, node_fade * 0.7)

            # Glow effect for brighter nodes
            if node_fade > 0.5:
                for r in range(size + 4, size, -1):
                    glow_color = tuple(int(c * 0.3 * (r - size) / 4) for c in color)
                    draw.ellipse([x - r, y - r, x + r, y + r], fill=glow_color)

            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Text: "1,289 Researchers"
    if progress > 0.7:
        text_fade = ease_in_out_cubic((progress - 0.7) / 0.25)
        font = get_font(28)
        text = "Mapping 1,289 Researchers..."
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, WARM_WHITE, text_fade * 0.8)
        draw.text((WIDTH // 2 - text_w // 2, HEIGHT - 80), text, fill=color, font=font)

    return img

def render_network_emerge(iris: IrisProcessor, frame_num, total_frames):
    """Network fully emerges from iris structure"""
    progress = frame_num / total_frames
    eased = ease_out_expo(progress)

    # Hold zoom at 2.5, slight movement
    zoom = 2.5 + math.sin(frame_num * 0.02) * 0.05

    img = iris.get_frame(zoom=zoom, brightness=0.92, contrast=1.08)
    draw = ImageDraw.Draw(img)

    positions = iris.get_iris_node_positions(NUM_NODES, zoom=zoom)

    # All nodes visible now, connections forming
    visible_nodes = int(200 + eased * (NUM_NODES - 200))

    # Generate connections
    np.random.seed(123)
    connections = []
    for _ in range(int(eased * 300)):
        i = np.random.randint(0, min(visible_nodes, len(positions)))
        j = np.random.randint(0, min(visible_nodes, len(positions)))
        if i != j:
            x1, y1, _ = positions[i]
            x2, y2, _ = positions[j]
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < 80:
                connections.append((i, j, 0.3 + np.random.random() * 0.7))

    # Draw connections first
    for i, j, strength in connections:
        x1, y1, _ = positions[i]
        x2, y2, _ = positions[j]

        conn_alpha = eased * strength * 0.6
        color = lerp_color(KSU_BLACK, KSU_GOLD, conn_alpha)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    # Draw nodes
    pulse = (math.sin(frame_num * 0.1) + 1) / 2

    for i in range(min(visible_nodes, len(positions))):
        x, y, depth = positions[i]

        # Vary size with pulse
        size = int(2 + depth * 3 + pulse * 1)

        # Color variation
        intensity = 0.5 + depth * 0.3 + pulse * 0.2
        color = lerp_color((100, 100, 100), KSU_GOLD, intensity)

        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Text overlay
    font = get_font(36, bold=True)
    text = "Research Network"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]

    text_alpha = 0.7 + pulse * 0.2
    color = lerp_color(KSU_BLACK, WARM_WHITE, text_alpha)
    draw.text((WIDTH // 2 - text_w // 2, 50), text, fill=color, font=font)

    return img

def render_pulse_discovery(iris: IrisProcessor, frame_num, total_frames):
    """AI discovery pulses through the network"""
    progress = frame_num / total_frames

    zoom = 2.5 + math.sin(frame_num * 0.015) * 0.1

    img = iris.get_frame(zoom=zoom, brightness=0.88, contrast=1.1)
    draw = ImageDraw.Draw(img)

    positions = iris.get_iris_node_positions(NUM_NODES, zoom=zoom)

    # Pulse wave expanding from center
    wave_radius = progress * 600
    wave_width = 80

    # Generate connections
    np.random.seed(123)
    connections = []
    for _ in range(400):
        i = np.random.randint(0, len(positions))
        j = np.random.randint(0, len(positions))
        if i != j:
            x1, y1, _ = positions[i]
            x2, y2, _ = positions[j]
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < 100:
                connections.append((i, j, 0.3 + np.random.random() * 0.7))

    center = (WIDTH // 2, HEIGHT // 2)

    # Draw connections with pulse effect
    for i, j, strength in connections:
        x1, y1, _ = positions[i]
        x2, y2, _ = positions[j]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2

        dist_from_center = math.sqrt((mx - center[0]) ** 2 + (my - center[1]) ** 2)

        # Pulse intensity
        wave_dist = abs(dist_from_center - wave_radius)
        wave_intensity = max(0, 1 - wave_dist / wave_width) if wave_dist < wave_width else 0

        base_alpha = 0.2 + wave_intensity * 0.6
        color = lerp_color(KSU_BLACK, KSU_GOLD, base_alpha * strength)
        width = 1 + int(wave_intensity * 2)

        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    # Draw nodes with pulse
    for i, (x, y, depth) in enumerate(positions):
        dist_from_center = math.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)

        wave_dist = abs(dist_from_center - wave_radius)
        wave_intensity = max(0, 1 - wave_dist / wave_width) if wave_dist < wave_width else 0

        size = int(2 + depth * 2 + wave_intensity * 4)
        intensity = 0.3 + wave_intensity * 0.7
        color = lerp_color((80, 80, 80), KSU_GOLD, intensity)

        # Extra glow for pulsed nodes
        if wave_intensity > 0.5:
            for r in range(size + 6, size, -2):
                glow_alpha = (r - size) / 6 * wave_intensity * 0.4
                glow_color = tuple(int(c * glow_alpha) for c in KSU_GOLD)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=glow_color)

        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # "AI-Powered Discovery" text
    font = get_font(40, bold=True)
    text = "AI-Powered Discovery"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]

    pulse_text = (math.sin(frame_num * 0.08) + 1) / 2
    color = lerp_color((100, 80, 30), KSU_GOLD, 0.6 + pulse_text * 0.4)
    draw.text((WIDTH // 2 - text_w // 2, 50), text, fill=color, font=font)

    # Subtitle
    font_sub = get_font(24)
    sub = "Analyzing research synergies across disciplines"
    bbox = draw.textbbox((0, 0), sub, font=font_sub)
    sub_w = bbox[2] - bbox[0]
    draw.text((WIDTH // 2 - sub_w // 2, HEIGHT - 70), sub, fill=lerp_color(KSU_BLACK, WARM_WHITE, 0.7), font=font_sub)

    return img

def render_connections(iris: IrisProcessor, frame_num, total_frames):
    """Connections form, match scores revealed"""
    progress = frame_num / total_frames

    zoom = 2.3 + math.sin(frame_num * 0.01) * 0.1

    img = iris.get_frame(zoom=zoom, brightness=0.9, contrast=1.05)
    draw = ImageDraw.Draw(img)

    positions = iris.get_iris_node_positions(NUM_NODES, zoom=zoom)

    # Define some "match" connections to highlight
    highlighted_matches = [
        (50, 120, 0.94, "Machine Learning × Genomics"),
        (200, 350, 0.89, "Data Science × Neuroscience"),
        (400, 520, 0.91, "AI Ethics × Philosophy"),
        (80, 180, 0.87, "Climate × Economics"),
    ]

    # Draw regular connections
    np.random.seed(123)
    for _ in range(300):
        i = np.random.randint(0, len(positions))
        j = np.random.randint(0, len(positions))
        if i != j:
            x1, y1, _ = positions[i]
            x2, y2, _ = positions[j]
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < 80:
                color = lerp_color(KSU_BLACK, KSU_GOLD, 0.25)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    # Draw all nodes
    pulse = (math.sin(frame_num * 0.12) + 1) / 2

    for x, y, depth in positions:
        size = int(2 + depth * 2)
        color = lerp_color((80, 80, 80), KSU_GOLD, 0.4 + depth * 0.2)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Draw highlighted matches with animation
    for idx, (i, j, score, label) in enumerate(highlighted_matches):
        match_delay = idx * 0.2
        if progress < match_delay:
            continue

        match_progress = min(1, (progress - match_delay) / 0.25)
        match_eased = ease_out_expo(match_progress)

        if i >= len(positions) or j >= len(positions):
            continue

        x1, y1, _ = positions[i]
        x2, y2, _ = positions[j]

        # Bright connection line
        for w in range(6, 0, -1):
            alpha = (6 - w) / 6 * match_eased * 0.6
            color = lerp_color(KSU_BLACK, KSU_GOLD, alpha)
            draw.line([(x1, y1), (x2, y2)], fill=color, width=w)

        # Bright endpoint nodes
        for x, y in [(x1, y1), (x2, y2)]:
            glow_size = int(8 + pulse * 4)
            for r in range(glow_size, 0, -2):
                alpha = r / glow_size * match_eased * 0.5
                glow_color = tuple(int(c * alpha) for c in KSU_GOLD)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=glow_color)
            draw.ellipse([x - 4, y - 4, x + 4, y + 4], fill=KSU_GOLD)

        # Score badge
        if match_progress > 0.5:
            badge_alpha = (match_progress - 0.5) / 0.5
            mx, my = (x1 + x2) / 2, (y1 + y2) / 2 - 20

            font_badge = get_font(16, bold=True)
            score_text = f"{int(score * 100)}%"

            # Badge background
            badge_color = lerp_color(KSU_BLACK, KSU_GOLD, badge_alpha * 0.9)
            draw.ellipse([mx - 18, my - 10, mx + 18, my + 10], fill=badge_color)

            bbox = draw.textbbox((0, 0), score_text, font=font_badge)
            tw = bbox[2] - bbox[0]
            draw.text((mx - tw // 2, my - 7), score_text, fill=KSU_BLACK, font=font_badge)

    # Title
    font = get_font(36, bold=True)
    text = "Discovering Connections"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    draw.text((WIDTH // 2 - text_w // 2, 50), text, fill=lerp_color(KSU_BLACK, WARM_WHITE, 0.85), font=font)

    return img

def render_pull_back(iris: IrisProcessor, frame_num, total_frames):
    """Pull back to show full network on iris"""
    progress = frame_num / total_frames
    eased = ease_in_out_cubic(progress)

    # Zoom out from 2.3 to 1.2
    zoom = 2.3 - eased * 1.1

    img = iris.get_frame(zoom=zoom, brightness=0.95, contrast=1.02)
    draw = ImageDraw.Draw(img)

    positions = iris.get_iris_node_positions(NUM_NODES, zoom=zoom)

    # Draw all connections
    np.random.seed(123)
    pulse = (math.sin(frame_num * 0.08) + 1) / 2

    for _ in range(500):
        i = np.random.randint(0, len(positions))
        j = np.random.randint(0, len(positions))
        if i != j:
            x1, y1, _ = positions[i]
            x2, y2, _ = positions[j]
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            # Connection distance threshold scales with zoom
            max_dist = 50 + (1 - eased) * 50
            if dist < max_dist:
                alpha = 0.2 + pulse * 0.15
                color = lerp_color(KSU_BLACK, KSU_GOLD, alpha)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    # Draw nodes
    for x, y, depth in positions:
        size = int(1 + depth * 2 + (1 - eased) * 2)
        intensity = 0.4 + depth * 0.3 + pulse * 0.15
        color = lerp_color((60, 60, 60), KSU_GOLD, intensity)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Stats appearing
    if progress > 0.5:
        stats_fade = ease_in_out_cubic((progress - 0.5) / 0.4)

        font = get_font(48, bold=True)
        font_sub = get_font(24)

        stats = [
            ("1,289", "Researchers"),
            ("47", "Departments"),
            ("∞", "Possibilities"),
        ]

        y_pos = HEIGHT - 180
        spacing = WIDTH // 4

        for i, (value, label) in enumerate(stats):
            x = spacing * (i + 1)

            # Stagger appearance
            stat_delay = i * 0.1
            if (progress - 0.5) / 0.4 < stat_delay:
                continue
            stat_alpha = min(1, ((progress - 0.5) / 0.4 - stat_delay) * 2)

            # Value
            bbox = draw.textbbox((0, 0), value, font=font)
            vw = bbox[2] - bbox[0]
            color = lerp_color(KSU_BLACK, KSU_GOLD, stat_alpha)
            draw.text((x - vw // 2, y_pos), value, fill=color, font=font)

            # Label
            bbox = draw.textbbox((0, 0), label, font=font_sub)
            lw = bbox[2] - bbox[0]
            color = lerp_color(KSU_BLACK, WARM_WHITE, stat_alpha * 0.7)
            draw.text((x - lw // 2, y_pos + 55), label, fill=color, font=font_sub)

    return img

def render_finale(iris: IrisProcessor, frame_num, total_frames):
    """Final stats, tagline, fade out"""
    progress = frame_num / total_frames

    zoom = 1.2 + math.sin(frame_num * 0.01) * 0.02

    img = iris.get_frame(zoom=zoom, brightness=0.9 + progress * 0.1, contrast=1.0)
    draw = ImageDraw.Draw(img)

    positions = iris.get_iris_node_positions(NUM_NODES, zoom=zoom)

    # Subtle network overlay
    pulse = (math.sin(frame_num * 0.06) + 1) / 2

    np.random.seed(123)
    for _ in range(400):
        i = np.random.randint(0, len(positions))
        j = np.random.randint(0, len(positions))
        if i != j:
            x1, y1, _ = positions[i]
            x2, y2, _ = positions[j]
            dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
            if dist < 60:
                alpha = 0.15 + pulse * 0.1
                color = lerp_color(KSU_BLACK, KSU_GOLD, alpha)
                draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    for x, y, depth in positions:
        size = int(1 + depth * 1.5)
        intensity = 0.35 + depth * 0.2 + pulse * 0.1
        color = lerp_color((50, 50, 50), KSU_GOLD, intensity)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Impact metrics
    metrics = [
        ("3-5×", "Higher Grant Success"),
        ("67%", "More Cross-Disciplinary Research"),
        ("100%", "Data Privacy Preserved"),
    ]

    y_start = 200
    y_spacing = 180

    for i, (value, label) in enumerate(metrics):
        metric_delay = i * 0.12
        if progress < metric_delay:
            continue

        metric_progress = min(1, (progress - metric_delay) / 0.2)
        metric_eased = ease_out_expo(metric_progress)

        y = y_start + i * y_spacing

        # Value (large)
        font_value = get_font(72, bold=True)
        bbox = draw.textbbox((0, 0), value, font=font_value)
        vw = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, KSU_GOLD, metric_eased)
        draw.text((WIDTH // 2 - vw // 2, y), value, fill=color, font=font_value)

        # Label
        font_label = get_font(28)
        bbox = draw.textbbox((0, 0), label, font=font_label)
        lw = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, WARM_WHITE, metric_eased * 0.85)
        draw.text((WIDTH // 2 - lw // 2, y + 75), label, fill=color, font=font_label)

    # Final tagline
    if progress > 0.6:
        tagline_fade = ease_in_out_cubic((progress - 0.6) / 0.25)

        font_tag = get_font(36, bold=True)
        tagline = "The Future of Research Collaboration"
        bbox = draw.textbbox((0, 0), tagline, font=font_tag)
        tw = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, KSU_GOLD, tagline_fade)
        draw.text((WIDTH // 2 - tw // 2, HEIGHT - 120), tagline, fill=color, font=font_tag)

        font_ksu = get_font(24)
        ksu_text = "Kennesaw State University"
        bbox = draw.textbbox((0, 0), ksu_text, font=font_ksu)
        kw = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, WARM_WHITE, tagline_fade * 0.6)
        draw.text((WIDTH // 2 - kw // 2, HEIGHT - 70), ksu_text, fill=color, font=font_ksu)

    # Fade to black at end
    if progress > 0.9:
        fade = (progress - 0.9) / 0.1
        black = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
        img = Image.blend(img, black, fade)

    return img

# ============================================================================
# MAIN
# ============================================================================

def render_video():
    print("=" * 60)
    print("IRIS Cinematic Demo - Photorealistic Version")
    print("=" * 60)

    # Initialize iris processor
    if not IRIS_IMAGE.exists():
        print(f"ERROR: Iris image not found at {IRIS_IMAGE}")
        return

    print(f"Loading iris image: {IRIS_IMAGE}")
    iris = IrisProcessor(IRIS_IMAGE)
    print(f"  Image size: {iris.width}x{iris.height}")
    print(f"  Iris center: {iris.iris_center}")
    print(f"  Iris radius: {iris.iris_radius}")

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    total_frames = TOTAL_DURATION * FPS

    scene_renderers = {
        'opening': render_opening,
        'zoom_to_iris': render_zoom_to_iris,
        'network_emerge': render_network_emerge,
        'pulse_discovery': render_pulse_discovery,
        'connections': render_connections,
        'pull_back': render_pull_back,
        'finale': render_finale,
    }

    print(f"\nRendering {total_frames} frames...")
    print(f"Output: {OUTPUT_FILE}")

    frames = []

    for frame_num in range(total_frames):
        current_time = frame_num / FPS

        # Find current scene
        current_scene = None
        scene_start = 0
        scene_end = 0

        for scene_name, (start, end) in SCENES.items():
            if start <= current_time < end:
                current_scene = scene_name
                scene_start = start
                scene_end = end
                break

        if current_scene is None:
            current_scene = 'finale'
            scene_start, scene_end = SCENES[current_scene]

        # Calculate scene-relative frame
        scene_duration = scene_end - scene_start
        scene_frame = int((current_time - scene_start) * FPS)
        scene_total = int(scene_duration * FPS)

        # Render frame
        renderer = scene_renderers[current_scene]
        frame = renderer(iris, scene_frame, scene_total)

        # Save frame
        frame_path = FRAMES_DIR / f"frame_{frame_num:05d}.png"
        frame.save(frame_path, "PNG")

        if frame_num % (FPS * 5) == 0:
            pct = (frame_num / total_frames) * 100
            print(f"  {pct:.1f}% - {current_scene}")

    print("\nFrames complete. Generating audio...")

    # Generate ambient audio
    samples = int(TOTAL_DURATION * 44100)
    t = np.linspace(0, TOTAL_DURATION, samples)

    # Deep, cinematic drone
    audio = 0.12 * np.sin(2 * np.pi * 55 * t)  # A1
    audio += 0.08 * np.sin(2 * np.pi * 82.5 * t)  # E2
    audio += 0.06 * np.sin(2 * np.pi * 110 * t)  # A2
    audio += 0.04 * np.sin(2 * np.pi * 165 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t))
    audio += 0.03 * np.sin(2 * np.pi * 220 * t) * (0.3 + 0.3 * np.sin(2 * np.pi * 0.1 * t))

    # Subtle shimmer
    audio += 0.015 * np.sin(2 * np.pi * 440 * t) * (0.2 + 0.2 * np.sin(2 * np.pi * 0.15 * t))

    # Fade in/out
    fade_samples = int(3 * 44100)
    audio[:fade_samples] *= np.linspace(0, 1, fade_samples)
    audio[-fade_samples:] *= np.linspace(1, 0, fade_samples)

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.75

    # Save as WAV
    audio_path = FRAMES_DIR / "audio.wav"
    import wave
    stereo = np.column_stack([audio, audio])
    audio_int16 = (stereo * 32767).astype(np.int16)

    with wave.open(str(audio_path), 'w') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        wav.writeframes(audio_int16.tobytes())

    print("Encoding video with FFmpeg...")

    ffmpeg_path = r"C:\Program Files\Topaz Labs LLC\Topaz Video Enhance AI\ffmpeg.exe"

    cmd = f'"{ffmpeg_path}" -y -framerate {FPS} -i "{FRAMES_DIR}/frame_%05d.png" -i "{audio_path}" -c:v libx264 -preset slow -crf 16 -c:a aac -b:a 192k -pix_fmt yuv420p "{OUTPUT_FILE}"'

    os.system(cmd)

    print("\n" + "=" * 60)
    print("CINEMATIC VIDEO COMPLETE!")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    render_video()

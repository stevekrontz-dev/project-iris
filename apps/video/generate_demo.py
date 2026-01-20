#!/usr/bin/env python3
"""
IRIS Demo Video Generator
Creates a 90-second cinematic demonstration video for Project IRIS
1920x1080 @ 30fps with ambient audio
"""

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import sys
import math
from pathlib import Path

# Try to import moviepy components
try:
    from moviepy import ImageSequenceClip, AudioClip, CompositeAudioClip, concatenate_videoclips
    MOVIEPY_AVAILABLE = True
except ImportError:
    try:
        from moviepy.editor import ImageSequenceClip, AudioClip, CompositeAudioClip, concatenate_videoclips
        MOVIEPY_AVAILABLE = True
    except ImportError:
        MOVIEPY_AVAILABLE = False
        print("Warning: moviepy not fully available, will use ffmpeg directly")

# ============================================================================
# CONFIGURATION
# ============================================================================

WIDTH, HEIGHT = 1920, 1080
FPS = 30
TOTAL_DURATION = 90  # seconds

# KSU Brand Colors
KSU_GOLD = (253, 187, 48)       # #FDBB30
KSU_BLACK = (11, 19, 21)        # #0B1315
KSU_GOLD_DIM = (180, 133, 34)   # Dimmer gold for accents
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)

# Scene timings (in seconds)
SCENES = {
    'logo_reveal': (0, 10),
    'network_birth': (10, 25),
    'magic_moment': (25, 40),
    'ai_intelligence': (40, 55),
    'before_after': (55, 70),
    'future_vision': (70, 80),
    'impact_metrics': (80, 90),
}

# Number of researcher nodes
NUM_RESEARCHERS = 1289

# Output paths
SCRIPT_DIR = Path(__file__).parent
OUTPUT_DIR = SCRIPT_DIR.parent.parent / "docs" / "videos"
FRAMES_DIR = SCRIPT_DIR / "frames"
OUTPUT_FILE = OUTPUT_DIR / "iris-demo.mp4"

# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def ease_in_out_cubic(t):
    """Smooth easing function for animations"""
    if t < 0.5:
        return 4 * t * t * t
    return 1 - pow(-2 * t + 2, 3) / 2

def ease_out_expo(t):
    """Exponential ease out"""
    return 1 if t == 1 else 1 - pow(2, -10 * t)

def lerp(a, b, t):
    """Linear interpolation"""
    return a + (b - a) * t

def lerp_color(c1, c2, t):
    """Interpolate between two RGB colors"""
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))

def get_font(size, bold=False):
    """Get a font, falling back to default if custom fonts unavailable"""
    try:
        # Try common Windows fonts
        font_names = [
            "C:/Windows/Fonts/segoeui.ttf",
            "C:/Windows/Fonts/arial.ttf",
            "C:/Windows/Fonts/calibri.ttf",
        ]
        if bold:
            font_names = [
                "C:/Windows/Fonts/segoeuib.ttf",
                "C:/Windows/Fonts/arialbd.ttf",
                "C:/Windows/Fonts/calibrib.ttf",
            ] + font_names

        for font_path in font_names:
            if os.path.exists(font_path):
                return ImageFont.truetype(font_path, size)
    except:
        pass
    return ImageFont.load_default()

def draw_glow(draw, center, radius, color, intensity=1.0):
    """Draw a glowing circle effect"""
    x, y = center
    for i in range(int(radius), 0, -2):
        alpha = int(255 * (i / radius) * intensity * 0.3)
        glow_color = (*color, alpha)
        # Since we can't do alpha directly, we'll simulate with color blending
        fade = i / radius
        faded_color = tuple(int(c * fade * intensity) for c in color)
        draw.ellipse([x - i, y - i, x + i, y + i], fill=faded_color)

def create_iris_positions(n_nodes, center, max_radius):
    """Generate positions forming an iris/eye pattern"""
    positions = []
    cx, cy = center

    # Create concentric rings with varying densities
    rings = [
        (0.15, 50),   # Inner ring (pupil edge)
        (0.25, 80),   #
        (0.35, 120),  #
        (0.45, 150),  #
        (0.55, 180),  #
        (0.65, 200),  #
        (0.75, 220),  #
        (0.85, 180),  #
        (0.95, 119),  # Outer ring
    ]

    # Distribute nodes across rings
    total_allocated = sum(r[1] for r in rings)
    scale = n_nodes / total_allocated

    for ring_ratio, base_count in rings:
        count = int(base_count * scale)
        radius = ring_ratio * max_radius
        for i in range(count):
            angle = (2 * math.pi * i / count) + (ring_ratio * 0.5)  # Offset each ring
            # Add slight randomness for organic look
            r_jitter = radius * (1 + 0.05 * (np.random.random() - 0.5))
            a_jitter = angle + 0.02 * (np.random.random() - 0.5)
            x = cx + r_jitter * math.cos(a_jitter)
            y = cy + r_jitter * math.sin(a_jitter)
            positions.append((x, y))

    # Fill remaining with random positions in iris area
    while len(positions) < n_nodes:
        angle = np.random.random() * 2 * math.pi
        radius = np.random.random() * max_radius * 0.95
        if radius > max_radius * 0.12:  # Keep pupil clear
            x = cx + radius * math.cos(angle)
            y = cy + radius * math.sin(angle)
            positions.append((x, y))

    return positions[:n_nodes]

# ============================================================================
# SCENE GENERATORS
# ============================================================================

def generate_logo_reveal(frame_num, total_frames):
    """Scene 1: Logo Reveal (0-10s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames

    # Fade in
    fade = ease_in_out_cubic(min(progress * 2, 1.0))

    # Draw iris logo
    center_x, center_y = WIDTH // 2, HEIGHT // 2 - 50
    max_radius = 200

    if fade > 0:
        # Outer glow
        glow_intensity = fade * (0.8 + 0.2 * math.sin(frame_num * 0.1))
        for r in range(max_radius + 80, max_radius, -5):
            alpha = (r - max_radius) / 80
            glow_color = tuple(int(c * (1 - alpha) * glow_intensity * 0.3) for c in KSU_GOLD)
            draw.ellipse([center_x - r, center_y - r, center_x + r, center_y + r], fill=glow_color)

        # Iris rings
        num_rings = 8
        for i in range(num_rings):
            ring_radius = max_radius * (0.3 + 0.7 * i / num_rings)
            ring_width = 3
            # Animate rings appearing
            ring_progress = max(0, min(1, (fade - i * 0.08) * 2))
            if ring_progress > 0:
                color = lerp_color(KSU_BLACK, KSU_GOLD, ring_progress * 0.7)
                draw.ellipse(
                    [center_x - ring_radius, center_y - ring_radius,
                     center_x + ring_radius, center_y + ring_radius],
                    outline=color, width=ring_width
                )

        # Pupil (center)
        pupil_radius = max_radius * 0.25
        pupil_color = lerp_color(KSU_BLACK, (30, 30, 35), fade)
        draw.ellipse(
            [center_x - pupil_radius, center_y - pupil_radius,
             center_x + pupil_radius, center_y + pupil_radius],
            fill=pupil_color
        )

        # "IRIS" text in center
        if progress > 0.3:
            text_fade = ease_in_out_cubic(min((progress - 0.3) / 0.3, 1.0))
            font_large = get_font(72, bold=True)
            text = "IRIS"
            bbox = draw.textbbox((0, 0), text, font=font_large)
            text_w = bbox[2] - bbox[0]
            text_color = lerp_color(KSU_BLACK, KSU_GOLD, text_fade)
            draw.text((center_x - text_w // 2, center_y - 30), text, fill=text_color, font=font_large)

        # Subtitle
        if progress > 0.5:
            sub_fade = ease_in_out_cubic(min((progress - 0.5) / 0.3, 1.0))
            font_sub = get_font(28)
            subtitle = "Intelligent Research Information System"
            bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
            sub_w = bbox[2] - bbox[0]
            sub_color = lerp_color(KSU_BLACK, WHITE, sub_fade * 0.8)
            draw.text((center_x - sub_w // 2, center_y + max_radius + 60), subtitle, fill=sub_color, font=font_sub)

        # KSU text at bottom
        if progress > 0.7:
            ksu_fade = ease_in_out_cubic(min((progress - 0.7) / 0.2, 1.0))
            font_ksu = get_font(24)
            ksu_text = "Kennesaw State University"
            bbox = draw.textbbox((0, 0), ksu_text, font=font_ksu)
            ksu_w = bbox[2] - bbox[0]
            ksu_color = lerp_color(KSU_BLACK, KSU_GOLD_DIM, ksu_fade * 0.6)
            draw.text((center_x - ksu_w // 2, HEIGHT - 80), ksu_text, fill=ksu_color, font=font_ksu)

    return img

def generate_network_birth(frame_num, total_frames):
    """Scene 2: Network Birth (10-25s) - 1,289 nodes forming iris pattern"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames
    eased = ease_in_out_cubic(progress)

    center = (WIDTH // 2, HEIGHT // 2)
    max_radius = 400

    # Seed for consistent random positions
    np.random.seed(42)

    # Generate target iris positions
    target_positions = create_iris_positions(NUM_RESEARCHERS, center, max_radius)

    # Generate random starting positions (scattered)
    start_positions = []
    for _ in range(NUM_RESEARCHERS):
        x = np.random.random() * WIDTH
        y = np.random.random() * HEIGHT
        start_positions.append((x, y))

    # Draw nodes transitioning from scattered to iris
    for i in range(NUM_RESEARCHERS):
        sx, sy = start_positions[i]
        tx, ty = target_positions[i]

        # Stagger the animation per node
        node_delay = (i / NUM_RESEARCHERS) * 0.3
        node_progress = max(0, min(1, (eased - node_delay) / 0.7))
        node_eased = ease_out_expo(node_progress)

        x = lerp(sx, tx, node_eased)
        y = lerp(sy, ty, node_eased)

        # Color transition: white -> gold
        color = lerp_color(WHITE, KSU_GOLD, node_eased * 0.8)

        # Size based on progress
        size = 2 + int(node_eased * 2)

        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Draw central pupil
    if progress > 0.5:
        pupil_fade = ease_in_out_cubic((progress - 0.5) / 0.5)
        pupil_radius = max_radius * 0.12
        pupil_color = lerp_color(KSU_BLACK, (20, 25, 30), pupil_fade)
        draw.ellipse(
            [center[0] - pupil_radius, center[1] - pupil_radius,
             center[0] + pupil_radius, center[1] + pupil_radius],
            fill=pupil_color
        )

    # Title text
    if progress > 0.7:
        text_fade = ease_in_out_cubic((progress - 0.7) / 0.2)
        font = get_font(32)
        text = f"{NUM_RESEARCHERS:,} Researchers Connected"
        bbox = draw.textbbox((0, 0), text, font=font)
        text_w = bbox[2] - bbox[0]
        text_color = lerp_color(KSU_BLACK, WHITE, text_fade * 0.7)
        draw.text((WIDTH // 2 - text_w // 2, HEIGHT - 100), text, fill=text_color, font=font)

    return img

def generate_magic_moment(frame_num, total_frames):
    """Scene 3: Magic Moment - Zoom into cluster (25-40s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames

    center = (WIDTH // 2, HEIGHT // 2)

    # Zoom effect - start wide, end focused
    zoom = 1 + progress * 2  # 1x to 3x zoom

    # Focus point (upper right cluster)
    focus_x = WIDTH // 2 + 200
    focus_y = HEIGHT // 2 - 150

    np.random.seed(42)
    target_positions = create_iris_positions(NUM_RESEARCHERS, center, 400)

    # Calculate view offset based on zoom and focus
    view_offset_x = (focus_x - WIDTH // 2) * (zoom - 1) * 0.5
    view_offset_y = (focus_y - HEIGHT // 2) * (zoom - 1) * 0.5

    # Connection pairs for this cluster
    cluster_connections = [
        (45, 67, 0.92), (67, 89, 0.87), (45, 89, 0.84),
        (23, 45, 0.79), (89, 112, 0.88), (112, 134, 0.85),
        (67, 134, 0.76), (23, 112, 0.81), (45, 134, 0.73),
    ]

    # Draw all nodes (transformed by zoom)
    for i, (x, y) in enumerate(target_positions):
        # Apply zoom transformation
        zx = (x - WIDTH // 2) * zoom + WIDTH // 2 - view_offset_x
        zy = (y - HEIGHT // 2) * zoom + HEIGHT // 2 - view_offset_y

        # Check if in view
        if -50 < zx < WIDTH + 50 and -50 < zy < HEIGHT + 50:
            # Highlight nodes in focus area
            dist_to_focus = math.sqrt((x - focus_x) ** 2 + (y - focus_y) ** 2)
            in_cluster = dist_to_focus < 120

            if in_cluster:
                size = 4 + int(zoom)
                color = KSU_GOLD
            else:
                size = 2 + int(zoom * 0.5)
                color = lerp_color(GRAY, KSU_GOLD_DIM, 0.3)

            draw.ellipse([zx - size, zy - size, zx + size, zy + size], fill=color)

    # Draw connections lighting up
    if progress > 0.2:
        conn_progress = (progress - 0.2) / 0.6
        for idx, (i, j, score) in enumerate(cluster_connections):
            conn_delay = idx / len(cluster_connections)
            if conn_progress > conn_delay:
                conn_alpha = min(1, (conn_progress - conn_delay) * 3)

                x1, y1 = target_positions[i]
                x2, y2 = target_positions[j]

                # Transform
                zx1 = (x1 - WIDTH // 2) * zoom + WIDTH // 2 - view_offset_x
                zy1 = (y1 - HEIGHT // 2) * zoom + HEIGHT // 2 - view_offset_y
                zx2 = (x2 - WIDTH // 2) * zoom + WIDTH // 2 - view_offset_x
                zy2 = (y2 - HEIGHT // 2) * zoom + HEIGHT // 2 - view_offset_y

                line_color = lerp_color(KSU_BLACK, KSU_GOLD, conn_alpha * 0.8)
                draw.line([(zx1, zy1), (zx2, zy2)], fill=line_color, width=2)

    # Labels appearing
    if progress > 0.5:
        label_fade = ease_in_out_cubic((progress - 0.5) / 0.3)
        font = get_font(20)
        labels = [
            (focus_x - 80, focus_y - 60, "Dr. Smith - AI/ML"),
            (focus_x + 40, focus_y + 20, "Dr. Jones - Bioinformatics"),
            (focus_x - 20, focus_y + 80, "Dr. Chen - Data Science"),
        ]
        for lx, ly, text in labels:
            zlx = (lx - WIDTH // 2) * zoom + WIDTH // 2 - view_offset_x
            zly = (ly - HEIGHT // 2) * zoom + HEIGHT // 2 - view_offset_y
            color = lerp_color(KSU_BLACK, WHITE, label_fade * 0.9)
            draw.text((zlx, zly), text, fill=color, font=font)

    # Match score badges
    if progress > 0.7:
        badge_fade = ease_in_out_cubic((progress - 0.7) / 0.2)
        font_badge = get_font(18, bold=True)
        badges = [
            (focus_x - 30, focus_y - 30, "92%"),
            (focus_x + 60, focus_y + 50, "87%"),
        ]
        for bx, by, score in badges:
            zbx = (bx - WIDTH // 2) * zoom + WIDTH // 2 - view_offset_x
            zby = (by - HEIGHT // 2) * zoom + HEIGHT // 2 - view_offset_y
            # Badge background
            badge_color = lerp_color(KSU_BLACK, KSU_GOLD, badge_fade)
            draw.ellipse([zbx - 20, zby - 12, zbx + 20, zby + 12], fill=badge_color)
            # Score text
            draw.text((zbx - 12, zby - 8), score, fill=KSU_BLACK, font=font_badge)

    return img

def generate_ai_intelligence(frame_num, total_frames):
    """Scene 4: AI Intelligence - Pulsing connections (40-55s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames
    pulse = (math.sin(frame_num * 0.15) + 1) / 2  # Pulsing effect

    center = (WIDTH // 2, HEIGHT // 2)
    np.random.seed(42)
    positions = create_iris_positions(NUM_RESEARCHERS, center, 380)

    # Generate connections
    np.random.seed(123)
    connections = []
    for _ in range(200):
        i = np.random.randint(0, len(positions))
        j = np.random.randint(0, len(positions))
        if i != j:
            dist = math.sqrt((positions[i][0] - positions[j][0]) ** 2 +
                           (positions[i][1] - positions[j][1]) ** 2)
            if dist < 150:
                connections.append((i, j, 0.5 + np.random.random() * 0.5))

    # Draw pulsing connections
    wave_center = progress * 800  # Expanding wave

    for i, j, strength in connections:
        x1, y1 = positions[i]
        x2, y2 = positions[j]
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2

        # Distance from center for wave effect
        dist_from_center = math.sqrt((mx - center[0]) ** 2 + (my - center[1]) ** 2)

        # Wave intensity
        wave_dist = abs(dist_from_center - wave_center)
        wave_intensity = max(0, 1 - wave_dist / 100) if wave_dist < 100 else 0

        base_intensity = 0.3 + wave_intensity * 0.7 + pulse * 0.2 * strength

        color = lerp_color(KSU_BLACK, KSU_GOLD, base_intensity * strength)
        width = 1 + int(wave_intensity * 2)
        draw.line([(x1, y1), (x2, y2)], fill=color, width=width)

    # Draw nodes
    for i, (x, y) in enumerate(positions):
        dist_from_center = math.sqrt((x - center[0]) ** 2 + (y - center[1]) ** 2)
        wave_dist = abs(dist_from_center - wave_center)
        wave_intensity = max(0, 1 - wave_dist / 80) if wave_dist < 80 else 0

        size = 3 + int(wave_intensity * 3)
        intensity = 0.5 + wave_intensity * 0.5 + pulse * 0.2
        color = lerp_color(GRAY, KSU_GOLD, intensity)
        draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # "Spinout Potential" highlights
    spinout_nodes = [100, 250, 400, 600, 800, 1000]
    for node_idx in spinout_nodes:
        if node_idx < len(positions):
            x, y = positions[node_idx]
            glow_size = 15 + int(pulse * 10)
            for r in range(glow_size, 0, -3):
                alpha = r / glow_size
                glow_color = tuple(int(c * alpha * 0.4) for c in KSU_GOLD)
                draw.ellipse([x - r, y - r, x + r, y + r], fill=glow_color)
            draw.ellipse([x - 5, y - 5, x + 5, y + 5], fill=KSU_GOLD)

    # Text overlay
    font = get_font(36, bold=True)
    text = "AI-Powered Discovery"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_alpha = 0.7 + pulse * 0.3
    text_color = lerp_color(KSU_BLACK, KSU_GOLD, text_alpha)
    draw.text((WIDTH // 2 - text_w // 2, 60), text, fill=text_color, font=font)

    # Subtitle
    font_sub = get_font(24)
    sub_text = "Discovering Cross-Disciplinary Synergies"
    bbox = draw.textbbox((0, 0), sub_text, font=font_sub)
    sub_w = bbox[2] - bbox[0]
    draw.text((WIDTH // 2 - sub_w // 2, HEIGHT - 80), sub_text, fill=lerp_color(KSU_BLACK, WHITE, 0.6), font=font_sub)

    return img

def generate_before_after(frame_num, total_frames):
    """Scene 5: Before/After Split Screen (55-70s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames

    # Divider animation
    divider_x = int(WIDTH * (0.3 + ease_in_out_cubic(min(progress * 2, 1)) * 0.2))

    np.random.seed(42)

    # LEFT SIDE: Before IRIS (isolated, gray)
    left_center = (divider_x // 2, HEIGHT // 2)
    left_positions = []
    for _ in range(150):
        x = np.random.random() * (divider_x - 100) + 50
        y = np.random.random() * (HEIGHT - 200) + 100
        left_positions.append((x, y))

    for x, y in left_positions:
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=GRAY)

    # RIGHT SIDE: With IRIS (connected, vibrant)
    right_center = ((WIDTH + divider_x) // 2, HEIGHT // 2)
    right_positions = create_iris_positions(300, right_center, 300)

    # Draw connections (animated)
    pulse = (math.sin(frame_num * 0.1) + 1) / 2
    np.random.seed(456)
    for _ in range(100):
        i = np.random.randint(0, len(right_positions))
        j = np.random.randint(0, len(right_positions))
        if i != j:
            x1, y1 = right_positions[i]
            x2, y2 = right_positions[j]
            if x1 > divider_x and x2 > divider_x:
                dist = math.sqrt((x1 - x2) ** 2 + (y1 - y2) ** 2)
                if dist < 100:
                    intensity = 0.3 + pulse * 0.4
                    color = lerp_color(KSU_BLACK, KSU_GOLD, intensity)
                    draw.line([(x1, y1), (x2, y2)], fill=color, width=1)

    for x, y in right_positions:
        if x > divider_x:
            size = 3 + int(pulse * 2)
            color = lerp_color(KSU_GOLD_DIM, KSU_GOLD, 0.5 + pulse * 0.3)
            draw.ellipse([x - size, y - size, x + size, y + size], fill=color)

    # Divider line
    draw.line([(divider_x, 0), (divider_x, HEIGHT)], fill=WHITE, width=3)

    # Labels
    font = get_font(32, bold=True)
    font_sub = get_font(20)

    if progress > 0.2:
        label_fade = ease_in_out_cubic((progress - 0.2) / 0.3)

        # Left label
        left_label = "Before IRIS"
        bbox = draw.textbbox((0, 0), left_label, font=font)
        label_w = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, GRAY, label_fade)
        draw.text((divider_x // 2 - label_w // 2, 50), left_label, fill=color, font=font)

        sub_left = "Isolated Researchers"
        bbox = draw.textbbox((0, 0), sub_left, font=font_sub)
        sub_w = bbox[2] - bbox[0]
        draw.text((divider_x // 2 - sub_w // 2, 95), sub_left, fill=lerp_color(KSU_BLACK, GRAY, label_fade * 0.7), font=font_sub)

        # Right label
        right_label = "With IRIS"
        bbox = draw.textbbox((0, 0), right_label, font=font)
        label_w = bbox[2] - bbox[0]
        color = lerp_color(KSU_BLACK, KSU_GOLD, label_fade)
        draw.text(((WIDTH + divider_x) // 2 - label_w // 2, 50), right_label, fill=color, font=font)

        sub_right = "Connected Ecosystem"
        bbox = draw.textbbox((0, 0), sub_right, font=font_sub)
        sub_w = bbox[2] - bbox[0]
        draw.text(((WIDTH + divider_x) // 2 - sub_w // 2, 95), sub_right, fill=lerp_color(KSU_BLACK, WHITE, label_fade * 0.7), font=font_sub)

    return img

def generate_future_vision(frame_num, total_frames):
    """Scene 6: Future Vision - Historical figures (70-80s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames
    pulse = (math.sin(frame_num * 0.08) + 1) / 2

    # Historical figures (represented as glowing nodes with labels)
    historical = [
        (200, HEIGHT // 2 - 100, "Einstein", (200, 180, 160)),
        (200, HEIGHT // 2 + 100, "Curie", (180, 160, 200)),
        (350, HEIGHT // 2, "Hawking", (160, 200, 180)),
    ]

    # Modern researchers on right
    np.random.seed(789)
    modern_positions = []
    for i in range(80):
        x = 900 + np.random.random() * 800
        y = 150 + np.random.random() * 780
        modern_positions.append((x, y))

    # Draw ethereal connections
    if progress > 0.2:
        conn_alpha = ease_in_out_cubic((progress - 0.2) / 0.5)
        for hx, hy, name, color in historical:
            for i in range(0, len(modern_positions), 5):
                mx, my = modern_positions[i]
                # Ethereal fading line
                for t in range(20):
                    tt = t / 20
                    px = lerp(hx, mx, tt)
                    py = lerp(hy, my, tt)
                    fade = (1 - tt) * conn_alpha * (0.3 + pulse * 0.2)
                    point_color = lerp_color(KSU_BLACK, KSU_GOLD, fade * 0.5)
                    draw.ellipse([px - 1, py - 1, px + 1, py + 1], fill=point_color)

    # Draw historical figures (silhouettes as glowing circles)
    for hx, hy, name, tint in historical:
        node_fade = ease_in_out_cubic(min(progress * 2, 1))

        # Glow effect
        for r in range(60, 0, -5):
            alpha = (r / 60) * node_fade * (0.5 + pulse * 0.3)
            glow_color = tuple(int(c * alpha * 0.3) for c in tint)
            draw.ellipse([hx - r, hy - r, hx + r, hy + r], fill=glow_color)

        # Center
        draw.ellipse([hx - 15, hy - 15, hx + 15, hy + 15], fill=lerp_color(GRAY, tint, node_fade))

        # Label
        font = get_font(18)
        bbox = draw.textbbox((0, 0), name, font=font)
        text_w = bbox[2] - bbox[0]
        text_color = lerp_color(KSU_BLACK, WHITE, node_fade * 0.8)
        draw.text((hx - text_w // 2, hy + 30), name, fill=text_color, font=font)

    # Draw modern nodes
    for x, y in modern_positions:
        intensity = 0.4 + pulse * 0.3
        color = lerp_color(GRAY, KSU_GOLD, intensity)
        draw.ellipse([x - 3, y - 3, x + 3, y + 3], fill=color)

    # Title
    if progress > 0.3:
        title_fade = ease_in_out_cubic((progress - 0.3) / 0.4)
        font = get_font(36, bold=True)
        title = "Standing on the Shoulders of Giants"
        bbox = draw.textbbox((0, 0), title, font=font)
        title_w = bbox[2] - bbox[0]
        title_color = lerp_color(KSU_BLACK, WHITE, title_fade * 0.9)
        draw.text((WIDTH // 2 - title_w // 2, HEIGHT - 100), title, fill=title_color, font=font)

    return img

def generate_impact_metrics(frame_num, total_frames):
    """Scene 7: Impact Metrics Finale (80-90s)"""
    img = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
    draw = ImageDraw.Draw(img)

    progress = frame_num / total_frames

    metrics = [
        ("3-5x", "Higher Grant Success", 0.0),
        ("67%", "More Cross-Disciplinary Research", 0.25),
        ("Zero", "External Data Dependencies", 0.5),
    ]

    # Animated counters
    y_start = 250
    y_spacing = 200

    for i, (value, label, delay) in enumerate(metrics):
        if progress > delay:
            metric_progress = ease_out_expo(min((progress - delay) / 0.35, 1))

            y = y_start + i * y_spacing

            # Large value
            font_value = get_font(96, bold=True)
            value_color = lerp_color(KSU_BLACK, KSU_GOLD, metric_progress)
            bbox = draw.textbbox((0, 0), value, font=font_value)
            value_w = bbox[2] - bbox[0]
            draw.text((WIDTH // 2 - value_w // 2, y), value, fill=value_color, font=font_value)

            # Label below
            font_label = get_font(32)
            label_color = lerp_color(KSU_BLACK, WHITE, metric_progress * 0.8)
            bbox = draw.textbbox((0, 0), label, font=font_label)
            label_w = bbox[2] - bbox[0]
            draw.text((WIDTH // 2 - label_w // 2, y + 100), label, fill=label_color, font=font_label)

    # Final tagline
    if progress > 0.75:
        tagline_fade = ease_in_out_cubic((progress - 0.75) / 0.2)
        font_tag = get_font(28)
        tagline = "The Future of Research Collaboration"
        bbox = draw.textbbox((0, 0), tagline, font=font_tag)
        tag_w = bbox[2] - bbox[0]
        tag_color = lerp_color(KSU_BLACK, KSU_GOLD, tagline_fade)
        draw.text((WIDTH // 2 - tag_w // 2, HEIGHT - 120), tagline, fill=tag_color, font=font_tag)

    # Fade to black at the very end
    if progress > 0.9:
        fade_out = (progress - 0.9) / 0.1
        overlay = Image.new('RGB', (WIDTH, HEIGHT), KSU_BLACK)
        img = Image.blend(img, overlay, fade_out)

    return img

# ============================================================================
# AUDIO GENERATION
# ============================================================================

def generate_ambient_audio(duration, fps=44100):
    """Generate procedural ambient audio"""
    samples = int(duration * fps)
    t = np.linspace(0, duration, samples)

    # Base drone (low frequency)
    drone = 0.15 * np.sin(2 * np.pi * 55 * t)  # A1
    drone += 0.1 * np.sin(2 * np.pi * 82.5 * t)  # E2
    drone += 0.08 * np.sin(2 * np.pi * 110 * t)  # A2

    # Subtle pad (higher harmonics)
    pad = 0.05 * np.sin(2 * np.pi * 220 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.1 * t))
    pad += 0.03 * np.sin(2 * np.pi * 330 * t) * (0.5 + 0.5 * np.sin(2 * np.pi * 0.08 * t))

    # Gentle shimmer (very subtle high frequency modulation)
    shimmer = 0.02 * np.sin(2 * np.pi * 880 * t) * (0.3 + 0.3 * np.sin(2 * np.pi * 0.5 * t))

    # Combine
    audio = drone + pad + shimmer

    # Fade in/out
    fade_samples = int(2 * fps)  # 2 second fade
    fade_in = np.linspace(0, 1, fade_samples)
    fade_out = np.linspace(1, 0, fade_samples)

    audio[:fade_samples] *= fade_in
    audio[-fade_samples:] *= fade_out

    # Normalize
    audio = audio / np.max(np.abs(audio)) * 0.7

    # Convert to stereo
    stereo = np.column_stack([audio, audio])

    return stereo

# ============================================================================
# MAIN RENDERING
# ============================================================================

def render_video():
    """Main function to render the complete video"""
    print("=" * 60)
    print("IRIS Demo Video Generator")
    print("=" * 60)
    print(f"Resolution: {WIDTH}x{HEIGHT} @ {FPS}fps")
    print(f"Duration: {TOTAL_DURATION} seconds")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

    # Ensure output directories exist
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    FRAMES_DIR.mkdir(parents=True, exist_ok=True)

    total_frames = TOTAL_DURATION * FPS
    frames = []

    scene_generators = {
        'logo_reveal': generate_logo_reveal,
        'network_birth': generate_network_birth,
        'magic_moment': generate_magic_moment,
        'ai_intelligence': generate_ai_intelligence,
        'before_after': generate_before_after,
        'future_vision': generate_future_vision,
        'impact_metrics': generate_impact_metrics,
    }

    print("\nGenerating frames...")

    for frame_num in range(total_frames):
        current_time = frame_num / FPS

        # Determine which scene we're in
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
            # Default to last scene if somehow out of bounds
            current_scene = 'impact_metrics'
            scene_start, scene_end = SCENES[current_scene]

        # Calculate frame within scene
        scene_duration = scene_end - scene_start
        scene_frame = int((current_time - scene_start) * FPS)
        scene_total_frames = int(scene_duration * FPS)

        # Generate frame
        generator = scene_generators[current_scene]
        frame = generator(scene_frame, scene_total_frames)

        # Convert to numpy array for moviepy
        frame_array = np.array(frame)
        frames.append(frame_array)

        # Progress update
        if frame_num % (FPS * 5) == 0:  # Every 5 seconds
            pct = (frame_num / total_frames) * 100
            print(f"  {pct:.1f}% - {current_scene} (frame {frame_num}/{total_frames})")

    print("\nAll frames generated!")
    print(f"Total frames: {len(frames)}")

    # Create video
    print("\nAssembling video...")

    if MOVIEPY_AVAILABLE:
        try:
            clip = ImageSequenceClip(frames, fps=FPS)

            # Generate audio
            print("Generating ambient audio...")
            audio_data = generate_ambient_audio(TOTAL_DURATION)

            def make_audio_frame(t):
                if isinstance(t, np.ndarray):
                    indices = (t * 44100).astype(int)
                    indices = np.clip(indices, 0, len(audio_data) - 1)
                    return audio_data[indices]
                else:
                    idx = int(t * 44100)
                    idx = min(idx, len(audio_data) - 1)
                    return audio_data[idx]

            audio_clip = AudioClip(make_audio_frame, duration=TOTAL_DURATION, fps=44100)
            audio_clip = audio_clip.with_nchannels(2)

            # Combine video and audio
            final_clip = clip.with_audio(audio_clip)

            # Export
            print(f"Exporting to {OUTPUT_FILE}...")

            # Set ffmpeg path
            ffmpeg_path = r"C:\Program Files\Topaz Labs LLC\Topaz Video Enhance AI\ffmpeg.exe"
            if os.path.exists(ffmpeg_path):
                os.environ["IMAGEIO_FFMPEG_EXE"] = ffmpeg_path

            final_clip.write_videofile(
                str(OUTPUT_FILE),
                fps=FPS,
                codec='libx264',
                audio_codec='aac',
                audio_bitrate='192k',
                preset='medium',
                threads=4,
                logger='bar'
            )

            print("\n" + "=" * 60)
            print("VIDEO GENERATION COMPLETE!")
            print(f"Output: {OUTPUT_FILE}")
            print("=" * 60)

        except Exception as e:
            print(f"MoviePy export failed: {e}")
            print("Falling back to frame-by-frame export...")
            export_frames_fallback(frames)
    else:
        export_frames_fallback(frames)

def export_frames_fallback(frames):
    """Fallback: Export frames and use ffmpeg directly"""
    print("Exporting individual frames...")

    for i, frame in enumerate(frames):
        frame_path = FRAMES_DIR / f"frame_{i:05d}.png"
        Image.fromarray(frame).save(frame_path)

        if i % (FPS * 5) == 0:
            pct = (i / len(frames)) * 100
            print(f"  {pct:.1f}% exported")

    print("\nFrames exported. Creating video with ffmpeg...")

    # Generate audio file
    print("Generating audio...")
    audio_data = generate_ambient_audio(TOTAL_DURATION)
    audio_path = FRAMES_DIR / "ambient.wav"

    # Simple WAV export
    import wave
    with wave.open(str(audio_path), 'w') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(44100)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wav.writeframes(audio_int16.tobytes())

    # FFmpeg command
    ffmpeg_path = r"C:\Program Files\Topaz Labs LLC\Topaz Video Enhance AI\ffmpeg.exe"
    cmd = f'"{ffmpeg_path}" -y -framerate {FPS} -i "{FRAMES_DIR}/frame_%05d.png" -i "{audio_path}" -c:v libx264 -preset medium -crf 18 -c:a aac -b:a 192k -pix_fmt yuv420p "{OUTPUT_FILE}"'

    print(f"Running: {cmd}")
    os.system(cmd)

    print("\n" + "=" * 60)
    print("VIDEO GENERATION COMPLETE!")
    print(f"Output: {OUTPUT_FILE}")
    print("=" * 60)

if __name__ == "__main__":
    render_video()

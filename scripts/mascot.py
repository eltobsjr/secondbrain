#!/usr/bin/env python3
"""SecondBrain animated mascot — run before any skill output."""

import sys, time, math, os

# ── ANSI ──────────────────────────────────────────────────────────────────────
R   = '\033[0m'
B   = '\033[1m'
DIM = '\033[2m'
P1  = '\033[38;5;129m'   # purple
P2  = '\033[38;5;165m'   # bright purple
P3  = '\033[38;5;201m'   # pink-purple
CY  = '\033[38;5;51m'    # bright cyan
CY2 = '\033[38;5;45m'    # cyan
GR  = '\033[38;5;240m'   # dark gray
WH  = '\033[97m'
YE  = '\033[38;5;226m'   # yellow (spark)

HIDE = '\033[?25l'
SHOW = '\033[?25h'
CLEAR_LINE = '\033[2K'
UP = '\033[{}A'

# ── Brain frames (4 frames of subtle morph) ───────────────────────────────────
FRAMES = [
    [
        r"    .-'''''-.  .-'''''-.",
        r"   /  .-. .-Y`-Y-. .-. \ ",
        r"  | _( o ) |   | ( o )_ |",
        r"  ||  `---'|   |`---'  ||",
        r"  ||  ~~~~ \   / ~~~~  ||",
        r"   \  `----.\`./-.----'  /",
        r"    `-._____|___|_____.-' ",
    ],
    [
        r"    .-'''''-.  .-'''''-.",
        r"   / .-. .-. Y-. .-. .-\ ",
        r"  |_( o )  |   |  ( o )_|",
        r"  ||  `---`|   |'---'  ||",
        r"  ||  ~~~~~ \   / ~~~~~||",
        r"   \  `.----.\./-.---.'  /",
        r"    `-.______|_|______.-' ",
    ],
    [
        r"    .-'''''-.  .-'''''-.",
        r"   /  .-. .-Y`-Y-. .-. \ ",
        r"  | _( o ) |   | ( o )_ |",
        r"  ||  `---'|   |`---'  ||",
        r"  ||  ~~~~~ \   / ~~~~~||",
        r"   \  `-----.`-.------'  /",
        r"    `-._______|_______.-' ",
    ],
    [
        r"    .-'''''-.  .-'''''-.",
        r"   / .-. .-. Y-. .-. .-\ ",
        r"  |_( o )  |   |  ( o )_|",
        r"  ||  `---'|   |`---'  ||",
        r"  ||  ~~~~ \   / ~~~~  ||",
        r"   \  `----./`.-.----'   /",
        r"    `-._______|_______.-' ",
    ],
]

# ── Palette cycles through purple shades ──────────────────────────────────────
PALETTE = [P1, P2, P3, P2]

# ── Orbit particles ───────────────────────────────────────────────────────────
PARTICLES = ['·', '•', '◦', '∘', '⊙', '∘', '◦', '•']
SPARK     = ['*', '+', '✦', '*']

def orbit_pos(t, index, n=8, rx=22, ry=4, cx=24, cy=5):
    angle = 2 * math.pi * (index / n) + t
    x = cx + int(rx * math.cos(angle))
    y = cy + int(ry * math.sin(angle) * 0.6)
    return x, y

def render_frame(t, cmd, total_cols=54, total_rows=14):
    fi = int(t * 2) % 4
    brain = FRAMES[fi]
    color = PALETTE[fi]

    # Build a grid
    grid = [[' '] * total_cols for _ in range(total_rows)]
    color_grid = [[R] * total_cols for _ in range(total_rows)]

    # Place brain lines (centered, starting row 3)
    brain_start_row = 3
    for li, line in enumerate(brain):
        row = brain_start_row + li
        col_start = (total_cols - len(line)) // 2
        for ci, ch in enumerate(line):
            c = col_start + ci
            if 0 <= c < total_cols and 0 <= row < total_rows:
                grid[row][c] = ch
                color_grid[row][c] = color

    # Place orbit particles
    n_particles = 8
    for i in range(n_particles):
        px, py = orbit_pos(t * 1.5, i, n=n_particles, rx=23, ry=4, cx=26, cy=6)
        if 0 <= py < total_rows and 0 <= px < total_cols:
            # particle brightness depends on position (brighter at top)
            angle = 2 * math.pi * (i / n_particles) + t * 1.5
            brightness = (math.sin(angle) + 1) / 2
            ch = PARTICLES[i % len(PARTICLES)]
            pcol = CY if brightness > 0.6 else CY2 if brightness > 0.3 else GR
            if grid[py][px] == ' ':
                grid[py][px] = ch
                color_grid[py][px] = pcol

    # Sparks (fast small ones)
    n_sparks = 4
    for i in range(n_sparks):
        px, py = orbit_pos(t * 3.5 + math.pi, i, n=n_sparks, rx=18, ry=3, cx=26, cy=6)
        if 0 <= py < total_rows and 0 <= px < total_cols:
            if grid[py][px] == ' ':
                grid[py][px] = SPARK[i % len(SPARK)]
                color_grid[py][px] = YE

    # Top border
    border_top    = GR + '  ╭' + '─' * (total_cols - 4) + '╮' + R
    border_bot    = GR + '  ╰' + '─' * (total_cols - 4) + '╯' + R

    # Assemble output
    lines = [border_top]
    for row in range(total_rows):
        line_out = GR + '  │' + R
        for col in range(total_cols - 2):
            line_out += color_grid[row][col] + grid[row][col]
        line_out += R + GR + '│' + R
        lines.append(line_out)

    # Command label line
    label = f'  {cmd}'
    label_line = (GR + '  │' + R +
                  WH + B + label.center(total_cols - 2) + R +
                  GR + '│' + R)
    lines.append(label_line)

    # Subtitle
    sub = 'SecondBrain'
    sub_line = (GR + '  │' + R +
                DIM + sub.center(total_cols - 2) + R +
                GR + '│' + R)
    lines.append(sub_line)

    lines.append(border_bot)
    return lines

def animate(cmd, duration=2.2, fps=18):
    cmd_label = f'/{cmd}' if not cmd.startswith('/') else cmd
    frame_time = 1.0 / fps
    start = time.time()

    sys.stdout.write(HIDE)
    sys.stdout.flush()

    first = True
    n_lines = None

    try:
        while True:
            elapsed = time.time() - start
            if elapsed >= duration:
                break

            t = elapsed * 1.2
            lines = render_frame(t, cmd_label)

            if first:
                sys.stdout.write('\n')
                n_lines = len(lines)
                first = False
            else:
                # Move cursor up
                sys.stdout.write(f'\033[{n_lines + 1}A')

            for line in lines:
                sys.stdout.write(f'\033[2K{line}\n')

            sys.stdout.flush()
            time.sleep(frame_time)

        # Final static frame (clean)
        t = duration * 1.2
        lines = render_frame(t, cmd_label)
        sys.stdout.write(f'\033[{n_lines + 1}A')
        for line in lines:
            sys.stdout.write(f'\033[2K{line}\n')
        sys.stdout.write('\n')
        sys.stdout.flush()

    finally:
        sys.stdout.write(SHOW)
        sys.stdout.flush()

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else 'secondbrain'
    duration = float(sys.argv[2]) if len(sys.argv) > 2 else 2.2
    animate(cmd, duration)

import tkinter as tk
import random
import winsound
invader_win = None
invader_label = None
invader_on = False
invader_flip = 0
danger_active = False
danger_phase = 0
danger_tick = 0
esc_enabled = False

# ---------------------------
# CONFIG YOU CAN TWEAK
# ---------------------------
SPAWN_LIMIT = 60

START_DELAY_MS = 200       # you set this (nice!)
MIN_DELAY_MS = 35          # lower = more "panic spike"

DOOM_START_AT = 35         # when doom begins
DOOM_END_AT = 58           # when burst sequence starts

# TRUE red / doom palette (hex so it isn't baby pink)
BG_CALM = "#FFFFFF"
BG_UNEASY = "#FFF4D6"      # warm ivory
BG_WARN = "#FFB3B3"      # light red (warning)
BG_DOOM = "#B00020"      # deep blood red

FG_DARK = "#111111"
FG_LIGHT = "#FFFFFF"

# Comedic texts to sprinkle into many windows
COMEDY = [
    "OH DAMN", "NAH..", "STOP", "AW MAN", "HERE WE GO AGAIN",
    "BOOM", "NOPE", "OH CRAP", "TOO MANY", "HUH???", "SLAYY",
    "HELP", "UH OH", "BRO", "HELL NAW", "DOOMFALL"
]

# Ensure at least 25 windows get comedic text
COMEDY_MIN_COUNT = 25

root = tk.Tk()
root.title("origin")
root.geometry("360x200")

label = tk.Label(root, text="hello.", font=("Arial", 20))
label.pack(expand=True)

running = True
windows = [(root, label)]   # store (window, label) pairs so we can update them
spawn_count = 0
delay_ms = START_DELAY_MS
dots = 1

# Preselect which window indices will get comedic text (1..SPAWN_LIMIT)
comedy_indices = set(random.sample(range(1, SPAWN_LIMIT + 1), k=min(COMEDY_MIN_COUNT, SPAWN_LIMIT)))


def panic_stop(event=None):
    """Emergency stop: closes everything cleanly."""
    global running
    if event is not None and not esc_enabled:
        return
    running = False
    stop_invader()
    try:
        root.destroy()
    except tk.TclError:
        pass


root.bind_all("<Escape>", panic_stop)


def stage_for(n: int) -> int:
    # 0 calm, 1 uneasy, 2 warning, 3 doom
    if n < DOOM_START_AT:
        return 0
    elif n < DOOM_START_AT + 8:
        return 1
    elif n < DOOM_END_AT:
        return 2
    else:
        return 3


def colors_for(stage: int):
    if stage == 0:
        return BG_CALM, FG_DARK
    if stage == 1:
        return BG_UNEASY, FG_DARK
    if stage == 2:
        return BG_WARN, FG_DARK
    return BG_DOOM, FG_LIGHT


def spawn_window(i: int, stage: int):
    w = tk.Toplevel(root)
    w.title(f"echo {i}")

    # Swarm placement (random-ish)
    w_w, w_h = 240, 140
    x = random.randint(0, 1000)
    y = random.randint(0, 650)
    w.geometry(f"{w_w}x{w_h}+{x}+{y}")

    bg, fg = colors_for(stage)

    # Pick text: comedy for at least 25 indices, otherwise stage-based
    if i in comedy_indices:
        text = random.choice(COMEDY)
    else:
        text = "..." if stage < 2 else ("too many" if stage == 2 else "STOP")

    l = tk.Label(w, text=text, font=("Arial", 14), bg=bg, fg=fg)
    l.pack(expand=True, fill="both")

    w.configure(bg=bg)

    windows.append((w,l))


def update_all_windows(stage: int):
    """Push current doom color onto all existing windows (feels more unified)."""
    bg, fg = colors_for(stage)
    for w, l in windows:
        try:
            w.configure(bg=bg)
            l.configure(bg=bg, fg=fg)
        except tk.TclError:
            pass


def dangerous_glitch():
    """
    freeze → flicker → blackout → exit
    """
    global running
    esc_enabled = True

    if not running:
        return

    # 1) FREEZE everything (black screen)
    for w, l in windows:
        try:
            w.configure(bg="#000000")
            l.configure(bg="#000000", fg=FG_LIGHT)
        except tk.TclError:
            pass

    if invader_on and invader_win is not None:
        try:
            invader_win.configure(bg="#000000")
            invader_label.configure(bg="#000000", fg=FG_LIGHT)
        except tk.TclError:
            pass

    # 2) FLICKER a few times
    for i in range(6):
        bg = BG_DOOM if i % 2 else "#000000"
        root.after(
            i * 80,
            lambda c=bg: [
                w.configure(bg=c) or l.configure(bg=c)
                for w, l in windows
                if w.winfo_exists()
            ]
        )

    # invader flicker too
    if invader_on and invader_win is not None:
        for i in range(6):
            bg = BG_DOOM if i % 2 else "#000000"
            root.after(
                i * 80,
                lambda c=bg: invader_win.configure(bg=c)
            )

    # 3) BLACKOUT + EXIT
    root.after(10000, panic_stop)


def burst_sequence(step=0, steps=10):
    """
    Fake explosion: rapidly jitter + resize + flash,
    then destroy all windows at the end.
    """
    if not running:
        return

    # Flash between doom red and white for a strobe-like "burst"
    flash_bg = BG_DOOM if step % 2 == 0 else "#FFFFFF"
    flash_fg = FG_LIGHT if step % 2 == 0 else FG_DARK

    for w, l in windows:
        try:
            # jitter position + slightly change size
            cur = w.geometry()
            # geometry format: "{w}x{h}+{x}+{y}" (may vary), so we do a gentle override instead
            w_w = random.randint(180, 360)
            w_h = random.randint(110, 220)
            x = random.randint(0, 1100)
            y = random.randint(0, 700)
            w.geometry(f"{w_w}x{w_h}+{x}+{y}")

            w.configure(bg=flash_bg)
            l.configure(bg=flash_bg, fg=flash_fg)

            # Make texts more frantic near the end
            if step >= steps - 3:
                l.configure(text=random.choice(COMEDY))
        except tk.TclError:
            pass

    if step >= steps-3:
        dangerous_glitch()
        return

    if step >= steps:
        panic_stop()
        return

    root.after(45, lambda: burst_sequence(step + 1, steps))


def enable_esc_prompt():
    global esc_enabled
    esc_enabled = True
    tk.Label(
        invader_win,
        text="press ESC to exit LOL",
        font=("Arial", 14, "bold"),
        fg="#FFFFFF",
        bg=invader_win.cget("bg")
    ).place(relx=0.5, rely=0.98, anchor="s")

    winsound.PlaySound("deathpiano.wav", winsound.SND_FILENAME | winsound.SND_ASYNC)


def start_invader():
    global invader_win, invader_label, invader_on, invader_flip

    if invader_on:
        return

    invader_on = True
    invader_flip = 0

    invader_win = tk.Toplevel(root)
    invader_win.bind("<Escape>", panic_stop)
    invader_win.configure(bg="#000000")
    invader_win.title("UH OH")
    invader_win.overrideredirect(True)  # no border = scarier
    invader_win.attributes("-topmost", True)

    w, h = 500, 300
    x = (invader_win.winfo_screenwidth() - w) // 2
    y = (invader_win.winfo_screenheight() - h) // 2
    invader_win.geometry(f"{w}x{h}+{x}+{y}")

    invader_label = tk.Label(
        invader_win,
        text="UH OH\nBOOM",
        font=("Arial", 36, "bold"),
        fg=FG_LIGHT,
        bg="#000000",
        justify="center"
    )
    invader_label.pack(expand=True, fill="both")

    flicker_invader()

    invader_win.after(7000, enable_esc_prompt)


def stop_invader():
    global invader_on, invader_win
    invader_on = False
    if invader_win:
        try:
            invader_win.destroy()
        except tk.TclError:
            pass
    invader_win = None


def flicker_invader():
    global invader_flip

    if not invader_on or invader_win is None or invader_label is None or not running:
        return

    invader_flip += 1
    bg = "#000000" if invader_flip % 2 == 0 else BG_DOOM

    try:
        invader_win.configure(bg=bg)
        invader_label.configure(bg=bg, fg=FG_LIGHT)
    except tk.TclError:
        return

    # IMPORTANT: schedule the next flicker
    invader_win.after(120, flicker_invader)



def pulse():
    global spawn_count, delay_ms, dots

    if not running:
        return

    # "heartbeat" dots
    dots = (dots % 3) + 1

    if spawn_count < SPAWN_LIMIT:
        spawn_count += 1
        stage = stage_for(spawn_count)

        # INVADER trigger (NEW)
        if stage >= 3:  # appears when doom red starts
            start_invader()
        else:
            stop_invader()

        bg, fg = colors_for(stage)

        # main label text
        if stage < 3:
            label.configure(text="hello" + "." * dots, bg=bg, fg=fg)
        else:
            label.configure(text="STOP", bg=bg, fg=fg)

        root.configure(bg=bg)
        update_all_windows(stage)

        spawn_window(spawn_count, stage)

        # Flood acceleration (panic spike: harsher acceleration during doom)
        accel = 0.93 if spawn_count < DOOM_START_AT else 0.86
        delay_ms = max(MIN_DELAY_MS, int(delay_ms * accel))

        # Once we hit doom end: trigger burst
        if spawn_count >= DOOM_END_AT:
            burst_sequence()
            return

    root.after(delay_ms, pulse)

pulse()
root.mainloop()


# -*- coding: utf-8 -*-
"""
5分钟计时器 —— 瑞士铁路钟风格的桌面倒计时 (Windows)

每轮 5 分钟，红色扫针扫过整圈。到时播放提示音并闪烁提醒，
停在 00:00，点击"再来一轮"手动开始下一轮。
"""

import argparse
import ctypes
import math
import threading
import time
import tkinter as tk
import tkinter.font as tkfont
import winsound

# ---------------- 设计 tokens ----------------
FACE = "#FBFBF7"   # 表盘纸白
INK = "#191919"    # 刻度、数字、正文
RED = "#E20612"    # 铁路信号红：扫针、已走时弧、提醒
TRACK = "#DDDDD6"  # 未走时轨道
GREY = "#8A877E"   # 次级文字

ROUND_SECONDS = 5 * 60
TICK_MS = 50


def best_family(root, candidates):
    installed = set(tkfont.families(root))
    for name in candidates:
        if name in installed:
            return name
    return "TkDefaultFont"


def fmt(seconds):
    s = max(0, math.ceil(seconds - 1e-9))
    return "%02d:%02d" % (s // 60, s % 60)


def beeps():
    for _ in range(3):
        winsound.Beep(880, 180)
        time.sleep(0.12)


class Dial(tk.Canvas):
    """5分钟表盘：整圈 = 一轮，红色指针从顶部顺时针扫过。"""

    CX, CY = 170, 152
    R_TICK = 126     # 刻度外沿
    R_ARC = 96       # 已走时弧
    R_HAND = 82      # 指针尖端
    R_NUM = 146      # 分钟数字

    def __init__(self, master, digit_font, dial_font):
        super().__init__(master, width=340, height=300,
                         bg=FACE, highlightthickness=0, bd=0)
        self._draw_static(dial_font)
        self.arc = self.create_arc(self._bbox(self.R_ARC), start=90, extent=-0.01,
                                   style="arc", outline=RED, width=12, state="hidden")
        self.hand = self.create_line(0, 0, 0, 0, fill=RED, width=3, capstyle="round")
        self.paddle = self.create_oval(0, 0, 0, 0, fill=RED, outline="")
        self.readout = self.create_text(self.CX, self.CY + 2, text="",
                                        font=digit_font, fill=INK)

    def _bbox(self, r):
        return (self.CX - r, self.CY - r, self.CX + r, self.CY + r)

    def _draw_static(self, dial_font):
        # 刻度：每 15 秒一根，每分钟一根长刻度
        for i in range(20):
            a = math.radians(-90 + i * 18)
            major = (i % 4 == 0)
            r0 = 108 if major else 117
            self.create_line(self.CX + r0 * math.cos(a), self.CY + r0 * math.sin(a),
                             self.CX + self.R_TICK * math.cos(a), self.CY + self.R_TICK * math.sin(a),
                             fill=INK, width=3 if major else 1, tags="ink")
        # 分钟数字 1-5（5 在正上方）
        for k in range(1, 6):
            a = math.radians(-90 + k * 72)
            self.create_text(self.CX + self.R_NUM * math.cos(a),
                             self.CY + self.R_NUM * math.sin(a),
                             text=str(k), font=dial_font, fill=INK, tags="ink")
        # 未走时轨道
        self.create_arc(self._bbox(self.R_ARC), start=0, extent=359.99,
                        style="arc", outline=TRACK, width=12)

    def set(self, frac, text, text_color=INK):
        """frac: 已走比例 0..1；text: 中央读秒。"""
        frac = max(0.0, min(1.0, frac))
        if frac <= 0:
            self.itemconfigure(self.arc, state="hidden")
        else:
            self.itemconfigure(self.arc, state="normal", extent=-359.99 * frac)
        a = math.radians(-90 + 360 * frac)
        x0 = self.CX + 26 * math.cos(a)
        y0 = self.CY + 26 * math.sin(a)
        x1 = self.CX + self.R_HAND * math.cos(a)
        y1 = self.CY + self.R_HAND * math.sin(a)
        self.coords(self.hand, x0, y0, x1, y1)
        px = self.CX + 66 * math.cos(a)
        py = self.CY + 66 * math.sin(a)
        self.coords(self.paddle, px - 7, py - 7, px + 7, py + 7)
        self.itemconfigure(self.readout, text=text, fill=text_color)


class TimerApp:
    def __init__(self, root, seconds=ROUND_SECONDS):
        self.root = root
        self.round_seconds = seconds
        self.remaining = float(seconds)
        self.rounds = 0
        self.state = "idle"      # idle | running | paused | finished
        self.sound_on = True
        self._job = None
        self._flash_job = None
        self._flash_step = 0
        self._end_ts = 0.0

        digit_family = best_family(root, ["Bahnschrift SemiBold", "Segoe UI Semibold"])
        ui_family = best_family(root, ["Microsoft YaHei UI", "Segoe UI"])
        self.f_digit = (digit_family, 44)
        self.f_dial = (digit_family, 13)
        self.f_ui = (ui_family, 10)
        self.f_title = (ui_family, 11)

        root.title("5分钟计时")
        root.configure(bg=FACE)
        root.geometry("380x540")
        root.resizable(False, False)

        # 顶部：标题 + 声音开关
        self.header = tk.Frame(root, bg=FACE)
        self.header.pack(fill="x", padx=20, pady=(16, 0))
        self.title_label = tk.Label(self.header, text="5分钟计时",
                                    font=self.f_title, bg=FACE, fg=INK)
        self.title_label.pack(side="left")
        self.sound_btn = tk.Button(self.header, text="声音 开", command=self.toggle_sound,
                                   font=(self.f_ui[0], 9), bg=FACE, fg=GREY,
                                   relief="flat", bd=0, cursor="hand2",
                                   activebackground=FACE, activeforeground=INK)
        self.sound_btn.pack(side="right")

        # 表盘
        self.dial = Dial(root, self.f_digit, self.f_dial)
        self.dial.pack(pady=(10, 0))

        # 轮次计数
        self.counter_label = tk.Label(root, font=self.f_ui, bg=FACE, fg=GREY)
        self.counter_label.pack(pady=(6, 0))

        # 控制区
        self.controls = tk.Frame(root, bg=FACE)
        self.controls.pack(pady=(18, 0))
        self.main_btn = self._button(self.controls, self.on_main, primary=True, width=10)
        self.main_btn.pack(side="left", padx=(0, 12))
        self.reset_btn = self._button(self.controls, self.on_reset, primary=False, width=8)
        self.reset_btn.pack(side="left")

        self._render()

    # ---------------- 控件 ----------------
    def _button(self, parent, command, primary, width):
        bg = INK if primary else FACE
        fg = FACE if primary else INK
        btn = tk.Button(parent, command=command, width=width,
                        font=self.f_ui, bg=bg, fg=fg,
                        relief="flat", bd=0, pady=8, cursor="hand2",
                        activebackground=RED, activeforeground=FACE,
                        highlightthickness=0 if primary else 1,
                        highlightbackground=TRACK, highlightcolor=INK)
        hover_bg = RED if primary else "#F0EEE6"
        btn.bind("<Enter>", lambda e: btn.configure(bg=hover_bg, fg=FACE if primary else INK))
        btn.bind("<Leave>", lambda e: btn.configure(bg=bg, fg=fg))
        return btn


    # ---------------- 计时引擎 ----------------
    def on_main(self):
        if self.state == "idle":
            self._start()
        elif self.state == "running":
            self._pause()
        elif self.state == "paused":
            self._resume()
        elif self.state == "finished":
            self._reset_round()
            self._start()

    def on_reset(self):
        self._cancel_jobs()
        self.state = "idle"
        self.rounds = 0
        self.remaining = float(self.round_seconds)
        self._render()

    def toggle_sound(self):
        self.sound_on = not self.sound_on
        self.sound_btn.configure(text="声音 开" if self.sound_on else "声音 关")

    def _start(self):
        self._end_ts = time.monotonic() + self.remaining
        self.state = "running"
        self._render()
        self._job = self.root.after(TICK_MS, self._tick)

    def _resume(self):
        self._start()

    def _pause(self):
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        self.state = "paused"
        self._render()

    def _reset_round(self):
        self._cancel_jobs()
        self.remaining = float(self.round_seconds)
        self.state = "idle"

    def _cancel_jobs(self):
        if self._job:
            self.root.after_cancel(self._job)
            self._job = None
        if self._flash_job:
            self.root.after_cancel(self._flash_job)
            self._flash_job = None
            self._chrome(FACE, INK)

    def _tick(self):
        self.remaining = self._end_ts - time.monotonic()
        if self.remaining <= 0:
            self.remaining = 0.0
            self._job = None
            self._finish()
            return
        self._render()
        self._job = self.root.after(TICK_MS, self._tick)

    def _finish(self):
        self.state = "finished"
        self.rounds += 1
        self._render()
        if self.sound_on:
            threading.Thread(target=beeps, daemon=True).start()
        self._flash_step = 0
        self._flash()

    # ---------------- 提醒闪烁 ----------------
    def _flash(self):
        red_phase = (self._flash_step % 2 == 0)
        self._chrome(RED if red_phase else FACE, FACE if red_phase else INK)
        self._flash_step += 1
        if self._flash_step < 6:
            self._flash_job = self.root.after(170, self._flash)
        else:
            self._flash_job = None
            self._render()

    def _chrome(self, bg, fg):
        self.root.configure(bg=bg)
        self.header.configure(bg=bg)
        self.controls.configure(bg=bg)
        self.title_label.configure(bg=bg, fg=fg)
        self.counter_label.configure(bg=bg, fg=fg)
        self.sound_btn.configure(bg=bg, fg=fg, activebackground=bg)
        self.dial.configure(bg=bg)
        self.dial.itemconfigure("ink", fill=fg)
        self.dial.itemconfigure(self.dial.readout, fill=fg)

    # ---------------- 渲染 ----------------
    def _render(self):
        frac = 1.0 - self.remaining / self.round_seconds if self.round_seconds else 0
        text_color = RED if self.state == "finished" else INK
        self.dial.set(frac, fmt(self.remaining), text_color)
        self.counter_label.configure(text="已完成 %d 轮" % self.rounds)
        self.sound_btn.configure(bg=FACE, fg=GREY, activebackground=FACE)
        self.main_btn.configure(text={
            "idle": "开始",
            "running": "暂停",
            "paused": "继续",
            "finished": "再来一轮",
        }[self.state])


def main():
    parser = argparse.ArgumentParser(description="5分钟桌面倒计时")
    parser.add_argument("--seconds", type=int, default=ROUND_SECONDS,
                        help="每轮秒数（默认 300，调试用）")
    args = parser.parse_args()

    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # 高分屏清晰渲染
    except Exception:
        pass

    root = tk.Tk()
    TimerApp(root, seconds=args.seconds)
    root.mainloop()


if __name__ == "__main__":
    main()

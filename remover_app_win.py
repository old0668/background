import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk, ImageDraw, ImageFilter
import io
import os
import sys
import numpy as np
import ctypes
from rembg import remove, new_session

# --- Windows 高 DPI 支援 (防止介面模糊) ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# 自定義膠囊型圓角按鈕
class RoundedButton(tk.Canvas):
    def __init__(self, parent, text, command=None, width=105, height=36, radius=18, color="#2C2C2E", hover_color="#3A3A3C", text_color="white", font=("Microsoft JhengHei", 10, "bold")):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.command, self.color, self.hover_color, self.text = command, color, hover_color, text
        self.radius, self.text_color, self.font = radius, text_color, font
        self.state = "normal"; self.draw_button(self.color)
        self.bind("<Enter>", lambda e: self.draw_button(self.hover_color))
        self.bind("<Leave>", lambda e: self.draw_button(self.color))
        self.bind("<Button-1>", self.on_click)

    def draw_button(self, color):
        self.delete("all")
        w, h, r = self.winfo_reqwidth(), self.winfo_reqheight(), self.radius
        self.create_arc((0, 0, r*2, r*2), start=90, extent=90, fill=color, outline="")
        self.create_arc((w-r*2, 0, w, r*2), start=0, extent=90, fill=color, outline="")
        self.create_arc((0, h-r*2, r*2, h), start=180, extent=90, fill=color, outline="")
        self.create_arc((w-r*2, h-r*2, w, h), start=270, extent=90, fill=color, outline="")
        self.create_rectangle((r, 0, w-r, h), fill=color, outline="")
        self.create_rectangle((0, r, w, h-r), fill=color, outline="")
        self.create_text(w/2, h/2, text=self.text, fill=self.text_color, font=self.font)

    def on_click(self, event):
        if self.state == "normal" and self.command: self.command()

    def set_state(self, state):
        self.state = state; self.draw_button("#1A1A1C" if state == "disabled" else self.color)
        self.config(cursor="arrow" if state == "disabled" else "hand2")

# 自定義極簡白色滑桿
class MinimalSlider(tk.Canvas):
    def __init__(self, parent, from_=5, to=150, initial=20, command=None, width=100, height=36):
        super().__init__(parent, width=width, height=height, bg=parent["bg"], highlightthickness=0, cursor="hand2")
        self.from_, self.to, self.value, self.command = from_, to, initial, command
        self.w, self.h = width, height
        self.bind("<B1-Motion>", self.move_slider); self.bind("<Button-1>", self.move_slider)
        self.draw_slider()

    def move_slider(self, event):
        x = max(10, min(self.w - 10, event.x))
        self.value = self.from_ + (x - 10) / (self.w - 20) * (self.to - self.from_)
        self.draw_slider()
        if self.command: self.command(self.value)

    def draw_slider(self):
        self.delete("all")
        self.create_line(10, self.h/2, self.w-10, self.h/2, fill="#444", width=2)
        x = 10 + (self.value - self.from_) / (self.to - self.from_) * (self.w - 20)
        self.create_line(10, self.h/2, x, self.h/2, fill="white", width=2)
        self.create_oval(x-6, self.h/2-6, x+6, self.h/2+6, fill="white", outline="")

class XiangTeacherProAppWin:
    def __init__(self, root):
        self.root = root
        self.root.title("祥老師去背 (Windows版) - Pro AI Studio")
        self.root.geometry("1500x950")
        
        self.color_bg, self.color_toolbar = "#1C1C1E", "#000000"
        self.color_panel_l, self.color_panel_r = "#E5E5EA", "#777777"
        self.color_silver, self.color_accent = "#D1D1D6", "#0A84FF"
        self.root.configure(bg=self.color_silver)
        
        print("Starting AI Engine...")
        self.session = new_session("u2net")
        self.original_img = self.mask = None; self.history = []
        self.zoom_level, self.brush_size, self.tool_mode = 1.0, 20, "brush_restore"
        self.last_mx = self.last_my = 0
        
        self.crop_x1 = self.crop_y1 = self.crop_x2 = self.crop_y2 = None
        
        # Windows 的右鍵事件
        self.right_click = "<Button-3>"
        self.middle_click = "<Button-2>"
        
        self.setup_ui(); self.create_context_menu(); self.bind_events()

    def setup_ui(self):
        self.container = tk.Frame(self.root, bg=self.color_bg, bd=0); self.container.pack(expand=True, fill=tk.BOTH, padx=2, pady=2)
        
        # 標題
        title_bar = tk.Frame(self.container, bg=self.color_bg)
        title_bar.pack(fill=tk.X, padx=30, pady=10)
        tk.Label(title_bar, text="祥老師去背", bg=self.color_bg, fg="white", font=("微軟正黑體", 24, "bold")).pack(side=tk.LEFT)
        
        toolbar_container = tk.Frame(self.container, bg=self.color_toolbar, height=80); toolbar_container.pack(fill=tk.X)
        toolbar = tk.Frame(toolbar_container, bg=self.color_toolbar, pady=15, padx=30); toolbar.pack(fill=tk.X)
        
        fg = tk.Frame(toolbar, bg=self.color_toolbar); fg.pack(side=tk.LEFT)
        RoundedButton(fg, "載入圖片", self.load_image, width=90).pack(side=tk.LEFT, padx=5)
        self.btn_ai = RoundedButton(fg, "自動去背", self.run_ai, width=90, color=self.color_accent, hover_color="#54A6FF")
        self.btn_ai.pack(side=tk.LEFT, padx=5); self.btn_ai.set_state("disabled")

        tk.Frame(toolbar, width=1, bg="#333").pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        eg = tk.Frame(toolbar, bg=self.color_toolbar); eg.pack(side=tk.LEFT)
        style = ttk.Style(); style.theme_use('clam')
        style.configure("Pro.TRadiobutton", background=self.color_toolbar, foreground="white", font=("微軟正黑體", 10))
        style.map("Pro.TRadiobutton", background=[('active', self.color_toolbar)])
        
        self.tool_var = tk.StringVar(value="brush_restore")
        tools = [("修復", "brush_restore", "🖌"), ("擦除", "brush_erase", "✕"), ("移動", "pan", "✋"), ("裁切", "crop", "✂")]
        for text, mode, icon in tools:
            ttk.Radiobutton(eg, text=f"{icon} {text}", variable=self.tool_var, value=mode, style="Pro.TRadiobutton", command=lambda m=mode: self.set_tool(m)).pack(side=tk.LEFT, padx=6)

        tk.Frame(toolbar, width=1, bg="#333").pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        bg = tk.Frame(toolbar, bg=self.color_toolbar); bg.pack(side=tk.LEFT)
        tk.Label(bg, text="筆刷:", bg=self.color_toolbar, fg="#8E8E93", font=("微軟正黑體", 10)).pack(side=tk.LEFT, padx=5)
        self.brush_slider = MinimalSlider(bg, command=self.update_brush_size, width=80); self.brush_slider.pack(side=tk.LEFT)

        tk.Frame(toolbar, width=1, bg="#333").pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        self.btn_do_crop = RoundedButton(toolbar, "裁切圖片", self.apply_crop, width=90, color="#FF9500", hover_color="#FFB340")
        self.btn_do_crop.pack(side=tk.LEFT, padx=5)

        tk.Frame(toolbar, width=1, bg="#333").pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=5)
        nav_group = tk.Frame(toolbar, bg=self.color_toolbar); nav_group.pack(side=tk.LEFT)
        for d, dx, dy in [("←", -40, 0), ("↑", 0, -40), ("↓", 0, 40), ("→", 40, 0)]:
            RoundedButton(nav_group, d, lambda x=dx, y=dy: self.move_view(x, y), width=35, radius=10).pack(side=tk.LEFT, padx=1)

        ag = tk.Frame(toolbar, bg=self.color_toolbar); ag.pack(side=tk.RIGHT)
        RoundedButton(ag, "復原", self.undo, width=65).pack(side=tk.LEFT, padx=2)
        RoundedButton(ag, "重設", self.reset_view, width=65).pack(side=tk.LEFT, padx=2)
        RoundedButton(ag, "儲存結果", self.show_save_dialog, width=100, color=self.color_accent, hover_color="#54A6FF").pack(side=tk.LEFT, padx=8)

        self.work_area = tk.Frame(self.container, bg=self.color_bg); self.work_area.pack(expand=True, fill=tk.BOTH, padx=30, pady=10)
        self.canvas_left = tk.Canvas(tk.Frame(self.work_area, bg=self.color_panel_l, bd=0), bg=self.color_panel_l, highlightthickness=0)
        self.canvas_left.master.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8); self.canvas_left.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)
        self.canvas_right = tk.Canvas(tk.Frame(self.work_area, bg=self.color_panel_r, bd=0), bg=self.color_panel_r, highlightthickness=0)
        self.canvas_right.master.pack(side=tk.LEFT, expand=True, fill=tk.BOTH, padx=8); self.canvas_right.pack(expand=True, fill=tk.BOTH, padx=5, pady=5)

    def create_context_menu(self):
        self.context_menu = tk.Menu(self.root, tearoff=0, bg="#2C2C2E", fg="white", activebackground="#0A84FF", font=("微軟正黑體", 10))
        self.context_menu.add_command(label="🖌 修復模式", command=lambda: self.quick_set_tool("brush_restore"))
        self.context_menu.add_command(label="✕ 擦除模式", command=lambda: self.quick_set_tool("brush_erase"))
        self.context_menu.add_command(label="✂ 裁切模式", command=lambda: self.quick_set_tool("crop"))
        self.context_menu.add_separator()
        self.context_menu.add_command(label="✋ 移動視圖", command=lambda: self.quick_set_tool("pan"))

    def quick_set_tool(self, m): self.tool_var.set(m); self.set_tool(m)
    def set_tool(self, mode):
        self.tool_mode = mode; self.canvas_right.delete("brush_cursor", "crop_rect")
        if mode == "pan": self.canvas_right.config(cursor="fleur")
        elif mode == "crop": self.canvas_right.config(cursor="cross")
        else: self.canvas_right.config(cursor="arrow")

    def bind_events(self):
        self.root.bind("<MouseWheel>", self.handle_zoom)
        self.canvas_right.bind(self.middle_click, self.pan_start)
        self.canvas_right.bind(self.right_click, lambda e: self.context_menu.post(e.x_root, e.y_root))
        self.canvas_right.bind("<ButtonPress-1>", self.handle_click)
        self.canvas_right.bind("<B1-Motion>", self.handle_motion)
        self.canvas_right.bind("<ButtonRelease-1>", self.handle_release)
        self.canvas_right.bind("<Motion>", self.update_brush_cursor)
        self.root.bind("<Control-z>", lambda e: self.undo())

    def update_brush_size(self, val):
        self.brush_size = int(float(val)); self.draw_brush_cursor_at_last_pos()

    def update_brush_cursor(self, event):
        self.last_mx, self.last_my = event.x, event.y; self.draw_brush_cursor_at_last_pos()

    def draw_brush_cursor_at_last_pos(self):
        if self.tool_mode not in ["brush_restore", "brush_erase"] or self.original_img is None: return
        self.canvas_right.delete("brush_cursor"); cx, cy, vr = self.canvas_right.canvasx(self.last_mx), self.canvas_right.canvasy(self.last_my), self.brush_size
        self.canvas_right.create_oval(cx-vr, cy-vr, cx+vr, cy+vr, outline="white", width=1, tags="brush_cursor")

    def handle_click(self, event):
        if self.original_img is None: return
        if self.tool_mode == "pan": self.pan_start(event)
        elif self.tool_mode == "crop":
            self.crop_x1, self.crop_y1 = event.x, event.y; self.canvas_right.delete("crop_rect")
        else:
            self.save_to_history(); x, y = self.get_img_coords(event.x, event.y)
            if 0 <= x < self.original_img.size[0] and 0 <= y < self.original_img.size[1]: self.paint(x, y)

    def handle_motion(self, event):
        if self.original_img is None: return
        self.last_mx, self.last_my = event.x, event.y
        if self.tool_mode == "pan": self.pan_move(event)
        elif self.tool_mode == "crop" and self.crop_x1 is not None:
            self.canvas_right.delete("crop_rect")
            self.canvas_right.create_rectangle(self.canvas_right.canvasx(self.crop_x1), self.canvas_right.canvasy(self.crop_y1), self.canvas_right.canvasx(event.x), self.canvas_right.canvasy(event.y), outline=self.color_accent, width=2, tags="crop_rect")
        else:
            self.draw_brush_cursor_at_last_pos()
            if self.tool_mode in ["brush_restore", "brush_erase"]:
                x, y = self.get_img_coords(event.x, event.y)
                if 0 <= x < self.original_img.size[0] and 0 <= y < self.original_img.size[1]: self.paint(x, y)

    def handle_release(self, event):
        if self.tool_mode == "crop": self.crop_x2, self.crop_y2 = event.x, event.y

    def apply_crop(self):
        if self.crop_x1 is None or self.crop_x2 is None: return
        self.save_to_history(); ix1, iy1 = self.get_img_coords(self.crop_x1, self.crop_y1); ix2, iy2 = self.get_img_coords(self.crop_x2, self.crop_y2)
        l, t, r, b = min(ix1, ix2), min(iy1, iy2), max(ix1, ix2), max(iy1, iy2)
        if r - l < 10 or b - t < 10: return
        self.original_img = self.original_img.crop((l, t, r, b)); self.mask = self.mask.crop((l, t, r, b))
        self.canvas_right.delete("crop_rect"); self.crop_x1 = self.crop_x2 = None; self.reset_view()

    def show_save_dialog(self):
        if self.original_img is None: return
        sw = tk.Toplevel(self.root); sw.title("儲存"); sw.geometry("380x300"); sw.configure(bg="#2C2C2E"); sw.transient(self.root); sw.grab_set()
        tk.Label(sw, text="儲存影像設定", bg="#2C2C2E", fg="white", font=("微軟正黑體", 12, "bold")).pack(pady=15)
        fmt = tk.StringVar(value="PNG"); ol = tk.Label(sw, text="無損壓縮等級 (0-9):", bg="#2C2C2E", fg="#AAA")
        os = tk.Scale(sw, from_=0, to=9, orient=tk.HORIZONTAL, bg="#2C2C2E", fg="white", highlightthickness=0); os.set(6)
        def up():
            if fmt.get() == "PNG": ol.config(text="無損壓縮等級 (0-9):"); os.config(from_=0, to=9); os.set(6)
            else: ol.config(text="品質百分比 (10-100):"); os.config(from_=10, to=100); os.set(85)
        tk.Radiobutton(sw, text="PNG (高品質)", variable=fmt, value="PNG", bg="#2C2C2E", fg="white", selectcolor="#0A84FF", command=up).pack(); tk.Radiobutton(sw, text="JPG (體積小)", variable=fmt, value="JPEG", bg="#2C2C2E", fg="white", selectcolor="#0A84FF", command=up).pack()
        ol.pack(pady=(10, 0)); os.pack(pady=5)
        def save():
            ex = ".png" if fmt.get()=="PNG" else ".jpg"; p = filedialog.asksaveasfilename(defaultextension=ex, filetypes=[("Image", f"*{ex}")])
            if p:
                res = self.original_img.copy().convert("RGBA"); res.putalpha(self.mask)
                if fmt.get() == "JPEG":
                    res = Image.alpha_composite(Image.new("RGBA", res.size, "white"), res).convert("RGB")
                    res.save(p, "JPEG", quality=os.get(), optimize=True)
                else: res.save(p, "PNG", compress_level=os.get(), optimize=True)
                sw.destroy(); self.show_minimal_info("儲存成功", f"檔案已成功儲存！\n路徑：{p}")
        RoundedButton(sw, "確認儲存", save, color=self.color_accent, width=120).pack(pady=15)

    def show_minimal_info(self, title, msg):
        win = tk.Toplevel(self.root); win.title(title); win.geometry("450x180"); win.configure(bg="#1C1C1E"); win.transient(self.root); win.grab_set()
        tk.Label(win, text=msg, bg="#1C1C1E", fg="white", font=("微軟正黑體", 10), wraplength=400, justify=tk.LEFT, pady=30).pack()
        RoundedButton(win, "確定", win.destroy, width=80).pack(pady=10)

    def paint(self, x, y):
        draw = ImageDraw.Draw(self.mask); color = 255 if self.tool_mode == "brush_restore" else 0
        r = self.brush_size / self.get_total_scale(); draw.ellipse([x-r, y-r, x+r, y+r], fill=color); self.update_display_fast()

    def load_image(self):
        p = filedialog.askopenfilename(filetypes=[("Images", "*.jpg *.jpeg *.png *.webp")])
        if p: self.original_img = Image.open(p).convert("RGB"); self.mask = Image.new("L", self.original_img.size, 255); self.history = []; self.reset_view(); self.btn_ai.set_state("normal")

    def run_ai(self):
        try:
            self.save_to_history(); self.root.config(cursor="watch"); self.root.update()
            buf = io.BytesIO(); self.original_img.save(buf, format='PNG'); dat = remove(buf.getvalue(), session=self.session, only_mask=True)
            self.mask = Image.open(io.BytesIO(dat)).convert("L"); self.update_display()
        except Exception as e: messagebox.showerror("Error", f"AI Processing failed: {e}")
        finally: self.root.config(cursor="")

    def pan_start(self, event): self.canvas_right.scan_mark(event.x, event.y); self.canvas_left.scan_mark(event.x, event.y)
    def pan_move(self, event): self.canvas_right.scan_dragto(event.x, event.y, gain=1); self.canvas_left.scan_dragto(event.x, event.y, gain=1); self.draw_brush_cursor_at_last_pos()
    def reset_view(self): self.zoom_level = 1.0; self.update_display()
    def undo(self): 
        if self.history: self.mask = self.history.pop(); self.update_display()
    def save_to_history(self):
        if self.mask:
            self.history.append(self.mask.copy())
            if len(self.history) > 30: self.history.pop(0)

    def handle_zoom(self, event):
        if self.original_img is None: return
        f = 1.1 if event.delta > 0 else 0.9; self.zoom_level = max(0.1, min(20, self.zoom_level * f)); self.update_display()

    def update_display(self):
        if self.original_img is None: return
        w, h = self.original_img.size; ts = self.get_total_scale(); ns = (int(w*ts), int(h*ts))
        cw, ch = self.canvas_right.winfo_width() or 600, self.canvas_right.winfo_height() or 800
        ld = self.original_img.resize(ns, Image.Resampling.LANCZOS); self.canvas_left.delete("all")
        self.tk_left = ImageTk.PhotoImage(ld); self.canvas_left.create_image(cw//2, ch//2, image=self.tk_left)
        self.update_display_fast()
        for c in [self.canvas_left, self.canvas_right]: c.config(scrollregion=c.bbox("all"))

    def update_display_fast(self):
        if self.original_img is None: return
        w, h = self.original_img.size; ts = self.get_total_scale(); ns = (int(w*ts), int(h*ts))
        res = self.original_img.copy().convert("RGBA"); res.putalpha(self.mask); rd = res.resize(ns, Image.Resampling.NEAREST)
        bg = self.create_checkerboard(ns[0], ns[1]); bg.paste(rd, (0, 0), rd)
        self.tk_right = ImageTk.PhotoImage(bg); self.canvas_right.delete("img")
        self.canvas_right.create_image(self.canvas_right.winfo_width()//2, self.canvas_right.winfo_height()//2, image=self.tk_right, tags="img"); self.canvas_right.tag_lower("img")

    def create_checkerboard(self, w, h):
        c = Image.new("RGB", (w, h), "#666666"); d = ImageDraw.Draw(c); s = 15
        for i in range(0, w, s*2):
            for j in range(0, h, s*2):
                d.rectangle([i, j, i+s-1, j+s-1], fill="#777777"); d.rectangle([i+s, j+s, i+s*2-1, j+s*2-1], fill="#777777")
        return c

    def get_total_scale(self):
        if self.original_img is None: return 1.0
        return min(self.canvas_right.winfo_width()/self.original_img.size[0], self.canvas_right.winfo_height()/self.original_img.size[1]) * self.zoom_level

    def get_img_coords(self, sx, sy):
        w, h = self.original_img.size; ts = self.get_total_scale()
        cw, ch = self.canvas_right.winfo_width() // 2, self.canvas_right.winfo_height() // 2
        ax, ay = self.canvas_right.canvasx(sx) - (cw - int(w*ts)//2), self.canvas_right.canvasy(sy) - (ch - int(h*ts)//2)
        return int(ax/ts), int(ay/ts)

    def move_view(self, dx, dy):
        self.canvas_right.xview_scroll(dx, "units"); self.canvas_right.yview_scroll(dy, "units")
        self.canvas_left.xview_scroll(dx, "units"); self.canvas_left.yview_scroll(dy, "units"); self.draw_brush_cursor_at_last_pos()

if __name__ == "__main__":
    root = tk.Tk(); app = XiangTeacherProAppWin(root); root.mainloop()

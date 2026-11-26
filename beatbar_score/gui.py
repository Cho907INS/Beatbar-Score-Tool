"""BeatBar 难度评分器 · 图形界面（tkinter，无需额外依赖）。

从源码运行：
    python beatbar_score/gui.py

打包 exe：
    build_exe.bat
"""
from __future__ import annotations

import os
import sys
import traceback

import tkinter as tk
import webbrowser
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText

try:
    from . import card, data, i18n, model
except ImportError:                                    # 作为脚本直接运行
    _parent = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, _parent)
    from beatbar_score import card, data, i18n, model

APP_TITLE = "BeatBar Difficulty Scorer"
BG = "#1e2228"
FG = "#e8eaed"
SUB = "#9aa0a6"
ACCENT = "#3fa7d6"


def score_path(path, bpm=None, total=None):
    ext = os.path.splitext(path)[1].lower()
    if ext == ".rbarproj":
        d = data.load_rbarproj(path)
        _grid, raw = model.rate_from_notes(d["times"], d["T"])
        name = d["name"]
    elif ext in (".csv", ".txt"):
        d = data.load_csv(path)
        _grid, raw = model.rate_from_intervals(
            d["rows"], bpm if bpm else d["bpm"],
            total if total else d["total"])
        name = d["name"]
    else:
        raise ValueError(ext)
    r = model.cap_rate(raw)
    return name, model.metrics(r, raw)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.lang = "en"
        self.paths = []
        self.geometry("880x680")
        self.minsize(760, 560)
        self.configure(bg=BG)
        self._build()
        self._apply_lang()

    # ---------------------------------------------------------- 构建
    def _build(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TFrame", background=BG)
        style.configure("TLabel", background=BG, foreground=FG,
                        font=("Microsoft YaHei UI", 10))
        style.configure("Sub.TLabel", foreground=SUB,
                        font=("Microsoft YaHei UI", 9))
        style.configure("Title.TLabel", font=("Microsoft YaHei UI", 16, "bold"))
        style.configure("TButton", font=("Microsoft YaHei UI", 10))
        style.configure("Accent.TButton", font=("Microsoft YaHei UI", 11, "bold"))
        style.configure("TCombobox", font=("Microsoft YaHei UI", 10))

        top = ttk.Frame(self, padding=(16, 14, 16, 8))
        top.pack(fill="x")
        self.lbl_title = ttk.Label(top, text="", style="Title.TLabel")
        self.lbl_title.pack(side="left")
        self.lbl_sub = ttk.Label(top, text="", style="Sub.TLabel")
        self.lbl_sub.pack(side="left", padx=(12, 0), pady=(6, 0))

        self.lbl_lang = ttk.Label(top, text="", style="Sub.TLabel")
        self.lbl_lang.pack(side="right", padx=(8, 6))
        self.cmb_lang = ttk.Combobox(top, state="readonly", width=10,
                                     values=list(i18n.LANG_NAMES.values()))
        self.cmb_lang.current(0)
        self.cmb_lang.pack(side="right")
        self.cmb_lang.bind("<<ComboboxSelected>>", self._on_lang)

        bar = ttk.Frame(self, padding=(16, 0, 16, 6))
        bar.pack(fill="x")
        self.btn_choose = ttk.Button(bar, command=self._choose)
        self.btn_choose.pack(side="left")
        self.lbl_files = ttk.Label(bar, text="", style="Sub.TLabel")
        self.lbl_files.pack(side="left", padx=12)

        opt = ttk.Frame(self, padding=(16, 0, 16, 6))
        opt.pack(fill="x")
        self.lbl_bpm = ttk.Label(opt, text="", style="Sub.TLabel")
        self.lbl_bpm.pack(side="left")
        self.e_bpm = ttk.Entry(opt, width=10)
        self.e_bpm.pack(side="left", padx=(6, 18))
        self.lbl_total = ttk.Label(opt, text="", style="Sub.TLabel")
        self.lbl_total.pack(side="left")
        self.e_total = ttk.Entry(opt, width=12)
        self.e_total.pack(side="left", padx=(6, 18))

        helpf = ttk.Frame(self, padding=(16, 0, 16, 6))
        helpf.pack(fill="x")
        self.lbl_per8 = ttk.Label(helpf, text="", style="Sub.TLabel")
        self.lbl_per8.pack(anchor="w")
        self.lbl_proj = ttk.Label(helpf, text="", style="Sub.TLabel",
                                  foreground="#3fa7d6", cursor="hand2")
        self.lbl_proj.pack(anchor="w")
        self.lbl_proj.bind("<Button-1>", lambda _e: webbrowser.open(
            "https://github.com/Tez192780/RhythmBar-Studio-for-FapHero"))

        run = ttk.Frame(self, padding=(16, 0, 16, 8))
        run.pack(fill="x")
        self.btn_run = ttk.Button(run, command=self._run, style="Accent.TButton")
        self.btn_run.pack(side="left")
        self.lbl_tip = ttk.Label(run, text="", style="Sub.TLabel")
        self.lbl_tip.pack(side="left", padx=12)

        mid = ttk.Frame(self, padding=(16, 0, 16, 8))
        mid.pack(fill="both", expand=True)
        self.txt = ScrolledText(mid, wrap="none", bg="#14171b", fg=FG,
                                insertbackground=FG, relief="flat",
                                font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True)

        bot = ttk.Frame(self, padding=(16, 0, 16, 14))
        bot.pack(fill="x")
        self.btn_copy = ttk.Button(bot, command=self._copy)
        self.btn_copy.pack(side="left")
        self.btn_save = ttk.Button(bot, command=self._save)
        self.btn_save.pack(side="left", padx=8)

    # ---------------------------------------------------------- 语言
    def _on_lang(self, _e=None):
        self.lang = i18n.LANGS[self.cmb_lang.current()]
        self._apply_lang()
        if self.paths:
            self._run()

    def _apply_lang(self):
        g = lambda k, **kw: i18n.t(self.lang, k, **kw)   # noqa: E731
        self.title(g("title"))
        self.lbl_title.configure(text=g("title"))
        self.lbl_sub.configure(text=g("subtitle"))
        self.lbl_lang.configure(text=g("lang"))
        self.btn_choose.configure(text=g("choose"))
        self.lbl_bpm.configure(text=g("bpm"))
        self.lbl_total.configure(text=g("total"))
        self.btn_run.configure(text=g("run"))
        self.btn_copy.configure(text=g("copy"))
        self.btn_save.configure(text=g("save"))
        self.lbl_tip.configure(text=g("tip"))
        self.lbl_per8.configure(text=g("help_per8"))
        self.lbl_proj.configure(text=g("help_proj"))
        self._update_files_label()

    def _update_files_label(self):
        g = lambda k, **kw: i18n.t(self.lang, k, **kw)   # noqa: E731
        if self.paths:
            self.lbl_files.configure(text=g("chosen", n=len(self.paths)))
        else:
            self.lbl_files.configure(text=g("none"))

    # ---------------------------------------------------------- 动作
    def _choose(self):
        ft = [(i18n.t(self.lang, "filetypes"), "*.csv *.CSV *.txt *.rbarproj"),
              ("CSV", "*.csv"), ("rbarproj", "*.rbarproj"), ("*", "*.*")]
        sel = filedialog.askopenfilenames(title=i18n.t(self.lang, "choose"),
                                          filetypes=ft)
        if sel:
            self.paths = list(sel)
            self._update_files_label()

    def _run(self):
        g = lambda k, **kw: i18n.t(self.lang, k, **kw)   # noqa: E731
        if not self.paths:
            messagebox.showwarning(g("title"), g("err_no_file"))
            return
        try:
            bpm = float(self.e_bpm.get()) if self.e_bpm.get().strip() else None
        except ValueError:
            bpm = None
        try:
            total = float(self.e_total.get()) if self.e_total.get().strip() else None
        except ValueError:
            total = None

        rows, lines = [], []
        for p in self.paths:
            try:
                name, m = score_path(p, bpm, total)
            except Exception as e:
                lines.append(f"[{g('err_parse')}] {os.path.basename(p)}: {e}")
                continue
            rows.append((name, m))
            if len(self.paths) > 1:
                continue
            lines.append(card.render(m, name, self.lang))

        if len(rows) > 1:
            lines.append(card.table(rows, self.lang))
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", "\n".join(lines) if lines else g("err_no_file"))

    def _copy(self):
        self.clipboard_clear()
        self.clipboard_append(self.txt.get("1.0", "end").strip())
        self.lbl_tip.configure(text=i18n.t(self.lang, "copied"))

    def _save(self):
        p = filedialog.asksaveasfilename(
            defaultextension=".txt", filetypes=[("Text", "*.txt")])
        if not p:
            return
        with open(p, "w", encoding="utf-8") as f:
            f.write(self.txt.get("1.0", "end").strip() + "\n")
        self.lbl_tip.configure(text=i18n.t(self.lang, "saved", p=p))


def _app_dir():
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def _crash(exc_type, exc, tb):
    """把完整堆栈写到 exe 旁边，并弹出对话框。"""
    import traceback
    text = "".join(traceback.format_exception(exc_type, exc, tb))
    try:
        with open(os.path.join(_app_dir(), "BeatBarScore-error.log"),
                  "w", encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass
    try:
        with open(os.path.join(os.environ.get("TEMP", "."),
                               "BeatBarScore-error.log"), "w",
                  encoding="utf-8") as f:
            f.write(text)
    except Exception:
        pass
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, text[:1500], "BeatBarScore", 0x10)
    except Exception:
        pass


def selftest():
    """无窗口自检：验证模型与打包是否完整。结果写到临时文件与 stdout。"""
    import json
    import tempfile

    rows = [(0.0, 20.0, 40.0, None), (20.0, 40.0, 60.0, None)]
    _grid, raw = model.rate_from_intervals(rows)
    r = model.cap_rate(raw)
    m = model.metrics(r, raw)
    report = {"ok": True, "lang": list(i18n.LANGS), "metrics": m}
    path = os.path.join(tempfile.gettempdir(), "beatbar_selftest.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=1)
    if sys.stdout is not None:
        print(json.dumps(report, ensure_ascii=False))
    return 0


def main():
    sys.excepthook = _crash
    if "--selftest" in sys.argv:
        raise SystemExit(selftest())
    if "--selftest-gui" in sys.argv:
        app = App()
        app.update()
        app.destroy()
        if sys.stdout is not None:
            print("gui ok")
        return
    try:
        App().mainloop()
    except Exception:
        import traceback
        _crash(*sys.exc_info())
        if sys.stdout is not None:
            traceback.print_exc()


if __name__ == "__main__":
    main()


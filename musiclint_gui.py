#!/usr/bin/env python3
"""
musiclint GUI — optional graphical interface for musiclint.
Run with:  python musiclint_gui.py
The CLI (musiclint.py) is unaffected by this file.
"""

import builtins
import os
import queue
import re
import sys
import threading
import webbrowser
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext

# Ensure the repo root is importable so plugins/* can be found.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

_URL_RE = re.compile(r'https?://[^\s"\'<>]+')


# ── Thread-aware stdout shim ──────────────────────────────────────────────────

class _GUIStream:
    """Sends writes from the processing thread to the GUI queue; others go to real stdout."""

    def __init__(self, io_q: queue.Queue, get_thread_id, orig_stdout):
        self._q = io_q
        self._get_tid = get_thread_id
        self._orig = orig_stdout

    def write(self, text: str):
        if threading.current_thread().ident == self._get_tid():
            self._q.put(('text', text))
        else:
            self._orig.write(text)

    def flush(self):
        self._orig.flush()

    def isatty(self):
        return False


# ── Prompt classification ─────────────────────────────────────────────────────

def _quick_buttons(prompt: str):
    """Return (label, value) pairs for known musiclint prompts, or []."""
    p = prompt.strip()
    if re.search(r'\[y/n\]', p, re.I):
        return [('Yes', 'y'), ('No', 'n')]
    if re.search(r'\[c/r/s/q\]', p, re.I):
        return [('Continue', 'c'), ('Different release', 'r'), ('Skip', 's'), ('Quit', 'q')]
    if re.search(r'\[f/d/t\]', p, re.I):
        return [('Keep file', 'f'), ('Use DB', 'd'), ('Type custom', 't')]
    m = re.search(r'\[1-(\d+)/s/m/q\]', p, re.I)
    if m:
        n = int(m.group(1))
        btns = [(str(i), str(i)) for i in range(1, n + 1)]
        btns += [('Skip', 's'), ('Manual search', 'm'), ('Quit', 'q')]
        return btns
    return []


# ── GUI application ───────────────────────────────────────────────────────────

class MusicLintGUI:
    _PAD = 8
    _MONO = ('Menlo', 12) if sys.platform == 'darwin' else ('Courier', 11)

    def __init__(self, root: tk.Tk):
        self.root = root
        root.title('musiclint')
        root.minsize(760, 580)

        self._io_q: queue.Queue = queue.Queue()
        self._input_event = threading.Event()
        self._input_response = ''
        self._proc_tid = None
        self._orig_input = builtins.input
        self._orig_stdout = sys.stdout
        self._gui_stream = _GUIStream(self._io_q, lambda: self._proc_tid, sys.stdout)

        self._build_ui()
        self._poll()

    # ── UI construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        p = self._PAD

        # ── Settings ─────────────────────────────────────────────────────────
        sf = tk.LabelFrame(self.root, text=' Settings ', padx=p, pady=p)
        sf.pack(fill='x', padx=p, pady=(p, 0))
        sf.columnconfigure(1, weight=1)

        # Library path
        tk.Label(sf, text='Music library:').grid(row=0, column=0, sticky='w')
        self._lib_var = tk.StringVar()
        tk.Entry(sf, textvariable=self._lib_var).grid(
            row=0, column=1, sticky='ew', padx=(p, 4)
        )
        tk.Button(sf, text='Browse…', command=self._browse).grid(row=0, column=2)

        # Formats
        tk.Label(sf, text='Formats:').grid(row=1, column=0, sticky='w', pady=(p // 2, 0))
        ff = tk.Frame(sf)
        ff.grid(row=1, column=1, sticky='w')
        self._mp3_var  = tk.BooleanVar()
        self._flac_var = tk.BooleanVar()
        self._ogg_var  = tk.BooleanVar()
        self._all_var  = tk.BooleanVar()
        tk.Checkbutton(ff, text='MP3',  variable=self._mp3_var,  command=self._on_fmt).pack(side='left')
        tk.Checkbutton(ff, text='FLAC', variable=self._flac_var, command=self._on_fmt).pack(side='left')
        tk.Checkbutton(ff, text='OGG',  variable=self._ogg_var,  command=self._on_fmt).pack(side='left')
        tk.Checkbutton(ff, text='All',  variable=self._all_var,  command=self._on_all).pack(
            side='left', padx=(12, 0)
        )

        # Database
        tk.Label(sf, text='Database:').grid(row=2, column=0, sticky='w', pady=(p // 2, 0))
        df = tk.Frame(sf)
        df.grid(row=2, column=1, sticky='w')
        self._db_var = tk.StringVar(value='musicbrainz')
        for val, lbl in [('musicbrainz', 'MusicBrainz'), ('discogs', 'Discogs')]:
            tk.Radiobutton(df, text=lbl, variable=self._db_var, value=val).pack(side='left')

        # Verbosity
        tk.Label(sf, text='Verbosity:').grid(row=3, column=0, sticky='w', pady=(p // 2, 0))
        vf = tk.Frame(sf)
        vf.grid(row=3, column=1, sticky='w')
        self._verb_var = tk.IntVar(value=0)
        for v, lbl in [(0, '0 – quiet'), (1, '1'), (2, '2'), (3, '3 – verbose')]:
            tk.Radiobutton(vf, text=lbl, variable=self._verb_var, value=v).pack(side='left')

        # Start / Stop
        bf = tk.Frame(sf)
        bf.grid(row=4, column=0, columnspan=3, sticky='e', pady=(p, 0))
        self._start_btn = tk.Button(bf, text='Start', width=10, command=self._start)
        self._start_btn.pack(side='left', padx=(0, 4))
        self._stop_btn = tk.Button(bf, text='Stop', width=10, command=self._stop, state='disabled')
        self._stop_btn.pack(side='left')

        # ── Output ────────────────────────────────────────────────────────────
        of = tk.LabelFrame(self.root, text=' Output ', padx=p, pady=p)
        of.pack(fill='both', expand=True, padx=p, pady=p)
        self._out = scrolledtext.ScrolledText(
            of, font=self._MONO, state='disabled', wrap='word',
            bg='#1e1e1e', fg='#d4d4d4', insertbackground='white',
            selectbackground='#264f78',
        )
        self._out.tag_config('url', foreground='#4ec9b0', underline=True)
        self._out.tag_bind('url', '<Button-1>', self._url_click)
        self._out.tag_bind('url', '<Enter>', lambda _: self._out.config(cursor='hand2'))
        self._out.tag_bind('url', '<Leave>', lambda _: self._out.config(cursor=''))
        self._out.pack(fill='both', expand=True)

        # ── Input row (shown on demand) ───────────────────────────────────────
        self._input_frame = tk.Frame(self.root, bd=1, relief='sunken')

        self._prompt_lbl = tk.Label(
            self._input_frame, text='', font=self._MONO,
            fg='#569cd6', anchor='w', justify='left',
        )
        self._prompt_lbl.pack(side='left', padx=(p, 4), pady=p // 2)

        self._btn_frame = tk.Frame(self._input_frame)
        self._btn_frame.pack(side='left')

        self._input_entry = tk.Entry(self._input_frame, font=self._MONO, width=30)
        self._input_entry.pack(side='left', padx=4)
        self._input_entry.bind('<Return>', lambda _: self._submit_text())

        tk.Button(self._input_frame, text='Submit', command=self._submit_text).pack(
            side='left', padx=(0, p)
        )

    # ── Widget callbacks ──────────────────────────────────────────────────────

    def _browse(self):
        path = filedialog.askdirectory(title='Select music library folder')
        if path:
            self._lib_var.set(path)

    def _on_fmt(self):
        self._all_var.set(
            self._mp3_var.get() and self._flac_var.get() and self._ogg_var.get()
        )

    def _on_all(self):
        v = self._all_var.get()
        self._mp3_var.set(v)
        self._flac_var.set(v)
        self._ogg_var.set(v)

    # ── Processing ────────────────────────────────────────────────────────────

    def _start(self):
        lib = self._lib_var.get().strip()
        if not lib:
            messagebox.showerror('musiclint', 'Please select a music library folder.')
            return
        if not os.path.isdir(lib):
            messagebox.showerror('musiclint', f'Not a valid directory:\n{lib}')
            return

        do_mp3  = self._mp3_var.get()  or self._all_var.get()
        do_flac = self._flac_var.get() or self._all_var.get()
        do_ogg  = self._ogg_var.get()  or self._all_var.get()
        if not (do_mp3 or do_flac or do_ogg):
            messagebox.showerror('musiclint', 'Select at least one file format.')
            return

        self._out_clear()
        self._start_btn.config(state='disabled')
        self._stop_btn.config(state='normal')
        sys.stdout = self._gui_stream
        builtins.input = self._gui_input

        t = threading.Thread(
            target=self._worker,
            args=(lib, do_mp3, do_flac, do_ogg,
                  self._db_var.get(), self._verb_var.get()),
            daemon=True,
        )
        t.start()
        self._proc_tid = t.ident

    def _stop(self):
        # Unblock any waiting input() so the thread can reach its except/finally.
        self._input_response = 'q'
        self._input_event.set()

    def _worker(self, lib, mp3, flac, ogg, database, verbosity):
        try:
            import logging
            logging.basicConfig(
                filename='musiclint.log',
                format='%(asctime)s - %(message)s',
                datefmt='%m/%d/%Y %I:%M:%S %p',
                level=logging.INFO,
                force=True,
            )
            logging.info('*** GUI start processing ***')

            if mp3:
                from plugins.processMp3 import processMP3Files
                processMP3Files(lib, verbosity, database)
            if flac:
                from plugins.processFlac import processFLACFiles
                processFLACFiles(lib, verbosity, database)
            if ogg:
                from plugins.processOgg import processOGGFiles
                processOGGFiles(lib, verbosity, database)

        except SystemExit as exc:
            if exc.code not in (0, None):
                self._io_q.put(('text', f'\n[Exit: {exc.code}]\n'))
        except Exception as exc:
            import traceback
            self._io_q.put(('text', f'\n[Error: {exc}]\n{traceback.format_exc()}\n'))
        finally:
            self._io_q.put(('done', None))

    # ── I/O bridge ────────────────────────────────────────────────────────────

    def _gui_input(self, prompt: str = '') -> str:
        """Replacement for builtins.input() used only by the processing thread."""
        if threading.current_thread().ident != self._proc_tid:
            return self._orig_input(prompt)
        self._input_event.clear()
        self._io_q.put(('input_needed', prompt))
        self._input_event.wait()
        result = self._input_response
        self._input_response = ''
        return result

    def _submit_text(self):
        self._do_submit(self._input_entry.get().strip())

    def _submit_btn(self, value: str):
        self._do_submit(value)

    def _do_submit(self, value: str):
        self._input_entry.delete(0, 'end')
        self._hide_input()
        self._out_append(value + '\n')
        self._input_response = value
        self._input_event.set()

    def _show_input(self, prompt: str):
        for w in self._btn_frame.winfo_children():
            w.destroy()
        self._prompt_lbl.config(text=prompt)
        for label, val in _quick_buttons(prompt):
            v = val
            tk.Button(
                self._btn_frame, text=label,
                command=lambda v=v: self._submit_btn(v),
            ).pack(side='left', padx=2, pady=2)
        self._input_frame.pack(fill='x', padx=self._PAD, pady=(0, self._PAD))
        self._input_entry.focus_set()

    def _hide_input(self):
        self._input_frame.pack_forget()

    # ── Output helpers ────────────────────────────────────────────────────────

    def _out_append(self, text: str):
        self._out.config(state='normal')
        # Record the position before inserting so we can tag URLs within the new block.
        insert_at = self._out.index('end-1c')
        self._out.insert('end', text)
        for m in _URL_RE.finditer(text):
            url = m.group()
            s = f'{insert_at}+{m.start()}c'
            e = f'{insert_at}+{m.end()}c'
            self._out.tag_add('url', s, e)
            if 'discogs.com/oauth/authorize' in url:
                webbrowser.open(url)
                self._out.insert('end', '  [opened in browser]\n')
        self._out.see('end')
        self._out.config(state='disabled')

    def _out_clear(self):
        self._out.config(state='normal')
        self._out.delete('1.0', 'end')
        self._out.config(state='disabled')

    def _url_click(self, event):
        idx = self._out.index(f'@{event.x},{event.y}')
        ranges = self._out.tag_ranges('url')
        for i in range(0, len(ranges), 2):
            if (self._out.compare(ranges[i], '<=', idx) and
                    self._out.compare(idx, '<=', ranges[i + 1])):
                webbrowser.open(self._out.get(ranges[i], ranges[i + 1]))
                break

    # ── Poll loop ─────────────────────────────────────────────────────────────

    def _poll(self):
        try:
            while True:
                kind, data = self._io_q.get_nowait()
                if kind == 'text':
                    self._out_append(data)
                elif kind == 'input_needed':
                    self._show_input(data)
                elif kind == 'done':
                    self._on_done()
        except queue.Empty:
            pass
        self.root.after(50, self._poll)

    def _on_done(self):
        sys.stdout = self._orig_stdout
        builtins.input = self._orig_input
        self._proc_tid = None
        self._start_btn.config(state='normal')
        self._stop_btn.config(state='disabled')
        self._hide_input()
        self._out_append('\n─── Processing complete ───\n')


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    root = tk.Tk()
    try:
        style = tk.ttk.Style(root)
        if sys.platform == 'darwin':
            style.theme_use('aqua')
        elif sys.platform == 'win32':
            style.theme_use('vista')
        else:
            style.theme_use('clam')
    except Exception:
        pass
    app = MusicLintGUI(root)  # noqa: F841
    root.mainloop()


if __name__ == '__main__':
    main()

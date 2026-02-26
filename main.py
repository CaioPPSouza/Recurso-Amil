from __future__ import annotations

import tkinter as tk

from app.ui import AutomationApp


def main() -> None:
    root = tk.Tk()
    AutomationApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()


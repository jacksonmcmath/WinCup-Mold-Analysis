import re
import tkinter as tk
from tkinter import ttk

BRI_DELTA = 5
CON_DELTA = 10
SHA_DELTA = 10
SHU_DELTA = 100
SHU_MIN = 1000
SHU_MAX = 3000

BRI_EXPLAIN = 'How bright the image is.\nHigher is brighter'
CON_EXPLAIN = 'The scale of difference between\nblack and white.\nHigher is more difference.'
SHA_EXPLAIN = 'The harshness of edges.\nHigher is sharper.'
SHU_EXPLAIN = 'How fast the image is captured\nmeasured in microseconds.\nHigher is slower.'

class BrightnessFrame(ttk.Frame):
    """
    This class builds a frame for manipulating the 'brightness' setting.

    Attributes:
        master: The master or parent widget for this frame.
        value: The value for the 'brightness' setting.
    """
    def __init__(self, master, var, *args, **kwargs):
        """
        Inits BrightnessFrame with master and value.
        Creates entry and buttons for 'brightness' value.
        """
        ttk.Frame.__init__(self, master, *args, **kwargs)
        vcmd = (master.register(self.onValidate), '%P')
        self.master = master
        self.value = var

        self.label = ttk.Label(self, text='Brightness:', font='-weight bold')
        self.explain = ttk.Label(self, text=BRI_EXPLAIN, font='-size 10')
        self.buttona = ttk.Button(self, text='+', command=self.add, width=2)
        self.buttons = ttk.Button(self, text='-', command=self.sub, width=2)
        self.entry = ttk.Entry(self, width=5, validate='all',
                               validatecommand=vcmd, textvariable=self.value)

        self.label.grid(row=1, column=1, sticky='w', columnspan=5)
        self.explain.grid(row=2, column=1, sticky='w', columnspan=5)
        self.entry.grid(row=3, column=2)
        self.buttona.grid(row=3, column=3)
        self.buttons.grid(row=3, column=4)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(5, weight=1)

    def add(self):
        """Adds BRI_DELTA to value and updates entry."""
        val = int(self.value.get())
        if val >= 100 - BRI_DELTA:
            val = 100
        elif val < 100 - BRI_DELTA and val >= 0:
            val += BRI_DELTA
        else:
            val = 0
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def sub(self):
        """Subtracts BRI_DELTA from value and updates entry."""
        val = int(self.value.get())
        if val > 100:
            val = 100
        elif val <= 100 and val >= BRI_DELTA + 0:
            val -= BRI_DELTA
        else:
            val = 0
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def onValidate(self, value):
        """Checks if 0 <= value <= 100"""
        p = re.compile('^[0-9]$|^[1-9][0-9]$|^100$')
        if p.match(value):
            return True
        return False

class ContrastFrame(ttk.Frame):
    """
    This class builds a frame for manipulating the 'contrast' setting.

    Attributes:
        master: The master or parent widget for this frame.
        value: The value for the 'contrast' setting.
    """
    def __init__(self, master, var, *args, **kwargs):
        """
        Inits ContrastFrame with master and value.
        Creates entry and buttons for 'contrast' value.
        """
        ttk.Frame.__init__(self, master, *args, **kwargs)
        vcmd = (master.register(self.onValidate), '%P')
        self.master = master
        self.value = var

        self.label = ttk.Label(self, text='Contrast:', font='-weight bold')
        self.explain = ttk.Label(self, text=CON_EXPLAIN, font='-size 10')
        self.buttona = ttk.Button(self, text='+', command=self.add, width=2)
        self.buttons = ttk.Button(self, text='-', command=self.sub, width=2)
        self.entry = ttk.Entry(self, width=5, validate='all',
                               validatecommand=vcmd, textvariable=self.value)

        self.label.grid(row=1, column=1, sticky='w', columnspan=5)
        self.explain.grid(row=2, column=1, sticky='w', columnspan=5)
        self.entry.grid(row=3, column=2)
        self.buttona.grid(row=3, column=3)
        self.buttons.grid(row=3, column=4)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(5, weight=1)

    def add(self):
        """Adds 10 to value and updates entry."""
        val = int(self.value.get())
        if val >= 100 - CON_DELTA:
            val = 100
        elif val < 100 - CON_DELTA and val >= -100:
            val += CON_DELTA
        else:
            val = 0
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def sub(self):
        """Subtracts 10 from value and updates entry."""
        val = int(self.value.get())
        if val > 100:
            val = 100
        elif val <= 100 and val >= CON_DELTA - 100:
            val -= CON_DELTA
        else:
            val = -100
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def onValidate(self, value):
        """Checks if -100 <= value <= 100"""
        p = re.compile('^0$|^-?[1-9]$|^-?[1-9][0-9]$|^-?100$')
        if p.match(value):
            return True
        return False

class RotationFrame(ttk.Frame):
    """
    This class builds a frame for manipulating the 'rotation' setting.

    Attributes:
        master: The master or parent widget for this frame.
        value: The value for the 'rotation' setting.
    """
    def __init__(self, master, var, *args, **kwargs):
        """
        Inits RotationFrame with master and value.
        Creates radio buttons for 'rotation' options.
        """
        ttk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        self.value = var

        self.label = ttk.Label(self, text='Rotation:', font='-weight bold')
        self.rb1 = ttk.Radiobutton(self, text='0 deg', value=0,
                                   variable=self.value)
        self.rb2 = ttk.Radiobutton(self, text='90 deg', value=90,
                                   variable=self.value)
        self.rb3 = ttk.Radiobutton(self, text='180 deg', value=180,
                                   variable=self.value)
        self.rb4 = ttk.Radiobutton(self, text='270 deg', value=270,
                                   variable=self.value)

        self.label.grid(row=1, column=1, sticky='w', columnspan=2)
        self.rb1.grid(row=2, column=2, sticky='w')
        self.rb2.grid(row=3, column=2, sticky='w')
        self.rb3.grid(row=4, column=2, sticky='w')
        self.rb4.grid(row=5, column=2, sticky='w')

        self.rowconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(3, weight=1)

class SharpnessFrame(ttk.Frame):
    """
    This class builds a frame for manipulating the 'sharpness' setting.

    Attributes:
        master: The master or parent widget for this frame.
        value: The value for the 'sharpness' setting.
    """
    def __init__(self, master, var, *args, **kwargs):
        """
        Inits SharpnessFrame with master and value.
        Creates entry and buttons for 'sharpness' value.
        """
        ttk.Frame.__init__(self, master, *args, **kwargs)
        vcmd = (master.register(self.onValidate), '%P')
        self.master = master
        self.value = var

        self.label = ttk.Label(self, text='Sharpness:', font='-weight bold')
        self.explain = ttk.Label(self, text=SHA_EXPLAIN, font='-size 10')
        self.buttona = ttk.Button(self, text='+', command=self.add, width=2)
        self.buttons = ttk.Button(self, text='-', command=self.sub, width=2)
        self.entry = ttk.Entry(self, width=5, validate='all',
                               validatecommand=vcmd, textvariable=self.value)

        self.label.grid(row=1, column=1, sticky='w', columnspan=5)
        self.explain.grid(row=2, column=1, sticky='w', columnspan=5)
        self.entry.grid(row=3, column=2)
        self.buttona.grid(row=3, column=3)
        self.buttons.grid(row=3, column=4)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(5, weight=1)

    def add(self):
        """Adds 10 to value and updates entry."""
        val = int(self.value.get())
        if val >= 100 - SHA_DELTA:
            val = 100
        elif val < 100 - SHA_DELTA and val >= -100:
            val += SHA_DELTA
        else:
            val =-100
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def sub(self):
        """Subtracts 10 from value and updates entry."""
        val = int(self.value.get())
        if val > 100:
            val = 100
        elif val <= 100 and val >= SHA_DELTA - 100:
            val -= SHA_DELTA
        else:
            val = 0
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def onValidate(self, value):
        """Checks if -100 <= value <= 100"""
        p = re.compile('^0$|^-?[1-9]$|^-?[1-9][0-9]$|^-?100$')
        if p.match(value):
            return True
        return False

class ShutterSpeedFrame(ttk.Frame):
    """
    This class builds a frame for manipulating the 'shutter_speed' setting.

    Attributes:
        master: The master or parent widget for this frame.
        value: The value for the 'shutter_speed' setting.
    """
    def __init__(self, master, var, *args, **kwargs):
        """
        Inits ShutterSpeedFrame with master and value.
        Creates entry and buttons for 'shutter_speed' value.
        """
        ttk.Frame.__init__(self, master, *args, **kwargs)
        vcmd = (master.register(self.onValidate), '%P')
        self.master = master
        self.value = var

        self.label = ttk.Label(self, text='Shutter Speed:', font='-weight bold')
        self.explain = ttk.Label(self, text=SHU_EXPLAIN, font='-size 10')
        self.buttona = ttk.Button(self, text='+', command=self.add, width=2)
        self.buttons = ttk.Button(self, text='-', command=self.sub, width=2)
        self.entry = ttk.Entry(self, width=5, validate='all',
                               validatecommand=vcmd, textvariable=self.value)

        self.label.grid(row=1, column=1, sticky='w', columnspan=5)
        self.explain.grid(row=2, column=1, sticky='w', columnspan=5)
        self.entry.grid(row=3, column=2)
        self.buttona.grid(row=3, column=3)
        self.buttons.grid(row=3, column=4)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(4, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(5, weight=1)

    def add(self):
        """Adds SHU_DELTA to value and updates entry."""
        val = int(self.value.get())
        if val >= SHU_MAX - SHU_DELTA:
            val = SHU_MAX
        elif val < SHU_MAX - SHU_DELTA and val >= SHU_MIN:
            val += SHU_DELTA
        else:
            val = SHU_MIN
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def sub(self):
        """Subtracts SHU_DELTA from value and updates entry."""
        val = int(self.value.get())
        if val > SHU_MAX:
            val = SHU_MAX
        elif val <= SHU_MAX and val >= SHU_DELTA + SHU_MIN:
            val -= SHU_DELTA
        else:
            val = vSHU_MIN
        self.entry.delete(0, 'end')
        self.entry.insert(0, val)
        self.value.set(val)

    def onValidate(self, value):
        """Checks if SHU_MIN <= value <= SHU_MAX"""
        if int(value) >= SHU_MIN and int(value) <= SHU_MAX:
            return True
        return False

if __name__ == '__main__':
    root = tk.Tk()
    bri = BrightnessFrame(root, tk.IntVar())
    con = ContrastFrame(root, tk.IntVar())
    rot = RotationFrame(root, tk.IntVar())
    sha = SharpnessFrame(root, tk.IntVar())
    shu = ShutterSpeedFrame(root, tk.IntVar())

    bri.pack()
    con.pack()
    rot.pack()
    sha.pack()
    shu.pack()

    root.mainloop()

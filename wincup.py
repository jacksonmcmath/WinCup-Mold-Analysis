"""
WinCup Mold Analysis System

Uses a Raspberry Pi and Raspberry Pi Camera combined with OpenCV to analyze
molds. The Raspberry Pi uses a switch (connected to a GPIO pin) from the
machine to determine when to capture the image. LEDs are also connected to GPIO
pins to monitor activity while not looking at the screen.
"""
from ast import literal_eval
from datetime import datetime
import time
import json
import os
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox

import cv2
import gpiozero as gpio
import numpy
from picamera import PiCamera
from picamera.array import PiRGBArray
from PIL import Image, ImageTk

import frames


class RectTracker(object):
    """Draws a rectangle over the image to selct the zoom."""

    def __init__(self, canvas):
        self.canvas = canvas
        self.item = None

    def draw(self, start, end, **opts):
        """Draw the rectangle"""
        return self.canvas.create_rectangle(*(list(start) + list(end)), outline='red', **opts)

    def autodraw(self, **opts):
        """Setup automatic drawing; supports command option"""
        self.start = None
        self.canvas.bind("<Button-1>", self.__update, '+')
        self.canvas.bind("<B1-Motion>", self.__update, '+')
        self.canvas.bind("<ButtonRelease-1>", self.__stop, '+')

        self._command = opts.pop('command', lambda *args: None)
        self.rectopts = opts

    def __update(self, event):
        if not self.start:
            self.start = [event.x, event.y]
            return

        if self.item is not None:
            self.canvas.delete(self.item)
        self.item = self.draw(
            self.start, (event.x, event.y), **self.rectopts)
        self._command(self.start, (event.x, event.y))

    def __stop(self, event):
        self.start = None


class SplashFrame(ttk.Frame):
    """Creates the main splash page."""
    def __init__(self, master, *args, **kwargs):
        ttk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        wc_logo = tk.PhotoImage(file='wclogo.gif')
        ex_set = 'Change the settings for\nthe camera.'
        ex_cal = 'Calibrate the image used\nfor mold analysis.'
        ex_dif = 'Begin the mold analysis.\nMust calibrate first.'

        self.label_logo = ttk.Label(self, image=wc_logo)
        self.label_logo.img = wc_logo
        self.label_title = ttk.Label(self, text='Mold Analysis System', font='-weight bold -size 20')
        self.button_settings = ttk.Button(self, text='Settings', command=self.splash2settings)
        self.button_calibration = ttk.Button(self, text='Calibration', command=self.splash2calibration)
        self.button_difference = ttk.Button(self, text='Begin Analysis', command=self.splash2difference)
        self.button_quit = ttk.Button(self, text='Quit', command=self.onQuit)
        self.label_explain_set = ttk.Label(self, text=ex_set, justify='center')
        self.label_explain_cal = ttk.Label(self, text=ex_cal, justify='center')
        self.label_explain_dif = ttk.Label(self, text=ex_dif, justify='center')
        self.separator1 = ttk.Separator(self, orient='vertical')
        self.separator2 = ttk.Separator(self, orient='vertical')

        self.label_logo.grid(row=1, column=1, columnspan=5)
        self.label_title.grid(row=2, column=1, columnspan=5, padx=15, pady=20)
        self.separator1.grid(row=3, column=2, rowspan=2, sticky='ns', padx=5)
        self.separator2.grid(row=3, column=4, rowspan=2, sticky='ns', padx=5)
        self.label_explain_set.grid(row=3, column=1, padx=15, pady=10)
        self.label_explain_cal.grid(row=3, column=3, padx=15, pady=10)
        self.label_explain_dif.grid(row=3, column=5, padx=15, pady=10)
        self.button_settings.grid(row=4, column=1, padx=15, pady=10)
        self.button_calibration.grid(row=4, column=3, padx=15, pady=10)
        self.button_difference.grid(row=4, column=5, padx=15, pady=10)
        self.button_quit.grid(row=5, column=1, columnspan=5, pady=25)

        self.rowconfigure(0, weight=1)
        self.rowconfigure(6, weight=1)
        self.columnconfigure(0, weight=1)
        self.columnconfigure(6, weight=1)
        self.columnconfigure(1, minsize=200)
        self.columnconfigure(3, minsize=200)
        self.columnconfigure(5, minsize=200)

    def splash2settings(self):
        self.master.splash2settings()

    def splash2calibration(self):
        self.master.splash2calibration()

    def splash2difference(self):
        self.master.splash2difference()

    def onQuit(self):
        if messagebox.askokcancel('Quit', 'Are you sure you want to quit?'):
            self.master.onQuit()
        else:
            pass


class SettingsFrame(ttk.Frame):
    """Creates the page to control/edit the camera settings."""
    def __init__(self, master, *args, **kwargs):
        ttk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        self.frame_main = ttk.Frame(self, pad=5)
        self.frame_settings = ttk.Frame(self, pad=5)
        self.frame_zoom = ttk.Frame(self, pad=5)
        self.frame_zoom_confirm = ttk.Frame(self, pad=5)
        self.frame_manual = ttk.Frame(self, pad=5)

        self.zoom_finished = False
        self.using_auto = None

        self.init_vars()
        self.init_main()

    def init_vars(self):
        with open('camerasettings.json') as file:
            settings = json.load(file)
            self.json_settings = settings
        settings['default']['zoom'] = tuple(settings['default']['zoom'])
        settings['custom']['zoom'] = tuple(settings['custom']['zoom'])

        self.def_bri = tk.IntVar(value=settings['default']['brightness'])
        self.def_con = tk.IntVar(value=settings['default']['contrast'])
        self.def_rot = tk.IntVar(value=settings['default']['rotation'])
        self.def_sha = tk.IntVar(value=settings['default']['sharpness'])
        self.def_shu = tk.IntVar(value=settings['default']['shutter_speed'])
        self.def_zoo = tk.StringVar(value=str(settings['default']['zoom']))

        self.cus_bri = tk.IntVar(value=settings['custom']['brightness'])
        self.cus_con = tk.IntVar(value=settings['custom']['contrast'])
        self.cus_rot = tk.IntVar(value=settings['custom']['rotation'])
        self.cus_sha = tk.IntVar(value=settings['custom']['sharpness'])
        self.cus_shu = tk.IntVar(value=settings['custom']['shutter_speed'])
        self.cus_zoo = tk.StringVar(value=str(settings['custom']['zoom']))

    def save_vars(self):
        vars = {
            'brightness': self.cus_bri.get(),
            'contrast': self.cus_con.get(),
            'rotation': self.cus_rot.get(),
            'sharpness': self.cus_sha.get(),
            'shutter_speed': self.cus_shu.get(),
            'zoom': literal_eval(self.cus_zoo.get())
        }
        self.json_settings['custom'] = vars
        with open('camerasettings.json', 'w') as file:
            json.dump(self.json_settings, file, indent=4, sort_keys=True)

    def init_main(self):
        description = 'Configure the camera settings.\nGood camera settings make the analysis more accurate.'
        self.frame_main.pack(side="top", fill="both", expand=True)

        self.label_description = ttk.Label(self.frame_main, text=description)
        self.button_auto = ttk.Button(self.frame_main, text='Auto Setup', command=self.main2settings)
        self.button_man = ttk.Button(self.frame_main, text='Manual Setup', command=self.main2manual)
        self.label_title = ttk.Label(self.frame_main, text='Edit Camera Settings', font='-weight bold -size 20')
        self.separator_main = ttk.Separator(self.frame_main, orient='vertical')
        self.button_settings2splash = ttk.Button(self.frame_main, text='Home', command=self.settings2splash)
        self.label_explain_man = ttk.Label(self.frame_main, text='Use custom\ncamera settings.', justify='center')
        self.label_explain_auto = ttk.Label(self.frame_main, text='Use default\ncamera settings.', justify='center')

        self.label_title.grid(row=2, column=1, columnspan=3, padx=15, pady=20)
        self.button_auto.grid(row=4, column=3, padx=15, pady=10)
        self.label_explain_auto.grid(row=3, column=3)
        self.button_man.grid(row=4, column=1, padx=15, pady=10)
        self.label_explain_man.grid(row=3, column=1)
        self.separator_main.grid(row=3, column=2, rowspan=2, sticky='ns')
        self.button_settings2splash.grid(row=5, column=2, pady=35)

        self.frame_main.rowconfigure(0, weight=1)
        self.frame_main.rowconfigure(6, weight=1)
        self.frame_main.columnconfigure(0, weight=1)
        self.frame_main.columnconfigure(4, weight=1)

    def init_settings(self):
        if self.using_auto:
            self.label_auto = ttk.Label(self.frame_settings, text='Camera Settings - Auto Setup', font='-weight bold', pad=15)
            self.label_auto.grid(row=1, column=1, columnspan=2)
        else:
            self.label_manual = ttk.Label(self.frame_settings, text='Camera Settings - Manual Setup', font='-weight bold', pad=15)
            self.label_manual.grid(row=1, column=1, columnspan=2)
        self.separator_settings = ttk.Separator(self.frame_settings, orient='horizontal')

        self.label_bri = ttk.Label(self.frame_settings, pad=5, text='Brightness:')
        self.label_con = ttk.Label(self.frame_settings, pad=5, text='Contrast:')
        self.label_rot = ttk.Label(self.frame_settings, pad=5, text='Rotation:')
        self.label_sha = ttk.Label(self.frame_settings, pad=5, text='Sharpness:')
        self.label_shu = ttk.Label(self.frame_settings, pad=5, text='Shutter Speed:')
        self.label_zoo = ttk.Label(self.frame_settings, pad=5, text='Zoom:')

        self.label_bri_val = ttk.Label(self.frame_settings, textvariable=self.cus_bri)
        self.label_con_val = ttk.Label(self.frame_settings, textvariable=self.cus_con)
        self.label_rot_val = ttk.Label(self.frame_settings, textvariable=self.cus_rot)
        self.label_sha_val = ttk.Label(self.frame_settings, textvariable=self.cus_sha)
        self.label_shu_val = ttk.Label(self.frame_settings, textvariable=self.cus_shu)
        self.label_zoo_val = ttk.Label(self.frame_settings, textvariable=self.cus_zoo)

        if self.zoom_finished:
            self.button_finish = ttk.Button(self.frame_settings, text='Finish', command=self.settings2splash)
            self.button_finish.grid(row=10, column=2, sticky='e')
            self.button_settings2zoom = ttk.Button(self.frame_settings, text='Back', command=self.settings2zoom)
            self.button_settings2zoom.grid(row=10, column=1, sticky='w')

        else:
            self.button_settings2main = ttk.Button(self.frame_settings, text='Back', command=self.settings2main)
            self.button_settings2main.grid(row=10, column=1, sticky='w')
            if self.using_auto:
                self.button_settings2zoom = ttk.Button(self.frame_settings, text='Next', command=self.settings2zoom)
                self.button_settings2zoom.grid(row=10, column=2, sticky='e')
            else:
                self.button_settings2manual = ttk.Button(self.frame_settings, text='Next', command=self.settings2manual)
                self.button_settings2manual.grid(row=10, column=2, sticky='e')

        self.separator_settings.grid(row=2, column=1, columnspan=2, sticky='ew')

        self.label_bri.grid(row=3, column=1, sticky='e')
        self.label_con.grid(row=4, column=1, sticky='e')
        self.label_rot.grid(row=5, column=1, sticky='e')
        self.label_sha.grid(row=6, column=1, sticky='e')
        self.label_shu.grid(row=7, column=1, sticky='e')
        self.label_zoo.grid(row=8, column=1, sticky='e')

        self.label_bri_val.grid(row=3, column=2, sticky='w')
        self.label_con_val.grid(row=4, column=2, sticky='w')
        self.label_rot_val.grid(row=5, column=2, sticky='w')
        self.label_sha_val.grid(row=6, column=2, sticky='w')
        self.label_shu_val.grid(row=7, column=2, sticky='w')
        self.label_zoo_val.grid(row=8, column=2, sticky='w')

        self.frame_settings.rowconfigure(0, weight=5)
        self.frame_settings.rowconfigure(9, weight=1)
        self.frame_settings.rowconfigure(11, weight=5)
        self.frame_settings.columnconfigure(0, weight=5)
        self.frame_settings.columnconfigure(3, weight=5)

    def init_zoom(self):

        def savecoords_d(event):
            global dx, dy

            def event2canvas(e, c): return (c.canvasx(e.x), c.canvasy(e.y))
            dx, dy = event2canvas(event, self.canvas_zoom)

        def savecoords_u(event):
            global ux, uy

            def event2canvas(e, c): return (c.canvasx(e.x), c.canvasy(e.y))
            ux, uy = event2canvas(event, self.canvas_zoom)

        self.capture_image_zoom()
        img = tk.PhotoImage(file='zoom_bg.gif')
        self.zoom_w = img.width()
        self.zoom_h = img.height()

        global dx, dy, ux, uy
        dx = 0
        dy = 0
        ux = self.zoom_w   # in case there is no click on zoom screen
        uy = self.zoom_h

        if self.using_auto:
            self.button_zoom2settings_n = ttk.Button(self.frame_zoom, text='Next', command=self.zoom2settings_n)
            self.button_zoom2settings_b = ttk.Button(self.frame_zoom, text='Back', command=self.zoom2settings_b)
            self.button_zoom2settings_b.grid(row=3, column=1, pady=10)
            self.button_zoom2settings_n.grid(row=3, column=2, pady=10)
        else:
            self.button_zoom2settings = ttk.Button(self.frame_zoom, text='Next', command=self.zoom2settings_n)
            self.button_zoom2manual = ttk.Button(self.frame_zoom, text='Back', command=self.zoom2manual)
            self.button_zoom2settings.grid(row=3, column=2, pady=10)
            self.button_zoom2manual.grid(row=3, column=1, pady=10)

        self.label_zoom = ttk.Label(self.frame_zoom, text='Select the region of interest:', font='-weight bold -size 20')
        self.canvas_zoom = tk.Canvas(self.frame_zoom, width=img.width(), height=img.height())
        self.canvas_zoom.create_image(img.width() / 2, img.height() / 2, image=img)
        self.canvas_zoom.img = img
        self.canvas_zoom.bind('<ButtonPress-1>', savecoords_d)
        self.canvas_zoom.bind('<ButtonRelease-1>', savecoords_u)
        rect = RectTracker(self.canvas_zoom)
        rect.autodraw(width=1, stipple='gray12')

        self.label_zoom.grid(row=1, column=1, columnspan=2, pady=20)
        self.canvas_zoom.grid(row=2, column=1, columnspan=2)

        self.frame_zoom.rowconfigure(0, weight=1)
        self.frame_zoom.rowconfigure(4, weight=1)
        self.frame_zoom.columnconfigure(0, weight=1)
        self.frame_zoom.columnconfigure(3, weight=1)

    def init_zoom_confirm(self):
        self.zoom_test()
        time.sleep(0.1)
        img = tk.PhotoImage(file='zoom_test.gif')
        self.label_zoom_conf = ttk.Label(self.frame_zoom_confirm, text='Is this correct?', font='-weight bold -size 20')
        self.label_zoom_conf_img = ttk.Label(self.frame_zoom_confirm, image=img)
        self.label_zoom_conf_img.img = img
        self.button_zoom_y = ttk.Button(self.frame_zoom_confirm, text='Yes', command=self.conf2settings)
        self.button_zoom_n = ttk.Button(self.frame_zoom_confirm, text='No', command=self.conf2zoom)

        self.label_zoom_conf.grid(row=1, column=1, columnspan=2)
        self.label_zoom_conf_img.grid(row=2, column=1, columnspan=2)
        self.button_zoom_n.grid(row=3, column=1)
        self.button_zoom_y.grid(row=3, column=2)

        self.frame_zoom_confirm.rowconfigure(0, weight=1)
        self.frame_zoom_confirm.rowconfigure(4, weight=1)
        self.frame_zoom_confirm.columnconfigure(0, weight=1)
        self.frame_zoom_confirm.columnconfigure(3, weight=1)

    def init_manual(self):
        self.label_manual = ttk.Label(self.frame_manual, text='Camera Settings - Manual Setup', font='-weight bold', pad=15)
        self.separator_manual_1 = ttk.Separator(self.frame_manual, orient='horizontal')
        self.separator_manual_2 = ttk.Separator(self.frame_manual, orient='vertical')
        self.separator_manual_3 = ttk.Separator(self.frame_manual, orient='horizontal')
        self.separator_manual_4 = ttk.Separator(self.frame_manual, orient='vertical')
        self.frame_man_bri = frames.BrightnessFrame(self.frame_manual, self.cus_bri, pad=15)
        self.frame_man_con = frames.ContrastFrame(self.frame_manual, self.cus_con, pad=15)
        self.frame_man_rot = frames.RotationFrame(self.frame_manual, self.cus_rot, pad=15)
        self.frame_man_sha = frames.SharpnessFrame(self.frame_manual, self.cus_sha, pad=15)
        self.frame_man_shu = frames.ShutterSpeedFrame(self.frame_manual, self.cus_shu, pad=15)
        self.button_reset_settings = ttk.Button(self.frame_manual, text='Reset to default', command=self.reset_to_default)
        self.button_manual2zoom = ttk.Button(self.frame_manual, text='Next', command=self.manual2zoom)
        self.button_manual2main = ttk.Button(self.frame_manual, text='Back', command=self.manual2main)

        self.label_manual.grid(row=1, column=1, columnspan=5)
        self.separator_manual_1.grid(row=2, column=1, columnspan=5, sticky='ew')
        self.frame_man_rot.grid(row=3, column=1, rowspan=3)
        self.separator_manual_2.grid(row=3, column=2, rowspan=3, sticky='ns')
        self.frame_man_bri.grid(row=3, column=3)
        self.frame_man_con.grid(row=5, column=3)
        self.separator_manual_3.grid(row=4, column=3, columnspan=3, sticky='ew')
        self.separator_manual_4.grid(row=3, column=4, rowspan=3, sticky='ns')
        self.frame_man_sha.grid(row=3, column=5, sticky='w')
        self.frame_man_shu.grid(row=5, column=5)
        self.button_reset_settings.grid(row=6, column=2, columnspan=3, padx=30, pady=15)
        self.button_manual2zoom.grid(row=6, column=3, columnspan=3, sticky='e', padx=30, pady=15)
        self.button_manual2main.grid(row=6, column=1, columnspan=3, sticky='w', padx=30, pady=15)

        self.frame_manual.rowconfigure(0, weight=1)
        self.frame_manual.rowconfigure(8, weight=1)
        self.frame_manual.columnconfigure(0, weight=1)
        self.frame_manual.columnconfigure(6, weight=1)

    def main2settings(self):
        self.using_auto = True
        self.reset_to_default()
        self.init_settings()
        self.frame_main.pack_forget()
        self.frame_settings.pack(side="top", fill="both", expand=True)

    def settings2main(self):
        self.using_auto = None
        self.frame_settings.pack_forget()
        self.frame_main.pack(side="top", fill="both", expand=True)

    def settings2zoom(self):
        self.init_zoom()
        self.frame_settings.pack_forget()
        self.frame_zoom.pack(side="top", fill="both", expand=True)

    def settings2splash(self):
        self.zoom_finished = False
        self.save_vars()
        self.settings2main()
        self.master.settings2splash()

    def settings2manual(self):
        self.init_manual()
        self.frame_settings.pack_forget()
        self.frame_manual.pack(side="top", fill="both", expand=True)

    def zoom2settings_n(self):
        self.frame_zoom.pack_forget()
        self.save_vars()
        self.cus_zoo.set(str(self.getzoomcoords()))
        self.zoom_test()
        self.init_zoom_confirm()
        self.frame_zoom_confirm.pack(side="top", fill="both", expand=True)

    def zoom2settings_b(self):
        self.init_settings()
        self.zoom_finished = False
        self.frame_zoom.pack_forget()
        self.frame_settings.pack(side="top", fill="both", expand=True)

    def zoom2manual(self):
        self.init_manual()
        self.zoom_finished = False
        self.frame_zoom.pack_forget()
        self.frame_manual.pack(side="top", fill="both", expand=True)

    def conf2settings(self):
        self.frame_zoom_confirm.pack_forget()
        self.cus_zoo.set(str(self.getzoomcoords()))
        self.zoom_finished = True
        self.init_settings()
        self.frame_settings.pack(side="top", fill="both", expand=True)

    def conf2zoom(self):
        self.init_zoom()
        self.frame_zoom_confirm.pack_forget()
        self.frame_zoom.pack(side="top", fill="both", expand=True)

    def main2manual(self):
        self.using_auto = False
        self.init_manual()
        self.frame_main.pack_forget()
        self.frame_manual.pack(side="top", fill="both", expand=True)

    def manual2zoom(self):
        self.init_zoom()
        self.frame_manual.pack_forget()
        self.frame_zoom.pack(side="top", fill="both", expand=True)

    def manual2main(self):
        self.using_auto = None
        self.frame_manual.pack_forget()
        self.frame_main.pack(side="top", fill="both", expand=True)

    def reset_to_default(self):
        self.cus_bri.set(self.def_bri.get())
        self.cus_con.set(self.def_con.get())
        self.cus_rot.set(self.def_rot.get())
        self.cus_sha.set(self.def_sha.get())
        self.cus_shu.set(self.def_shu.get())
        self.cus_zoo.set(self.def_zoo.get())

    def getzoomcoords(self):
        global dx, dy, ux, uy
        dx = 0 if dx < 0 else dx
        dy = 0 if dy < 0 else dy
        ux = 0 if ux < 0 else ux
        uy = 0 if uy < 0 else uy

        dx = self.zoom_w if dx > self.zoom_w else dx
        dy = self.zoom_h if dy > self.zoom_h else dy
        ux = self.zoom_w if ux > self.zoom_w else ux
        uy = self.zoom_h if uy > self.zoom_h else uy

        xmin = round(min(dx, ux) / self.zoom_w, 3)
        xmax = round(max(dx, ux) / self.zoom_w, 3)
        ymin = round(min(dy, uy) / self.zoom_h, 3)
        ymax = round(max(dy, uy) / self.zoom_h, 3)
        return (xmin, ymin, xmax, ymax)

    def capture_image_zoom(self):
        self.save_vars()
        with PiCamera() as camera:
            camera = init_camera(camera)
            camera.zoom = (0.0, 0.0, 1.0, 1.0)
            camera.capture('zoom_bg.gif', resize=(400, 250))

    def zoom_test(self):
        self.save_vars()
        with PiCamera() as camera:
            camera = init_camera(camera)
            camera.capture('zoom_test.gif', resize=(400, 250))


class CalibrationFrame(ttk.Frame):
    """Creates the page to make the background image."""
    def __init__(self, master, *args, **kwargs):
        ttk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        self.num_total = tk.IntVar(value=10)
        self.num_current = tk.IntVar()
        self.frame_main = ttk.Frame(self, pad=5)
        self.frame_inprogress = ttk.Frame(self, pad=5)

        self.init_main()

    def init_main(self):
        description = 'Calibrates the base image used to analyze the molds.\nMolds must be empty and clean to ensure accuracy'
        self.frame_main.pack(side="top", fill="both", expand=True)
        self.label_title = ttk.Label(self.frame_main, text='Mold Calibration', font='-weight bold -size 20')
        self.separator_main = ttk.Separator(self.frame_main, orient='horizontal')
        self.label_num = ttk.Label(self.frame_main, text='Number of images:', font='-weight bold')
        self.rb_1 = ttk.Radiobutton(self.frame_main, text='10', value=10, variable=self.num_total)
        self.rb_2 = ttk.Radiobutton(self.frame_main, text='15', value=15, variable=self.num_total)
        self.rb_3 = ttk.Radiobutton(self.frame_main, text='20', value=20, variable=self.num_total)
        self.button_start = ttk.Button(self.frame_main, text='Calibrate', command=self.calibrate_start)
        self.button_home = ttk.Button(self.frame_main, text='Home', command=self.calibration2splash)

        self.label_title.grid(row=1, column=1, columnspan=2, padx=15, pady=10)
        self.separator_main.grid(row=2, column=1, columnspan=2, sticky='ew')
        self.label_num.grid(row=3, column=1, columnspan=2, padx=15, pady=10)
        self.rb_1.grid(row=4, column=1, columnspan=2)
        self.rb_2.grid(row=5, column=1, columnspan=2)
        self.rb_3.grid(row=6, column=1, columnspan=2)
        self.button_start.grid(row=7, column=2, sticky='e', pady=15)
        self.button_home.grid(row=7, column=1, sticky='w', pady=15)

        self.frame_main.rowconfigure(0, weight=1)
        self.frame_main.rowconfigure(8, weight=1)
        self.frame_main.columnconfigure(0, weight=1)
        self.frame_main.columnconfigure(3, weight=1)

    def init_inprogress(self):
        self.label_prog_text = ttk.Label(self.frame_inprogress, text='Calibration in Progress', font='-weight bold -size 20')
        self.label_prog_img = ttk.Label(self.frame_inprogress)
        self.pb_calibration = ttk.Progressbar(self.frame_inprogress, orient='horizontal', mode='determinate', maximum=self.num_total.get(), variable=self.num_current)
        self.button_back = ttk.Button(self.frame_inprogress, text='Back', command=self.inprogress2main)
        self.button_finish = ttk.Button(self.frame_inprogress, text='Finish', command=self.calibration2splash)

        self.label_prog_text.grid(row=1, column=1, columnspan=2)
        self.label_prog_img.grid(row=2, column=1, columnspan=2)
        self.pb_calibration.grid(row=3, column=1, columnspan=2, sticky='ew', pady=15)

        self.frame_inprogress.rowconfigure(0, weight=1)
        self.frame_inprogress.rowconfigure(5, weight=1)
        self.frame_inprogress.columnconfigure(0, weight=1)
        self.frame_inprogress.columnconfigure(3, weight=1)

    def calibrate_start(self):
        self.main2inprogress()
        # capture
        with PiCamera() as camera:
            camera = init_camera(camera)
            fns = []
            for i in range(1, self.num_total.get() + 1):
                fns.append('img{:0>2}.jpg'.format(i))
                camera.capture('img{:0>2}.jpg'.format(i), resize=(400, 250))
                image = ImageTk.PhotoImage(Image.open('img{:0>2}.jpg'.format(i)))
                self.label_prog_img.configure(image=image)
                self.label_prog_img.img = image
                self.num_current.set(i)
                self.master.root.update()
            # average
            self.pb_calibration.configure(mode='indeterminate')
            self.pb_calibration.start()
            images = []
            for fn in fns:
                img = Image.open(fn)
                images.append(img)
            w, h = images[0].size
            N = len(images)
            avgImgArr = numpy.zeros((h, w, 3), numpy.float)
            for img in images:
                imgArr = numpy.array(img, dtype=numpy.float)
                avgImgArr = avgImgArr + imgArr / N
            avgImgArr = numpy.array(numpy.round(avgImgArr), dtype=numpy.uint8)
            avgImg = Image.fromarray(numpy.uint8(avgImgArr))
            avgImg.save('average.jpg')
            image = ImageTk.PhotoImage(Image.open('average.jpg'))
            self.label_prog_img.configure(image=image)
            self.label_prog_img.img = image
            self.master.root.update()
            # delete
            for i in range(1, self.num_total.get() + 1):
                os.remove('img{:0>2}.jpg'.format(i))
            self.pb_calibration.stop()
            self.pb_calibration.grid_forget()
            # add exit button
            self.button_back.grid(row=4, column=1, pady=10)
            self.button_finish.grid(row=4, column=2, pady=10)
            self.label_prog_text.configure(text='Calibration Complete')

    def main2inprogress(self):
        self.init_inprogress()
        self.frame_main.pack_forget()
        self.frame_inprogress.pack(side="top", fill="both", expand=True)

    def inprogress2main(self):
        self.init_main()
        self.frame_inprogress.pack_forget()
        self.frame_main.pack(side="top", fill="both", expand=True)

    def calibration2splash(self):
        self.inprogress2main()
        self.master.calibration2splash()


class DifferenceFrame(ttk.Frame):
    """Creates the page to run the differencing algorithm."""
    def __init__(self, master, *args, **kwargs):
        ttk.Frame.__init__(self, master, *args, **kwargs)
        self.master = master
        self.frame_main = ttk.Frame(self, pad=5)
        self.frame_inprogress = ttk.Frame(self, pad=5)
        self.sens = tk.IntVar(value=25)

        self.init_main()

    def init_main(self):
        description = 'Analyzes molds using image differencing to\ndetect changes; checks molds after each cycle.\nEnsure that camera is calibrated and settings are\nadjusted for best results.'
        self.frame_main.pack(side="top", fill="both", expand=True)
        self.label_title = ttk.Label(self.frame_main, text='Mold Analysis', font='-weight bold -size 20')
        self.label_description = ttk.Label(self.frame_main, text=description)
        self.button_home = ttk.Button(self.frame_main, text='Home', command=self.difference2splash)
        self.button_start = ttk.Button(self.frame_main, text='Begin', command=self.main2inprogress)
        self.label_sens = ttk.Label(self.frame_main, pad=5, text='Sensitivity:', font='-weight bold')
        self.label_sens_val = ttk.Label(self.frame_main, textvariable=self.sens, font='-weight bold')
        self.scale_sens = tk.Scale(self.frame_main, variable=self.sens, orient='horizontal', from_=0, to=50, command=self.check_sens, showvalue=0)

        self.label_title.grid(row=1, column=1, columnspan=2)
        self.label_description.grid(row=2, column=1, columnspan=2)
        self.label_sens.grid(row=3, column=1, sticky='e', padx=3, pady=5)
        self.label_sens_val.grid(row=3, column=2, sticky='w', padx=3, pady=5)
        self.scale_sens.grid(row=4, column=1, columnspan=2, pady=5)
        self.button_home.grid(row=5, column=1, padx=15, pady=20)
        self.button_start.grid(row=5, column=2, padx=15, pady=20)

        self.frame_main.rowconfigure(0, weight=1)
        self.frame_main.rowconfigure(6, weight=1)
        self.frame_main.columnconfigure(0, weight=1)
        self.frame_main.columnconfigure(3, weight=1)

    def init_inprogress(self):
        self.switch = gpio.Button(26)
        self.switch.when_pressed = self.run_dif
        self.led_r = gpio.LED(5)
        self.led_g = gpio.LED(6)
        self.led_flash = gpio.LED(19)

        self.label_prog = ttk.Label(self.frame_inprogress, text='Analyzing', font='-weight bold -size 20')
        self.label_img = ttk.Label(self.frame_inprogress)
        self.button_back = ttk.Button(self.frame_inprogress, text='Back', command=self.inprogress2main)
        self.pb_dif = ttk.Progressbar(self.frame_inprogress, orient='horizontal', mode='indeterminate', length=400)

        self.label_prog.grid(row=1, column=1)
        self.label_img.grid(row=2, column=1)
        self.pb_dif.grid(row=3, column=1)
        self.button_back.grid(row=4, column=1)

        self.frame_inprogress.rowconfigure(0, weight=1)
        self.frame_inprogress.rowconfigure(5, weight=1)
        self.frame_inprogress.columnconfigure(0, weight=1)
        self.frame_inprogress.columnconfigure(2, weight=1)

    def run_dif(self):
        self.pb_dif.start()
        base_gray = cv2.imread('average.jpg', 0)
        with PiCamera() as camera:
            camera = init_camera(camera)
            with PiRGBArray(camera, size=(400, 250)) as rawCapture:
                self.led_flash.on()
                camera.capture(rawCapture, format='bgr', resize=(400, 250))
                filename = datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.jpg'
                self.led_flash.off()
                image = rawCapture.array
                rawCapture.truncate(0)
                image_gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

                diff = cv2.absdiff(base_gray, image_gray)
                thresh = cv2.threshold(diff, self.sens.get(), 255, cv2.THRESH_BINARY)[1]
                conts = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)[1]

                obj = 0
                for c in conts:
                    (x, y, w, h) = cv2.boundingRect(c)
                    if w > 35 and h > 35:
                        cv2.rectangle(image, (x, y), (x + w, y + h), (255, 0, 0), 2)
                        obj += 1

                if obj:
                    self.led_r.on()
                    self.led_g.off()
                else:
                    self.led_r.off()
                    self.led_g.on()

                img = ImageTk.PhotoImage(image=Image.fromarray(image))
                self.label_img.configure(image=img)
                self.label_img.img = img

                self.pb_dif.stop()
                self.master.root.update()

    def update_label(self):
        if self.text == '':
            self.text = '.'
            self.label_prog.configure(text='Analyzing .')
        elif self.text == '.':
            self.text = '..'
            self.label_prog.configure(text='Analyzing ..')
        elif self.text == '..':
            self.text = '...'
            self.label_prog.configure(text='Analyzing ...')
        elif self.text == '...':
            self.text = '....'
            self.label_prog.configure(text='Analyzing ....')
        elif self.text == '....':
            self.text = '.....'
            self.label_prog.configure(text='Analyzing .....')
        elif self.text == '.....':
            self.text = ''
            self.label_prog.configure(text='Analyzing')
        self.master.root.update()

    def difference2splash(self):
        self.master.difference2splash()

    def main2inprogress(self):
        self.init_inprogress()
        self.frame_main.pack_forget()
        self.frame_inprogress.pack(side="top", fill="both", expand=True)

    def inprogress2main(self):
        self.init_main()
        self.frame_inprogress.pack_forget()
        self.frame_main.pack(side="top", fill="both", expand=True)
        self.led_r.close()
        self.led_g.close()
        self.led_flash.close()
        self.switch.close()

    def check_sens(self, e=None):
        value = self.sens.get()
        if value != int(value):
            self.scale_sens.set(round(value))


class MainFrame(ttk.Frame):
    """Creates a frame to hold all the other frames."""
    def __init__(self, root, *args, **kwargs):
        ttk.Frame.__init__(self, root, *args, **kwargs)

        self.root = root
        self.frame_splash = SplashFrame(self, pad=5)
        self.frame_settings = SettingsFrame(self, pad=5)
        self.frame_calibration = CalibrationFrame(self, pad=5)
        self.frame_difference = DifferenceFrame(self, pad=5)

        self.frame_splash.pack(side="top", fill="both", expand=True)

    def splash2settings(self):
        self.frame_splash.pack_forget()
        self.frame_settings.pack(side="top", fill="both", expand=True)

    def splash2calibration(self):
        self.frame_splash.pack_forget()
        self.frame_calibration.pack(side="top", fill="both", expand=True)

    def splash2difference(self):
        self.frame_splash.pack_forget()
        self.frame_difference.pack(side="top", fill="both", expand=True)

    def settings2splash(self):
        self.frame_settings.pack_forget()
        self.frame_splash.pack(side="top", fill="both", expand=True)

    def calibration2splash(self):
        self.frame_calibration.pack_forget()
        self.frame_splash.pack(side="top", fill="both", expand=True)

    def difference2splash(self):
        self.frame_difference.pack_forget()
        self.frame_splash.pack(side="top", fill="both", expand=True)

    def onQuit(self):
        self.root.destroy()


def init_camera(camera):
    """Takes in a PiCamera object and applies settings to it."""
    with open('camerasettings.json') as file:
        settings = json.load(file)
    settings['custom']['zoom'] = tuple(settings['custom']['zoom'])
    for k, v in settings['custom'].items():
        setattr(camera, k, v)
    camera.resolution = (640, 368)
    camera.awb_mode = 'auto'
    return camera


def main():
    root = tk.Tk()
    MainFrame(root).pack(side="top", fill="both", expand=True)
    root.attributes('-zoomed', True)
    root.mainloop()


if __name__ == '__main__':
    main()

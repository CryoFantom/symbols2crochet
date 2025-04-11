from fontTools import ttLib
import os
from os import walk

import json

import tkinter as tk
from tkinter import filedialog, ttk
from PIL import Image, ImageTk, ImageFont, ImageDraw

from doc_treatment import iter_from_file, pattern_from_img, register

isDrawn = False

class SettingsModule():
    @staticmethod
    def character_limit(entry_text):
        if len(entry_text.get()) > 0:
            entry_text.set(entry_text.get()[-1])
                
    def __init__(self, root):
        self.frame = tk.Frame(root)
        
        self.txt = tk.Label(self.frame, text="Type a character for example :")
        self.txt.grid(column=1, row=0)
        
        self.character = tk.StringVar(value="漢")
        self.character.trace_add("write", lambda *args: self.character_limit(self.character))
        
        self.charEntry = tk.Entry(self.frame, width=3, textvariable=self.character)
        self.charEntry.grid(column=2, row=0)
        
        self.size = tk.IntVar(value = 30)
        
        self.sizeEntry = tk.Entry(self.frame, width=5, textvariable=self.size, justify="right")
        self.sizeEntry.grid(column=3, row=0)
        
        self.scText = tk.Label(self.frame, text="sc")
        self.scText.grid(column=4, row=0)
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)

def draw_character(character, size, font):
    img = Image.new('L', (size, size), color=0)
    font = ImageFont.truetype(font, size=size)
    draw = ImageDraw.Draw(img)
    draw.text((size//2, size//2), character, fill=(255), font=font, anchor="mm")

    img = img.point(lambda p: 255 if p>100 else 0)
    return img

class PreviewModule():
    @staticmethod
    def blackImage():
        return ImageTk.PhotoImage(Image.new('L', (120, 120), color=0))

    def __init__(self, root, character, size, font, fonts={}):
        self.frame = tk.Frame(root)
        
        self.fonts = fonts
        
        self.default = tk.Label(self.frame)
        tmp = self.blackImage()
        self.default.image = tmp
        self.default.configure(image= tmp)
        self.default.grid(column=0, row=0)
        
        self.pixelized = tk.Label(self.frame)
        tmp = self.blackImage()
        self.pixelized.image = tmp
        self.pixelized.configure(image= tmp)
        self.pixelized.grid(column=1, row=0)

        self.character = character
        self.size = size
        self.font = font
        
        self.character.trace_add("write", lambda *args: self.render())
        self.size.trace_add("write", lambda *args: self.render())
        self.font.trace_add("write", lambda *args: self.render())
        
        self.render()
        
    def get_size(self):
        return self.size.get()
    
    def get_font(self):
        return self.fonts[self.font.get()]
    
    def grid(self, **kwargs):
        self.frame.grid(**kwargs)
    
    def render(self):
        default = Image.new('L', (120, 120), color=0)
        
        if self.font.get() in self.fonts:
            default = draw_character(self.character.get()[-1], 120, self.get_font())
            defaultPhoto = ImageTk.PhotoImage(default)
            self.default.image = defaultPhoto
            self.default.configure(image = defaultPhoto)
            
            
            pixelized = draw_character(self.character.get()[-1], self.get_size(), self.get_font())
            pixelized = pixelized.resize((120, 120), Image.NEAREST)
            pixelized = pixelized.point(lambda p: 255 if p>100 else 0)
            pixelizedPhoto = ImageTk.PhotoImage(pixelized)
            self.pixelized.image = pixelizedPhoto
            self.pixelized.configure(image = pixelizedPhoto)
        

class SearchableComboBox():
    def __init__(self, root, entry_root, options, fonts={}) -> None:
        self._hovering = False
        def sethover(val):
            self._hovering = val
        
        self.dropdown_id = None
        self.options = options

        # Create a Text widget for the entry field
        wrapper = tk.Frame(entry_root)
        wrapper.grid(column=2, row=0)
        
        self.entryVar = tk.StringVar(value = list(fonts.keys())[0])

        self.entry = tk.Entry(wrapper, width=20, textvariable=self.entryVar)
        self.entry.bind("<KeyRelease>", self.on_entry_key)
        root.bind("<Button-1>", self.unfocus)
        self.entry.bind("<Enter>", lambda *_: sethover(True))
        self.entry.bind("<Leave>", lambda *_: sethover(False))
        self.entry.bind("<FocusIn>", self.show_dropdown)
        self.entry.pack(side=tk.LEFT)

        # Dropdown icon/button
        self.icon = ImageTk.PhotoImage(Image.open("dropdown_arrow.png").resize((16,16)))
        tk.Button(wrapper, image=self.icon, command=self.show_dropdown).pack(side=tk.LEFT)

        # Create a Listbox widget for the dropdown menu
        self.listbox = tk.Listbox(root, height=5, width=30)
        self.listbox.bind("<<ListboxSelect>>", self.on_select)
        for option in self.options:
            self.listbox.insert(tk.END, option)
    
    def unfocus(self, event):
        if self._hovering:
            self.show_dropdown(event)
        else:
            self.hide_dropdown(event)
    
    def get(self):
        return self.entry.get()

    def on_entry_key(self, event):
        typed_value = event.widget.get().strip().lower()
        if not typed_value:
            # If the entry is empty, display all options
            self.listbox.delete(0, tk.END)
            for option in self.options:
                self.listbox.insert(tk.END, option)
        else:
            # Filter options based on the typed value
            self.listbox.delete(0, tk.END)
            filtered_options = [option for option in self.options if typed_value in option.lower()]
            for option in filtered_options:
                self.listbox.insert(tk.END, option)
        self.show_dropdown()

    def on_select(self, event):
        selected_index = self.listbox.curselection()
        if selected_index:
            selected_option = self.listbox.get(selected_index)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, selected_option)
            self.entryVar.set(selected_option)

    def show_dropdown(self, event=None):
        self.listbox.place(in_=self.entry, x=0, rely=1, relwidth=1, anchor="nw")
        self.listbox.lift()

    def hide_dropdown(self, event=None):
        self.listbox.place_forget()
        
    def trace_add(self, method, callback):
        self.entryVar.trace_add(method, callback)


path = os.path.join("C:\\", "Windows", "Fonts")

def getFont(font, font_path):
    x = lambda x: font['name'].getDebugName(x)
    if x(16) is None:
        return x(1), x(2), font_path
    if x(16) is not None:
        return x(16), x(17), font_path
    else:
        pass

fonts = {}
for (dirpath, dirnames, filenames) in walk(path):
    for file in filenames:
        if any(file.endswith(ext) for ext in ['.ttf', '.otf', '.ttc', '.ttz', '.woff', '.woff2']):
            font_path = os.path.join(dirpath, file)
            font = None
            if file.endswith("ttc"):
                try:
                    for k in range(100):
                        font = getFont(ttLib.TTFont(font_path, fontNumber=k), font_path)
                except:
                    pass
            else:
                font = getFont(ttLib.TTFont(font_path), font_path)
            if font[1]=="Regular":
                fonts[font[0]] = font[2]

root = tk.Tk()
root.title("Font to patron")

fontFrame = tk.Frame(root)
fontFrame.grid(column=1, row=0, padx=10, pady=10)

ttk.Label(fontFrame, text="Please select a font :").grid(column=1, row=0)
fontChosen = SearchableComboBox(root, fontFrame, list(fonts.keys()), fonts=fonts)

settings = SettingsModule(root)
settings.grid(column=1, row=1, padx=10, pady=10)

preview = PreviewModule(root, settings.character, settings.size, fontChosen, fonts=fonts)
preview.grid(column=1, row=2, padx=10, pady=10)

fileFrame = tk.Frame(root)
fileFrame.grid(column=1, row=4, padx=10, pady=10)

path = tk.StringVar()

fileSelector = tk.Entry(fileFrame, width=50, state="readonly", textvariable=path)
fileSelector.grid(column=1, row=0, padx=(0, 5))


def askFile():
    global path
    path.set(filedialog.askopenfilename(title='Select a file to treat', filetypes=(('Word doc', '*.docx'), ('Text files', '*.txt'))))
    buttonTreat["state"] = "normal"
    
def treatFile():
    global path
    dico = {}
    for kanji in iter_from_file(path.get()):
        img = draw_character(kanji, preview.get_size(), preview.get_font())
        pattern = pattern_from_img(img)
        dico[kanji] = pattern
    
    save(".".join(path.get().split("/")[-1].split(".")[:-1])+"_"+fontChosen.get(), preview.get_size(), dico)

def dico_to_str(dico):
    res = "{\n"
    for kanji in dico:
        print(kanji)
        res  += "  '"+kanji+"': [\n"
        for line in dico[kanji]:
            res += "    "+str(line)+",\n"
        res += "  ],\n"
    res += "}\n"
    return res

def save(filename, size, dico):
    lines = []
    with open("pattern_kanji.html", 'r') as f:
        for line in f:
            if r"{}//SPECIALTAG101" in line:
                print(line)
                line = line.replace(r"{}//SPECIALTAG101", dico_to_str(dico))
                print(line)
            lines.append(line)
    
    with open(f"pattern_kanji_{filename}_{size}x{size}.html", "w", encoding="utf-8") as f:
        f.writelines(lines)
                

fileOpener = tk.Button(fileFrame, command=askFile, text="Choose file")
fileOpener.grid(column=2, row=0)

buttonTreat = tk.Button(fileFrame, command=treatFile, text="Process file", state="disabled")
buttonTreat.grid(column=3, row=0)

root.mainloop()


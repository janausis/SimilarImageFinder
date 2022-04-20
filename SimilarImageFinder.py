import os
import imagehash
from PIL import Image
import numpy as np
tmpRoot = None
slide_num = 0
total = 0
first = 0
image_cache = []


def find_similar(location=None, dir=None, similarity=80, hashList=None):
    hash_size = 80
    if location == None:
        print("No Location given")
        return
    if dir == None:
        print("No Folder given")
        return

    location = location.replace("\\", "/")
    fnames = os.listdir(dir)
    threshold = 1 - similarity/100
    diff_limit = int(threshold*(hash_size**2))

    hash1 = []
    hash2 = []
    if hashList is not None:
        for i in hashList:
            if i["filename"] == location:
                hash1 = i["hash"]
                break
    else:
        with Image.open(location) as img:
            hash1 = imagehash.average_hash(img, hash_size).hash

    data = {"files": "", "similarTo": location, "directory": dir}
    fileList = []

    if len(hash1) <= 0:
        with Image.open(location) as img:
            hash1 = imagehash.average_hash(img, hash_size).hash

    for image in fnames:
        if image == location.split("/")[-1]:
            fileList.append({"filename": image, "similarity": 1.0, "isSelf": True})
            continue

        if hashList is not None:
            for i in hashList:
                if i["filename"] == os.path.join(dir,image).replace("\\", "/"):
                    hash2 = i["hash"]
                    break
        else:
            with Image.open(os.path.join(dir,image)) as img:
                hash2 = imagehash.average_hash(img, hash_size).hash

        if len(hash2) <= 0:
            with Image.open(os.path.join(dir,image)) as img:
                hash2 = imagehash.average_hash(img, hash_size).hash

        sim = 100 - np.count_nonzero(hash1 != hash2)
        if sim > similarity:
            fileList.append({"filename": image, "similarity": round(sim/100, 4), "isSelf": False})

    # when only the original image is in the list
    if len(fileList) <= 1:
        fileList = []

    data["files"] = fileList
    return data

def center(toplevel):
    toplevel.update_idletasks()

    # Tkinter way to find the screen resolution
    screen_width = toplevel.winfo_screenwidth()
    screen_height = toplevel.winfo_screenheight()

    # PyQt way to find the screen resolution
    # app = QtGui.QApplication([])
    # screen_width = app.desktop().screenGeometry().width()
    # screen_height = app.desktop().screenGeometry().height()

    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = screen_width/2 - size[0]/2
    y = screen_height/2 - size[1]/2

    toplevel.geometry("+%d+%d" % (x, y))

def Main():
    from tkinter import messagebox
    import tkinter as tk
    global tmpRoot

    root = tk.Tk()
    root.title('Similar Image Finder')
    root.geometry('200x100')
    root.config(bg='#222222', bd=0, padx=0, pady=0, highlightthickness=0)
    root.bind('<Escape>', lambda event: root.state('normal'))
    root.bind('<F11>', lambda event: root.state('zoomed'))

    def exit_app():
        try:
            root.destroy()
        except:
            pass

    def similarToFile():
        singleFile()

    def findInFolder():
        from tkinter import filedialog
        from glob import glob
        global tmpRoot

        tmpRoot.filename = filedialog.askdirectory(initialdir = os.getcwd(),title = "Select Folder")
        path = tmpRoot.filename
        if path is None or path == "":
            Main()
            return


        png_files = list(glob(path + "/**/*.png", recursive=True))
        jpg_files = list(glob(path + "/**/*.jpg", recursive=True))
        bmp_files = list(glob(path + "/**/*.bmp", recursive=True))
        gif_files = list(glob(path + "/**/*.gif", recursive=True))
        jpeg_files = list(glob(path + "/**/*.jpeg", recursive=True))
        cache = png_files + jpg_files + bmp_files + gif_files + jpeg_files

        hashList = []
        root2 = tk.Tk()
        root2.title(f'Creating hashes')
        root2.geometry('500x0')
        root2.config(bg='#222222', bd=0, padx=0, pady=0, highlightthickness=0)
        center(root2)
        def stop():
            root2.quit()
        root2.after(0, stop)
        root2.mainloop()
        hash_size = 80

        for file in cache:
            img = Image.open(file)
            hashList.append({"filename": file.replace("\\", "/"), "hash": imagehash.average_hash(img, hash_size).hash})
            fn = file.replace("\\", "/").split("/")[-1]
            root2.title(f'Creating hash for {fn}')
            root2.after(0, stop)
            root2.mainloop()


        try:
            root2.destroy()
        except:
            pass



        for file in cache:
            singleFile(file, hashList)
        Main()


    tk.Label(root, text='Mode').pack()
    tk.Button(root, command=similarToFile, text='Similar to one file').pack()
    tk.Button(root, command=findInFolder, text='Find all Similar in Folder').pack()
    tk.Button(root, text='Exit', command=exit_app).pack()

    root.focus_force()

    center(root)
    tmpRoot = root

    root.mainloop()


def singleFile(file=None, hashList=None):
    repeat = False
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from PIL import Image, ImageTk
    global tmpRoot, image_cache
    first = 0
    image_cache = []

    if file == None:
        tmpRoot.filename = filedialog.askopenfilename(initialdir = os.getcwd(),title = "Input File",filetypes = (("all files","*.*"),))
        FileInput = tmpRoot.filename.replace("\\", "/")
    else:
        repeat = True
        FileInput = file

    try:
        tmpRoot.destroy()
    except:
        pass

    root2 = tk.Tk()
    root2.title(f'Scanning for {FileInput.split("/")[-1]}')
    root2.geometry('500x0')
    root2.config(bg='#222222', bd=0, padx=0, pady=0, highlightthickness=0)
    center(root2)
    def stop():
        root2.quit()
    root2.after(0, stop)
    root2.mainloop()


    dir = os.path.dirname(FileInput)
    if not repeat:
        s = find_similar(FileInput, dir)
    else:
        s = find_similar(FileInput, dir, 80, hashList)
    try:
        root2.destroy()
    except:
        pass

    if len(s["files"]) <= 1:
        if not repeat:
            messagebox.showinfo("No similar Images", "There were no similar images found")
            Main()
        return

    first = 0

    root = tk.Tk()
    root.title(f'Similar to {FileInput.split("/")[-1]}')
    root.geometry('800x600')
    root.config(bg='#222222', bd=0, padx=0, pady=0, highlightthickness=0)
    root.bind('<Escape>', lambda event: root.state('normal'))
    root.bind('<F11>', lambda event: root.state('zoomed'))

    class Slide(tk.Label):
        def __init__(self, master, image_path: str = '', scale: float = 1.0, **kwargs):
            tk.Label.__init__(self, master, **kwargs)
            self.configure(bg=master['bg'])
            self.img = None if not image_path else Image.open(image_path)
            self.p_img = None
            self.scale = scale
            self.bind("<Configure>", self.resizing)

        def set_image(self, image_path: str, s=False):
            backslash = "/"
            r = image_path.replace("\\", "/").split(backslash)[-1]
            if s:
                root.title(f'Original Image: {r}')
            else:
                root.title(f'Image: {r}')

            self.img = Image.open(image_path)
            self.resizing()

        def get_image(self, image_path: str):
            return image_path

        def resizing(self, event=None):
            if self.img:
                iw, ih = self.img.width, self.img.height
                mw, mh = self.master.winfo_width(), self.master.winfo_height()

                if iw > ih:
                    ih = ih * (mw / iw)
                    r = mh / ih if (ih / mh) > 1 else 1
                    iw, ih = mw * r, ih * r
                else:
                    iw = iw * (mh / ih)
                    r = mw / iw if (iw / mw) > 1 else 1
                    iw, ih = iw * r, mh * r

                self.p_img = ImageTk.PhotoImage(self.img.resize((int(iw * self.scale), int(ih * self.scale))))
                self.config(image=self.p_img)

    total = 0
    slide_num = 0

    def get_slides(event=None):
        global total
        cache = []

        if len(s["files"]) <= 1:
            root.destroy()
            if not repeat:
                Main()
            return

        for file in s["files"]:
            cache.append(os.path.join(dir, file["filename"]))

        return cache

    image_cache = get_slides()

    def commit_slide(n, t):
        try:

            if s["files"][n]["isSelf"]:
                slide.set_image(image_cache[n], True)
            else:
                slide.set_image(image_cache[n])
            # image_cache.remove(image_cache[n])

            status.config(text=f'{n + 1} of {t} images')
        except Exception as e:
            print(e)


    def next_slide(event=None):
        global slide_num, total, first

        if first <= 1:
            slide_num = -1
            first = 2

        slide_num = (slide_num + 1) % len(image_cache)  # wrap
        commit_slide(slide_num, len(image_cache))

    root.bind('<Key-Right>', next_slide)

    def previous_slide(event=None):
        global slide_num, total, first

        if first <= 1:
            slide_num = 0
            first = 2

        slide_num = range(len(image_cache))[slide_num - 1]  # wrap
        commit_slide(slide_num, len(image_cache))

    def deleteFile(event=None):
        global slide_num, image_cache, total

        if s["files"][slide_num]["isSelf"]:
            answer = messagebox.askokcancel("Original Image", "Are you sure you want to delete the Original Image")
        else:
            answer = messagebox.askokcancel("Delete similar Image", "Are you sure you want to delete this similar image")
        if not answer:
            return


        total -= 1

        os.remove(image_cache[slide_num])
        for file in s["files"]:
            if file["filename"] == image_cache[slide_num].replace("\\", "/").split("/")[-1]:
                s["files"].remove(file)


        if len(s["files"]) <= 1:
            root.destroy()
            if not repeat:
                Main()
            return

        image_cache = get_slides()

        slide_num = range(len(image_cache))[slide_num - 1]  # wrap
        commit_slide(slide_num, len(image_cache))


    def exit_app():
        try:
            root.quit()
            root.destroy()
            if not repeat:
                Main()
            return
        except:
            pass

    root.bind('<Key-Left>', previous_slide)
    root.bind('<Delete>', deleteFile)

    # init display widgets
    slide = Slide(root)
    slide.pack()

    tk.Button(root, text='prev', command=previous_slide).place(relx=.02, rely=.99, anchor='sw')
    tk.Button(root, text='next', command=next_slide).place(relx=.98, rely=.99, anchor='se')
    tk.Button(root, text='Exit', command=exit_app).place(relx=.65, rely=.99, anchor='s')
    tk.Button(root, text='Remove', command=deleteFile).place(relx=.35, rely=.99, anchor='s')



    status = tk.Label(root, bg='white', font=('helvetica', 10))
    status.place(relx=.5, rely=.99, anchor='s')

    # init first slide

    if first == 0:
        first = 1
        if first == 1:
            pass

        status.config(text=f'Click "prev" or "next" to begin.')
        root.mainloop()

    try:
        commit_slide(slide_num, total)
        root.focus_force()
        center(root)
        root.mainloop()
    except:
        pass



if __name__ == '__main__':
    Main()

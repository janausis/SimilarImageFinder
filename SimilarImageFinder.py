import os
import imagehash
from PIL import Image
import numpy as np
import threading
tmpRoot = None
slide_num = 0
total = 0
first = 0
image_cache = []

def get_hash(location, hash_size, hashList=None):
    hash1 = []
    location = location.replace("\\", "/")

    # Search in hashlist if generated
    if hashList is not None:
        for i in hashList:
            if i["filename"] == location:
                hash1 = i["hash"]
                break
    else:
        # Create hash
        with Image.open(location) as img:
            hash1 = imagehash.average_hash(img, hash_size).hash

    # If hash could not be generated previously, try again
    if len(hash1) <= 0:
        with Image.open(location) as img:
            hash1 = imagehash.average_hash(img, hash_size).hash

    return hash1


def find_similar(location=None, dir=None, similarity=80, hashList=None):
    hash_size = 80
    if location == None:
        print("No Location given")
        return
    if dir == None:
        print("No Folder given")
        return


    fnames = os.listdir(dir)
    threshold = 1 - similarity/100
    diff_limit = int(threshold*(hash_size**2))

    hash1 = get_hash(location, hash_size, hashList)

    # Initialize json
    data = {"files": "", "similarTo": location, "directory": dir}
    fileList = []

    # Every file in the folder
    for image in fnames:
        # is the current file the same as the input file
        if image == location.split("/")[-1]:
            fileList.append({"filename": image, "similarity": 1.0, "isSelf": True})
            continue
        try:
            hash2 = get_hash(os.path.join(dir, image), hash_size, hashList)
        except:
            continue

        sim = 100 - np.count_nonzero(hash1 != hash2)
        if sim > similarity:
            fileList.append({"filename": image, "similarity": round(sim/100, 4), "isSelf": False})

    # when only the original image is in the list
    if len(fileList) <= 1:
        fileList = []

    data["files"] = fileList
    return data


def center(toplevel):
    # Center Tkinter view on screen
    toplevel.update_idletasks()

    # Tkinter way to find the screen resolution
    screen_width = toplevel.winfo_screenwidth()
    screen_height = toplevel.winfo_screenheight()

    size = tuple(int(_) for _ in toplevel.geometry().split('+')[0].split('x'))
    x = screen_width/2 - size[0]/2
    y = screen_height/2 - size[1]/2

    toplevel.geometry("+%d+%d" % (x, y))


def Main():
    # Main Screen
    from tkinter import messagebox
    import tkinter as tk
    global tmpRoot

    root = tk.Tk()
    root.title('Similar Image Finder')
    root.geometry('300x195')
    root.config(bg='#222222', bd=0, padx=0, pady=0, highlightthickness=0)

    def exit_app():
        try:
            root.destroy()
        except:
            pass

        exit()


    def similarToFile():
        from tkinter import filedialog
        tmpRoot.filename = filedialog.askopenfilename(initialdir = os.getcwd(),title = "Input File",filetypes = (("all files","*.*"),))
        file = tmpRoot.filename.replace("\\", "/")

        findInFolder(file)

    def inFolder():
        findInFolder()

    tk.Label(root, text='Similar Image Finder', fg="white", bg="#222222", padx=15, pady=10, font=("Calibri", 20, 'bold')).pack()
    tk.Button(root, command=similarToFile, text='Similar to one file', fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).pack(padx=10, pady=5)
    tk.Button(root, command=inFolder, text='Find all Similar in Folder', fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).pack(padx=10, pady=5)
    tk.Button(root, text='Exit', command=exit_app, fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).pack(padx=10, pady=5)

    root.focus_force()

    center(root)
    tmpRoot = root

    root.mainloop()


def findInFolder(MainFile=None):
    import tkinter as tk
    from tkinter import filedialog, messagebox
    from glob import glob
    global tmpRoot

    if MainFile is None:
        # get directory to search in
        tmpRoot.filename = filedialog.askdirectory(initialdir = os.getcwd(),title = "Select Folder")
        path = tmpRoot.filename
        if path is None or path == "":
            return

    else:
        path = os.path.dirname(MainFile)

    try:
        tmpRoot.destroy()
    except:
        pass

    # find all image files in this folder
    png_files = list(glob(path + "/**/*.png", recursive=True))
    jpg_files = list(glob(path + "/**/*.jpg", recursive=True))
    bmp_files = list(glob(path + "/**/*.bmp", recursive=True))
    gif_files = list(glob(path + "/**/*.gif", recursive=True))
    jpeg_files = list(glob(path + "/**/*.jpeg", recursive=True))
    cache = png_files + jpg_files + bmp_files + gif_files + jpeg_files

    # Log window
    hashList = []
    root2 = tk.Tk()
    root2.title(f'Log')
    root2.geometry('500x250')
    root2.config(bg='#222222', bd=0, padx=0, pady=0, highlightthickness=0)
    center(root2)

    scrollbar = tk.Scrollbar(root2)

    mylist = tk.Listbox(root2, yscrollcommand = scrollbar.set, width=500, height=250, fg="white", bg="#111111")
    mylist.insert(tk.END, 'Starting Hash Generation:\n\n')
    mylist.pack()
    #mylist.insert(tk.END, 'Starting Hash Generation...\n', font=("Calibri", 12, "bold"))

    scrollbar.config( command = mylist.yview )
    scrollbar.pack( side = tk.RIGHT, fill = tk.Y )
    root2.update_idletasks()

    hash_size = 80

    """
    firstly generate a hash for every file in the Folder
    then scan each file and compare with other files for similarity
    """
    def hashGen():
        # Store hashes for each file in list
        for file, n in zip(cache, range(len(cache))):
            hashList.append({"filename": file.replace("\\", "/"), "hash": get_hash(file, hash_size)})
            fn = file.replace("\\", "/").split("/")[-1]

            text = f'Creating hash for {fn}. {n+1}/{len(cache)}'
            root2.title(text)
            mylist.insert(tk.END, text)
            mylist.yview(tk.END)
            root2.update_idletasks()

        mylist.insert(tk.END, '')
        mylist.insert(tk.END, "Scanning Images:")

        # Scan each file for duplicates
        if MainFile is None:
            for f, n in zip(cache, range(len(cache))):
                singleFile(f, hashList, mylist, True, False, n+1, root2)
                mylist.yview(tk.END)
                root2.update_idletasks()
        else:
            singleFile(MainFile, hashList, mylist, False)
            mylist.yview(tk.END)
            root2.update_idletasks()

        # End of processing
        try:
            text = f"Finished processing {len(cache)} files"
            mylist.insert(tk.END, text)
            mylist.insert(tk.END, "Press enter to exit")
            mylist.yview(tk.END)
            root2.update_idletasks()
            root2.title(text)
            root2.bind('<Return>', lambda event: root2.destroy())

        except:
            pass


    root2.after(0, hashGen)
    root2.mainloop()

    Main()


def singleFile(FileInput, hashList, mylist, repeat, autoDelete=False, n=0, root3=None):

    import tkinter as tk
    from tkinter import filedialog, messagebox
    from PIL import Image, ImageTk
    global tmpRoot, image_cache
    first = 0
    image_cache = []

    FileInput = FileInput.replace("\\", "/")

    if n == 0:
        text = f'Scanning for {FileInput.split("/")[-1]}'
    else:
        text = f'Scanning for {FileInput.split("/")[-1]}. {n}/{len(hashList)}'

    mylist.insert(tk.END, text)
    if root3 is not None:
        root3.title(text)

    # Scan for similar files
    dir = os.path.dirname(FileInput)
    s = find_similar(FileInput, dir, 80, hashList)


    if len(s["files"]) <= 1:
        if not repeat:
            messagebox.showinfo("No similar Images", "There were no similar images found")
        return

    if autoDelete:
        pass
        """deletePath = os.path.join(dir, "deleted")
        if not os.path.exists(deletePath):
            os.mkdir(deletePath)
        for file in s["files"]:
            os.rename(os.path.join(dir, file["filename"]), os.path.join(deletePath, file["filename"]))"""


    first = 0

    # Allow the selection of which files to keep and which to delete
    root = tk.Tk()
    root.title(f'Similar to {FileInput.split("/")[-1]}')
    root.geometry('800x535')
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
            image_path = image_path.replace("\\", "/")
            backslash = "/"
            r = image_path.split(backslash)[-1]
            if s:
                root.title(f'Original Image: {r}')
            else:
                root.title(f'Image: {r}')

            name.config(text=r)

            self.img = Image.open(image_path)
            try:
                self.resizing()
            except:
                pass

        # Auto resize to window
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

                self.p_img = ImageTk.PhotoImage(self.img.resize((int(iw * self.scale), int(ih * self.scale))), master=self.master)
                self.config(image=self.p_img)

    total = 0
    slide_num = 0

    def get_slides(event=None):
        global total
        cache = []

        if len(s["files"]) <= 1:
            root.destroy()
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
            import traceback
            traceback.print_exc()


    def next_slide(event=None):
        global slide_num, total, first

        slide_num = (slide_num + 1) % len(image_cache)  # wrap
        commit_slide(slide_num, len(image_cache))

    root.bind('<Key-Right>', next_slide)

    def previous_slide(event=None):
        global slide_num, total, first

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

        f = image_cache[slide_num].replace("\\", "/").split("/")[-1]
        deletePath = os.path.join(dir, "deleted")
        if not os.path.exists(deletePath):
            os.mkdir(deletePath)

        os.rename(os.path.join(dir, f), os.path.join(deletePath, f))
        for file in s["files"]:
            if file["filename"] == f:
                s["files"].remove(file)
                mylist.insert(tk.END, f'Removed {file["filename"].split("/")[-1]}')
        for file in hashList:
            if file["filename"] == image_cache[slide_num].replace("\\", "/"):
                hashList.remove(file)


        if len(s["files"]) <= 1:
            try:
                root.destroy()
            except:
                pass
            return

        image_cache = get_slides()

        slide_num = range(len(image_cache))[slide_num - 1]  # wrap
        commit_slide(slide_num, len(image_cache))


    def exit_app():
        try:
            root.quit()
            root.destroy()
            return
        except:
            pass

    root.bind('<Key-Left>', previous_slide)
    root.bind('<Delete>', deleteFile)

    # init display widgets
    slide = Slide(root)
    slide.pack()

    tk.Button(root, text='prev', command=previous_slide, fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).place(relx=.02, rely=.99, anchor='sw')
    tk.Button(root, text='next', command=next_slide, fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).place(relx=.98, rely=.99, anchor='se')
    tk.Button(root, text='Exit', command=exit_app, fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).place(relx=.90, rely=.99, anchor='se')
    tk.Button(root, text='Remove', command=deleteFile, fg="white", bg="#555555", padx=5, pady=3, font=("Calibri", 12)).place(relx=.10, rely=.99, anchor='sw')



    status = tk.Label(root, fg="white", bg="#222222", padx=15, pady=10, font=("Calibri", 12, 'bold'))
    status.place(relx=.5, rely=.99, anchor='s')

    name = tk.Label(root, text="None", fg="white", bg="#222222", padx=5, pady=5, font=("Calibri", 12, 'bold'))
    name.place(anchor='nw')

    try:
        slide_num = 0
        next_slide()
        previous_slide()
        root.focus_force()
        center(root)
        root.mainloop()
    except:
        pass



if __name__ == '__main__':
    Main()

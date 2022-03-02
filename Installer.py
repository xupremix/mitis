import platform
def main():    
    if platform.system() == "Windows":
        windowsInstall()
    elif platform.system() == "Darwin":
        macInstall()
    else:
        linuxInstall()

def windowsInstall():
    from os import system
    print("Upgrading pip version")
    system("python -m pip install --upgrade pip")
    print("Installing tkinter")
    system("pip3 install tk")
    print("Installing opencv")
    system("pip3 install opencv-python")
    print("Installing munch")
    system("pip3 install munch")
    print("Installing numpy")
    system("pip3 install numpy")
    print("Installing pygame")
    system("pip3 install pygame")
    print("Installing pyaudio")
    system("pip3 install pyaudio")
    print("Installing pillow")
    system("pip3 install pillow")
    
def macInstall():
    from os import system
    print("Upgrading pip version")
    system("python -m pip install --upgrade pip")
    print("Installing tkinter")
    system("pip3 install tk")
    print("Installing opencv")
    system("pip3 install opencv-python")
    print("Installing munch")
    system("pip3 install munch")
    print("Installing numpy")
    system("pip3 install numpy")
    print("Installing pygame")
    system("pip3 install pygame")
    print("Installing pyaudio")
    system("pip3 install pyaudio")
    print("Installing pillow")
    system("pip3 install pillow")

def linuxInstall():
    from os import system
    print("Upgrading pip version")
    system("sudo python3 -m pip install --upgrade pip")
    print("Installing tkinter")
    system("sudo apt-get install python3-tk")
    print("Installing opencv")
    system("sudo apt-get install python3-opencv")
    print("Installing munch")
    system("pip3 install munch")
    print("Installing numpy")
    system("pip3 install numpy")
    print("Installing pygame")
    system("sudo apt-get install python3-pygame")
    print("Installing pyaudio")
    system("sudo apt-get install portaudio19-dev python3-pyaudio")
    print("Installing pillow")
    system("pip3 install pillow")

if __name__ == '__main__':
    main()
    

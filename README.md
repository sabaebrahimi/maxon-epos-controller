# Maxon epos Controller
A linux based desktop app for controlling maxon motor epos driver.

## overview
This project is a linux based desktop app for some methods of epos motor driver. You can also check the current value every 500ms. With this app you'll be able to controll your maxon motor in 4 modes:
* Controll it manually. While the `Rotate CCW` or `Rotate CW` buttons are pressed, the motor rotates clockwise or counterclockwise.
* Move motor for a specific duration. After you choose this method and set duration and velocity, the motor rotates for a period. Note that you can stop it with `Stop` button. 
* Move motor to a specific position. This method is same as poistion profile in epos driver command library. 
* Move motor N turns. This method rotates the motor for N turns.

Project UI is developed by PyQt5.

## Project structure

    .
    ├── main.py                   # Code logic  
    ├── mainwindow.py             # Generated ui file based on `mainwindow.ui`
    ├── mainwindow.ui             # UI file
    ├── LICENSE
    └── README.md
    
`mainwindow.ui` is added in case you want to change the UI or add more features. After editing the ui, regenerate mainwindow.py with this command:
```
pyuic5 mainwindow.ui -o mainwindow.py
```

## Install and run
1. Download epos linux library from [this link](https://www.maxongroup.net.au/maxon/view/product/control/Positionierung/280937?download=show). Extract the zip file and install it. Follow the instructions of installing this library from [here](https://www.maxongroup.com/medias/sys_master/8823917281310.pdf).

2. Download and install python v3.x on your system. Install python from [here](https://www.python.org/downloads/).

3. Install pyqt5 on your system. for linux based os run this command:

```
sudo apt-get install python3-pyqt5
```

4. Go to `main.py` file and edit this line based on your working directory, your system model and 32bit|64bit:
```
path1 = '/home/pi/EPOS_Linux_Library/lib/arm/v7/libEposCmd.so.6.7.1.0'
```
For example I run this app on rasbperrypi3 model B.

5. Run and Enjoy!


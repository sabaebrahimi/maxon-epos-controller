from PyQt5 import QtWidgets
from PyQt5.QtCore import QTimer

from mainwindow import Ui_MainWindow
from enum import Enum

import sys

from ctypes import *
from os.path import exists
from enum import Enum

import time

path1 = '/home/pi/EPOS_Linux_Library/lib/arm/v7/libEposCmd.so.6.7.1.0'

cdll.LoadLibrary(path1)
epos = CDLL(path1)

# How many increments is one turn
one_turn = 73728

# Node ID must match with Hardware Dip-Switch setting of EPOS4
NodeID = 1
keyhandle = 0
# return variable from Library Functions
ret = 0
pErrorCode = c_uint()
pDeviceErrorCode = c_uint()

#Gear settings
gear_reduction = 18
max_rpm = 8000

#Current interval
read_current_interval = 500

#default speed
default_speed = 50

# working modes
class Mode(Enum):
    MOVE_N_ROUNDS = 1,
    MOVE_TO_POSITION = 2,
    MOVE_MANUALLY = 3,
    MOVE_IN_DURATION = 4

class Direction(Enum):
    CW = 1,
    CCW = 2

class mainwindow(QtWidgets.QMainWindow):

    def __init__(self, pErrorCode):
        super(mainwindow, self).__init__()
        self.ui = Ui_MainWindow()
        self.moving_method = Mode.MOVE_MANUALLY
        self.velocity = default_speed * gear_reduction
        self.position = 0
        self.no_of_turns = 0
        self.duration = 0
        self.current = 0
        self.is_velocity_btn_pressed = False
        self.timer = QTimer()
        self.pErrorCode = pErrorCode
        self.direction = Direction.CW
        self.ui.setupUi(self)
        self.uiInitialize()

    def uiInitialize(self):
        self.setup_ui_connection()
        self.timer.timeout.connect(self.set_current_ls)
        self.timer.start(read_current_interval)
        self.ui.groupBox_3.setEnabled(False)
        self.ui.groupBox_2.setEnabled(False)

    def setup_ui_connection(self):
        self.ui.StartBtn.clicked.connect(self.start_btn_pressed)
        self.ui.StopBtn.clicked.connect(self.stop_btn_pressed)
        self.set_radio_btns_connection()
        self.set_inputs_connection()
        self.set_manual_btns_connection()
    
    def set_inputs_connection(self):
        self.ui.velocityInput.textChanged.connect(lambda text: self.on_velocity_input_change(text))
        self.ui.PositionInput.textChanged.connect(lambda text: self.on_position_input_change(text))
        self.ui.DurationInput.textChanged.connect(lambda text: self.on_duration_input_change(text))
        self.ui.TurnsInput.textChanged.connect(lambda text: self.on_turns_input_change(text))
    
    def set_manual_btns_connection(self):
        self.ui.ManualCW.pressed.connect(lambda: self.on_manual_btn_clicked(Direction.CW, True))
        self.ui.ManualCW.released.connect(lambda: self.on_manual_btn_clicked(Direction.CW, False))
        self.ui.ManualCCW.pressed.connect(lambda: self.on_manual_btn_clicked(Direction.CCW, True))
        self.ui.ManualCCW.released.connect(lambda: self.on_manual_btn_clicked(Direction.CCW, False))
        
    def set_radio_btns_connection(self):
        self.ui.MoveForDuration.clicked.connect(lambda: self.on_radio_btn_clicked(Mode.MOVE_IN_DURATION))
        self.ui.MoveNRounds.clicked.connect(lambda: self.on_radio_btn_clicked(Mode.MOVE_N_ROUNDS))
        self.ui.MoveToPosition.clicked.connect(lambda: self.on_radio_btn_clicked(Mode.MOVE_TO_POSITION))
        self.ui.CWRadio.clicked.connect(lambda: self.on_direction_radio_btn_change(Direction.CW))
        self.ui.CCWRadio.clicked.connect(lambda: self.on_direction_radio_btn_change(Direction.CCW))
    
    def wait_acknowledged(self):
        ObjectIndex = 0x6041
        ObjectSubindex = 0x0
        NbOfBytesToRead = 0x02
        pNbOfBytesRead = c_uint()
        pData = c_uint()
        pErrorCode = c_uint()

        # Setpoint Acknowledged
        Mask_Bit12 = 0x1000
        Bit12 = 0
        i = 0

        while True:
            # Read Statusword
            ret = epos.VCS_GetObject(keyhandle, NodeID, ObjectIndex, ObjectSubindex, byref(
                pData), NbOfBytesToRead, byref(pNbOfBytesRead), byref(pErrorCode))
            Bit12 = Mask_Bit12 & pData.value

            # Timed out
            if i > 20:
                return 0
                break

            if Bit12 == Mask_Bit12:
                time.sleep(1)
                i += 1

            # Bit12 reseted = new profile started
            else:
                return 1
                break

    
    def set_current_ls(self):
        current_short = c_short()
        epos.VCS_GetCurrentIsAveraged(keyhandle, NodeID, byref(current_short), byref(pErrorCode))
        self.current = current_short.value
        self.ui.Current.setText(str(self.current))

    def move_n_rounds(self, n, velocity, pErrorCode):
        epos.VCS_ActivateProfilePositionMode(keyhandle, NodeID, byref(pErrorCode))
        
        epos.VCS_SetPositionProfile(keyhandle, NodeID, velocity, 10000, 10000, byref(pErrorCode))
        
        target_position = int(n * one_turn)
        
        if self.direction == Direction.CW:
            target_position *= -1
        
        epos.VCS_MoveToPosition(keyhandle, NodeID, target_position, 0, 0, byref(pErrorCode))

    def move_to_position(self, target_position, velocity, pErrorCode):

        epos.VCS_ActivateProfilePositionMode(keyhandle, NodeID, byref(pErrorCode))

        epos.VCS_SetPositionProfile(keyhandle, NodeID, velocity, 10000, 10000, byref(pErrorCode))

        if self.direction == Direction.CW:
            target_position *= -1

        epos.VCS_MoveToPosition(keyhandle, NodeID, target_position, 0, 0, byref(pErrorCode))

    def move_with_velocity(self, velocity, direction, pErrorCode):
        epos.VCS_ActivateProfileVelocityMode(keyhandle, NodeID, pErrorCode)

        if direction == Direction.CW:
            velocity *= -1

        if self.is_velocity_btn_pressed == True:
            epos.VCS_MoveWithVelocity(keyhandle, NodeID, velocity, pErrorCode)
        else: 
            epos.VCS_HaltVelocityMovement(keyhandle, NodeID,pErrorCode)

    # duration unit is second
    def move_for_time(self, duration, velocity, pErrorCode):
        epos.VCS_ActivateProfileVelocityMode(keyhandle, NodeID, pErrorCode)

        if self.direction == Direction.CW:
            velocity *= -1

        start_time = time.time()

        while time.time() - start_time < duration:
            epos.VCS_MoveWithVelocity(keyhandle, NodeID, velocity, pErrorCode)
        
        epos.VCS_HaltVelocityMovement(keyhandle, NodeID,pErrorCode)


    def start_btn_pressed(self):
        if self.velocity > max_rpm:
            self.velocity = max_rpm
            print("Velocity out of range")

        if self.moving_method == Mode.MOVE_N_ROUNDS:
            self.move_n_rounds(self.no_of_turns, self.velocity, self.pErrorCode)
        elif self.moving_method == Mode.MOVE_TO_POSITION:
            self.move_to_position(self.position, self.velocity, self.pErrorCode)
        elif self.moving_method == Mode.MOVE_IN_DURATION:
            self.move_for_time(self.duration, self.velocity, self.pErrorCode)


    def stop_btn_pressed(self):
        if self.moving_method == Mode.MOVE_IN_DURATION or self.moving_method == Mode.MOVE_MANUALLY:
            epos.VCS_HaltVelocityMovement(keyhandle, NodeID, pErrorCode)
        else:
            epos.VCS_HaltPositionMovement(keyhandle, NodeID, pErrorCode)
    
    def on_radio_btn_clicked(self, selected_moving_method):
        self.moving_method = selected_moving_method
        self.set_inputs_disability()
        
    def set_inputs_disability(self):
        if self.ui.MoveForDuration.isChecked():
            self.ui.groupBox_3.setEnabled(True)
            self.ui.groupBox_2.setEnabled(False)
        elif self.ui.MoveNRounds.isChecked():
            self.ui.groupBox_3.setEnabled(False)
            self.ui.groupBox_2.setEnabled(True)
            self.ui.PositionInput.setEnabled(False)
            self.ui.TurnsInput.setEnabled(True)
        elif self.ui.MoveToPosition.isChecked():
            self.ui.groupBox_3.setEnabled(False)
            self.ui.groupBox_2.setEnabled(True)
            self.ui.PositionInput.setEnabled(True)
            self.ui.TurnsInput.setEnabled(False)

    def on_velocity_input_change(self, velocity_value):
        if velocity_value != '':
            self.velocity = int(velocity_value) * gear_reduction
        else:
            self.velocity = default_speed * gear_reduction

    def on_position_input_change(self, position_value):
        if position_value != '':
            self.position = int(position_value)

    def on_turns_input_change(self, turns_value):
        if turns_value != '':
            self.no_of_turns = float(turns_value)

    def on_duration_input_change(self, duration_value): 
        if duration_value != '':
            self.duration = int(duration_value)

    def on_manual_btn_clicked(self, direction_value, is_pressed):
        self.is_velocity_btn_pressed = is_pressed
        self.moving_method = Mode.MOVE_MANUALLY
        self.move_with_velocity(self.velocity, direction_value, pErrorCode)

    def on_direction_radio_btn_change(self, direction_value):
        self.direction = direction_value


if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    keyhandle = epos.VCS_OpenDevice(b'EPOS4', b'MAXON SERIAL V2', b'USB', b'USB0', byref(pErrorCode))

    if keyhandle != 0:
        ret = epos.VCS_GetDeviceErrorCode(keyhandle, NodeID, 1, byref(pDeviceErrorCode), byref(pErrorCode) )
        
        if pDeviceErrorCode.value == 0:
            epos.VCS_SetEnableState(keyhandle, NodeID, byref(pErrorCode))
            application = mainwindow(pErrorCode)

            application.show()
        else:
            print("error")

    sys.exit(app.exec())

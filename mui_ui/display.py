# display class

import crc8
import serial
import time

import RPi.GPIO as GPIO 

from threading import Lock

try:
   from matrix import Matrix, check_diff_range
except ImportError:
   from . import Matrix, check_diff_range

ACK = 0x06
NACK = 0x15

class Display(object):
    """
    mui Display API class
    """
    def __init__(self, device_name='/dev/ttyS0', debug=False):
        print("create display class")
        self.mutex = Lock()

        # create led matrix
        self.ledMatrix = Matrix(200, 32)
        self.ledMatrixBuf = Matrix(200, 32) # buffer for old data

        # open UART port
        self.port = serial.Serial(device_name,
                     115200,
                     parity=serial.PARITY_NONE,
                     bytesize=serial.EIGHTBITS,
                     stopbits=1,
                     timeout=1)
        
        self.debug = debug
        self._reset()
        self.port.reset_input_buffer()
        self.port.reset_output_buffer()


    def _reset(self):
        GPIO.setmode(GPIO.BCM)
        GPIO.setup(26, GPIO.OUT)
        GPIO.output(26, GPIO.LOW)
        time.sleep(0.02)
        GPIO.output(26, GPIO.HIGH)
        time.sleep(0.5)


    def turnOn(self, fade):
        packet = self._createDisplayReqCommand(0, fade, 100)
        self._writePacket(packet)
        self._recivePacket(6)

    def turnOff(self, fade):
        packet = self._createDisplayReqCommand(2, fade, 0)
        self._writePacket(packet)
        self._recivePacket(6)

    def setLayout(self, matrixInfo):
        # s = time.time()
        # for y in range(matrixInfo.height):
        #     for x in range(matrixInfo.width):
        #         self.ledMatrix.matrix[y + matrixInfo.startY][x + matrixInfo.startX] = matrixInfo.matrix[y][x]
        self.ledMatrix.matrix = matrixInfo.matrix

        # e = time.time()
        # print('??? setLayout ', (e - s))

    def updateLayout(self):
        #sT = time.time()
        packet = self._createLayoutCommandForDiff()
        if packet == None:
            return

        self._writePacket(packet)
        self._recivePacket(6)

        # store current layout info
        self.ledMatrixBuf.copy(self.ledMatrix)
        #eT = time.time()
        #print("create comannd time {0}".format(cT - sT))
        #print("send comannd time {0}".format(rT - sT))

    def refreshDisplay(self, fade, duty):
        packet = self._createDisplayReqCommand(1, fade, duty)
        self._writePacket(packet)
        self._recivePacket(6)

    def _writePacket(self, packet):
        self.mutex.acquire()
        self.port.write(packet)
#        packetlen = len(packet)
#        buf = bytearray(1)
#        for i in range(0, packetlen):
#                buf[0] = packet[i]
#                self.port.write(buf)
#                if ( i // 4 == 0 ):
#                        self.port.flush()

        self.port.flush()
        if self.debug is True:
            print('>', packet)
        # time.sleep(0.1)
        self.mutex.release()

    def _recivePacket(self, rdlen):
        self.mutex.acquire()
        self._waitRcvData()
        rdly = self.port.read(rdlen)
        if self.debug is True:
            print('<', len(rdly), rdly)
        self.mutex.release()

    def _waitRcvData(self):
        while self.port.in_waiting == 0:
#                print('Wait reply')
                time.sleep(0.1)

        
    def _updateLayoutForce(self, fade, duty):
        packet = self._createLayoutCommand()
        if packet == None:
            return

        self._writePacket(packet)
        self._recivePacket(6)

        # store current layout info
        self.ledMatrixBuf.copy(self.ledMatrix)
        

    def clearDisplay(self):
        self.ledMatrix = Matrix(200, 32) # clear
        self._updateLayoutForce(0, 100)
        self.refreshDisplay(0, 100)

    def getMuiID(self):
        pass

    def _createDisplayReqCommand(self, mode, fade, duty):
        buf = bytearray(8)
        sum = 0
        buf[0] = 0x00
        buf[1] = 0x06
        buf[2] = 0x00
        buf[3] = 0x03
        buf[4] = fade
        buf[5] = duty
        buf[6] = mode
        for i in range(2,7):
                sum = sum + buf[i]
        buf[7] = (sum & 0xFF)
        if self.debug is True:
            print('Sum:', buf[7])
        return buf


    def _createLayoutCommand(self):
        buf = bytearray(813)
        buf[0] = 0x03
        buf[1] = 0x2B
        buf[2] = 0x00
        buf[3] = 0x02
        buf[4] = 0		# x-pos
        buf[5] = 0
        buf[6] = 0		# y-pos
        buf[7] = 0
        buf[8] = 0		# width
        buf[9] = 200
        buf[10] = 0		# height
        buf[11] = 32		

        m = self.ledMatrix.matrix

        index = 0
        for y in range(32):
            for x in range(0, 200, 8):
                tmp = 0
                if m[y][x + 0] == 1:
                    tmp |= 0x80
                if m[y][x + 1] == 1:
                    tmp |= 0x40
                if m[y][x + 2] == 1:
                    tmp |= 0x20
                if m[y][x + 3] == 1:
                    tmp |= 0x10
                if m[y][x + 4] == 1:
                    tmp |= 0x08
                if m[y][x + 5] == 1:
                    tmp |= 0x04
                if m[y][x + 6] == 1:
                    tmp |= 0x02
                if m[y][x + 7] == 1:
                    tmp |= 0x01

                buf[12+index] = tmp
                index += 1

        sum = 0
        for i in range(2,812):
                sum = sum + buf[i]

        buf[812] = sum & 0xFF
        if self.debug is True:
            print('checksum' , buf[812] )
        return buf

    def _createLayoutCommandForDiff(self):

        posX = 0
        posY = 0
        w = 0
        h = 0
        dataLen = 0

        minX = 200
        maxX = -1
        minY = 32
        maxY = -1

        # mOld = self.ledMatrixBuf.matrix
        # mNew = self.ledMatrix.matrix

        #search data changed area
        # for y in range(32):
        #     for x in range(200):
        #         if (mOld[y][x] != mNew[y][x]):
        #             if x <= minX:
        #                 minX = x

        #             if x >= maxX:
        #                 maxX = x

        #             if y <= minY:
        #                 minY = y

        #             if y >= maxY:
        #                 maxY = y

        diffRange = check_diff_range(self.ledMatrixBuf.matrix, self.ledMatrix.matrix)
        minX = diffRange[0]
        maxX = diffRange[1]
        minY = diffRange[2]
        maxY = diffRange[3]
        if self.debug is True:
            print("minX {0}, maxX {1}, minY {2}, maxY {3}".format(minX, maxX, minY, maxY))


        # check change data is exist?
        if (maxX == -1) or (maxY == -1):
            # no data has changed
            if self.debug is True:
                print('-- no data has changed --')
            return

        # calc diff data area size and data size
        minX = (minX // 8) * 8
        maxX = ((maxX // 8) * 8) + 8
        if maxX > 200:
            maxX = 200

        maxY = maxY + 1
        if maxY > 32:
            maxY = 32

        posX = minX
        posY = minY
        w = maxX - minX
        h = maxY - minY
        dataLen = ((w // 8) * h) + 8
        if self.debug is True:
            print("data length {0}".format(dataLen))

        buf = bytearray(dataLen + 5)
        buf[0] = (( dataLen + 3) >> 8) & 0xFF
        buf[1] = (( dataLen + 3) & 0xFF )
        buf[2] = 0x00
        buf[3] = 0x02
        buf[4] = 0x00
        buf[5] = minX
        buf[6] = 0x00
        buf[7] = minY
        buf[8] = 0x00
        buf[9] = w
        buf[10] = 0x00
        buf[11] = h

        index = 0
        for y in range(minY, maxY, 1):
            for x in range(minX, maxX, 8):
                tmp = 0
                if self.ledMatrix.matrix[y][x + 0] == 1:
                    tmp |= 0x80
                if self.ledMatrix.matrix[y][x + 1] == 1:
                    tmp |= 0x40
                if self.ledMatrix.matrix[y][x + 2] == 1:
                    tmp |= 0x20
                if self.ledMatrix.matrix[y][x + 3] == 1:
                    tmp |= 0x10
                if self.ledMatrix.matrix[y][x + 4] == 1:
                    tmp |= 0x08
                if self.ledMatrix.matrix[y][x + 5] == 1:
                    tmp |= 0x04
                if self.ledMatrix.matrix[y][x + 6] == 1:
                    tmp |= 0x02
                if self.ledMatrix.matrix[y][x + 7] == 1:
                    tmp |= 0x01

                buf[12 + index] = tmp
                index += 1

        sum = 0
        for i in range(2, dataLen + 5):
                sum = sum + buf[i]
        buf[dataLen + 4] = (sum & 0xFF)
        return buf

    def toString(self):
        self.ledMatrix.toString()


# for TEST
if __name__ == '__main__':
    d=Display()
    d.turnOff(2)
    time.sleep(2)
    d.turnOn(2)

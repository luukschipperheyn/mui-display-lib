
# matrix class

import numpy as np

class Matrix:
    """
    LED Matrix information holder class
    """
    def __init__(self, w, h):
        self._startX = 0
        self._startY = 0
        self._width = w
        self._height = h
        self.matrix = np.asarray([[0] * w for i in range(h)], dtype='int8')

    @property
    def startX(self):
        return self._startX

    @property
    def startY(self):
        return self._startY

    @property
    def width(self):
        return self._width

    @property
    def height(self):
        return self._height

    @startX.setter
    def startX(self, startX):
        self._startX = startX

    @startY.setter
    def startY(self, startY):
        self._startY = startY
    
    def __str__(self):
        for h in range(self._height):
            print(self.matrix[h,:])


    def merge(self, b: 'Matrix'):
        if b == None:
            return

        bottom = self.startY + self.height
        right = self.startX + self.width

        bL = b.startX
        bT = b.startY
        bR = b.startX + b.width
        bB = b.startY + b.height

        for y in range(bottom):
            for x in range(right):
                if ((y >= bT) and (y < bB) and (x >= bL) and (x < bR)):
                    self.matrix[y - self.startY][x - self.startX] = b.matrix[y - bT][x - bL]
        


    def setStartX(self, x):
        self._startX = x

    def toString(self):
        for h in range(self._height):
            print(self.matrix[h,:])

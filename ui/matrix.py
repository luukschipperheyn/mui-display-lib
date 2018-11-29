
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
        self.matrix = np.asarray([[0] * w for i in range(h)])

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


    def setStartX(self, x):
        self._startX = x

    def toString(self):
        for h in range(self._height):
            print(self.matrix[h,:])

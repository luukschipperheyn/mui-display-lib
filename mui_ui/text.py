# -*- coding: utf-8 -*-

# mui ui text view class

import time
from enum import Enum

try:
    from parts import AbsParts
    from matrix import Matrix
    from muifont import MuiFont
except ImportError:
    from . import AbsParts
    from . import Matrix
    from . import MuiFont

LINE_OFFSET = (8+3)

class Border(Enum):
    NONE = 0
    BOTTOM = 1
    AROUND = 2

class TextAlignment(Enum):
    LEFT = 0
    CENTER = 1
    RIGHT = 2


class Text(AbsParts):
    """
    Text View

    this view convert text to Matrix data for mui UI drawing.
    when convert text, this view use the mui font.

    Examples
    ---------
    from mui_ui import Text, Border, TextAlignment, Widget, Display

    # create text view
    text = Text('hello world')
    text.setSize(0, 0, 100, 8) # set size and position. (x : 0, y : 0, width : 100, height : 8)

    # create UI base, full screen size
    ui = Widget(200, 32)

    # add text view to UI
    ui.addParts(text)

    # connect to display
    display = Display()

    # update UI
    def updateDisplay():
        # set layout to display
        display.setLayout(ui.getMatrix())
        display.updateLayout()

        # update display
        display.refreshDisplay()

    updateDisplay()

    # change text
    text.setText('hello ')

    # add Border to bottom of text
    text.setSize(0, 0, 100, 9) # please add 1dot for bottom border line.
    text.setBorder(Border.BOTTOM)
    updateDisplay()

    # text alignment to right
    text.setTextAlignment(TextAlignment.RIGHT)
    updateDisplay()

    # add text
    text.addText('mui')
    updateDisplay()

    # delte last char
    text.deleteLastChar()
    updateDisplay()


    Notes
    ------
    minimum height is 8dots. 
    if you'd like to set Border, please add 1 dot to height when use Border.BOTTOM and 
    add 4 dot both width and height when use Border.AROUND

    if you'd like to not replace all text but add text, you have to use addText() instead of setText().
    Because addText() is load matrix data of added text only, so it faster than use setText().

    text to be line fold automatically if it will over view area. but does not consider about hyphenation.

    See Also
    --------
    Border
    TextAlignment
    MuiFont

    """

    def __init__(self, text:str=None, border:Border=Border.NONE, name='textview'):
        super().__init__(name)
        self._text = text
        self._border = border
        self._textAlignment = TextAlignment.LEFT
        self._oldContent = None
        self._needRenderContent = True
        self._oldXOffset = 0
        self._oldYOffset = 0
        self._oldOrgXOffset = 0
        self._text_index = 0
        self._draw_out_area = False

    def setText(self, text:str, textAlignment:TextAlignment=None):
        if type(text) is not str:
            self._text = str(text)
        else:
            self._text = text

        if textAlignment is not None:
            self._textAlignment = textAlignment

        self._needRenderContent = True
        self._oldXOffset = 0
        self._oldYOffset = 0
        self._oldOrgXOffset = 0
        self._text_index = 0
        self._oldContent = None

    def addText(self, text: str):
        if self._text is None:
            self._text = ''

        self._text = self._text + text
        self._addTextMatrix(text)

    def deleteLastChar(self):
        if self._text is None:
            return

        newText = self._text[0:-1]
        self.setText(newText)


    def setTextAlignment(self, textAlignment:TextAlignment):
        self._textAlignment = textAlignment
        self._needRenderContent = True


    def setBorder(self, border:Border):
        self._border = border
        self._needRenderContent = True


    def _addTextMatrix(self, text: str):
        font = MuiFont.get_instance()

        yOffset = self._oldYOffset
        xOffset = self._oldXOffset
        xOffsetOrg = self._oldOrgXOffset
        isOverArea = False

        m = self._oldContent
        if m is None:
            m = Matrix(self.width, self.height)
            m.startX = self.x
            m.startY = self.y

        for s in text:                
            if s == '\n':
                yOffset += LINE_OFFSET
                xOffset = xOffsetOrg

                if ((yOffset + 8) > (self.y + self.height)):
                    isOverArea = True
            else:
                textM = font.getText(s)
                textM.startX = self.x + xOffset
                textM.startY = self.y + yOffset

                if ((textM.startX + textM.width) > (self.x + self.width)):
                    xOffset = 0
                    yOffset += LINE_OFFSET

                    textM.startX = self.x + xOffset
                    textM.startY = self.y + yOffset

                # merge char matrix data to area matrix
                m.merge(textM)

                xOffset += textM.width

            # check text is out from this view area
            if (isOverArea or (((xOffset + 8) > self.width) and ((yOffset + LINE_OFFSET) > self.height))):
                # notify text if out from view area
                self._onTextFull(self._text_index)

            self._text_index += 1

        self._oldXOffset = xOffset
        self._oldYOffset = yOffset


    def getMatrix(self):
        """
        Return Matrix data for display draw
        """
        #sT = time.time()

        text = self._text
        if text is None:
            return None

        if (self._oldContent is not None) and (self._needRenderContent is False):
            self._oldContent.startX = self.x
            self._oldContent.startY = self.y
            return self._oldContent

        # m = Matrix(self.width, self.height)
        # m.startX = self.x
        # m.startY = self.y

        xOffset = 0
        xOffsetOrg = 0
        yOffset = 0

        font = MuiFont.get_instance()

        maxX = 0
        xOffset = yOffset = 2 if self._border == Border.AROUND else 0

        tH = self.getTextHeight(font, self._text)
        if self._textAlignment == TextAlignment.CENTER:
            tW = self.getTextWidth(font, self._text)
            dX = self.width - tW
            xOffset = dX // 2
            xOffset += 1 if self._border == Border.AROUND else 0

            # tH = self.getTextHeight(font, self._text)
            dY = self.height - tH
            yOffset = dY // 2
        elif self._textAlignment == TextAlignment.RIGHT: 
            tW = self.getTextWidth(font, self._text)
            dX = self.width - tW
            dX -= 1 if self._border == Border.AROUND else 0
            xOffset = dX

        m = Matrix(self.width, tH if self._draw_out_area else self.height)
        m.startX = self.x
        m.startY = self.y

        xOffsetOrg = xOffset
        isOverArea = False

        # draw text
        self._text_index = 0
        call_text_full = False
        for s in text:                
            if s == '\n':
                yOffset += LINE_OFFSET
                xOffset = xOffsetOrg

                if ((yOffset + 8) > (self.y + self.height)):
                    isOverArea = True
            else:
                textM = font.getText(s)
                textM.startX = self.x + xOffset
                textM.startY = self.y + yOffset

                if ((textM.startX + textM.width) > (self.x + self.width)):
                    xOffset = 0
                    yOffset += LINE_OFFSET

                    textM.startX = self.x + xOffset
                    textM.startY = self.y + yOffset

                # merge char matrix data to area matrix
                m.merge(textM)

                xOffset += textM.width
                if maxX < xOffset:
                    maxX = xOffset

            # check text is out from this view area
            if (isOverArea or (((xOffset + 8) > self.width) and ((yOffset + LINE_OFFSET) > self.height))):
                # notify text if out from view area
                if call_text_full is False:
                    self._onTextFull(self._text_index)
                    call_text_full = True

            self._text_index += 1

        # write border
        if self._border == Border.BOTTOM:
            bYOffset = yOffset + 8
            if m.height > 8:
                for i in range(maxX):
                    m.matrix[bYOffset][i] = 1

        elif self._border == Border.AROUND:
            bMaxX = maxX + 2
            if self._textAlignment == TextAlignment.CENTER:
                bMaxX = self.width

            for i in range(bMaxX):
                m.matrix[0][i] = 1
                m.matrix[self.height-1][i] = 1

            for i in range(self.height - 1):
                m.matrix[i][0] = 1
                m.matrix[i][bMaxX - 1] = 1

        #eR = time.time() - sT
        #print("render text time : {0}".format(eR))

        self._oldContent = m
        self._needRenderContent = False
        self._oldXOffset = xOffset
        self._oldYOffset = yOffset
        self._oldOrgXOffset = xOffsetOrg

        return m


    def getTextWidth(self, font, text):
        """
        calcurate text width
        """
        textMaxWidth = 0
        textWidth = 0
        for s in text:
            if (s == '\n'):
                textWidth = 0
            else:
                tM = font.getText(s)
                tM.startX = self.x + textWidth

                if ((tM.startX + tM.width) > (self.x + self.width)):
                    textWidth = 0
                else:
                    textWidth += tM.width

            if textMaxWidth < textWidth:
                textMaxWidth = textWidth
        
        return textMaxWidth


    def getTextHeight(self, font, text):
        """
        calcurate text height
        """
        textWidth = 0
        textHeight = 8

        for s in text:
            if (s == '\n'):
                textHeight += LINE_OFFSET
                textWidth = 0
            else:
                tM = font.getText(s)
                tM.startX = self.x + textWidth

                if ((tM.startX + tM.width) > (self.x + self.width)):
                    textHeight += LINE_OFFSET
                    textWidth = 0

                textWidth += tM.width
        
        return textHeight

    def _onTextFull(self, text_index):
        pass



# for test
if __name__ == '__main__':
    print('call text.py')
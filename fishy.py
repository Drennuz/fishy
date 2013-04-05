import sys
import random
from PyQt4 import QtCore, QtGui, QtTest

class Fishy(QtGui.QMainWindow):
    Height = 600
    Width = 600
    
    def __init__(self):
        QtGui.QMainWindow.__init__(self)

        self.resize(Fishy.Width, Fishy.Height)
        self.setWindowTitle("Fishy game")
        self.fishyboard = Board(self)

        self.setCentralWidget(self.fishyboard)

        self.statusbar = self.statusBar()
        self.connect(self.fishyboard, QtCore.SIGNAL('messageToStatusbar(QString)'), self.statusbar, QtCore.SLOT('showMessage(QString)'))
        self.connect(self.fishyboard, QtCore.SIGNAL('closeApp'), self.close)

        self.center()

    def center(self):
        qr = self.frameGeometry()
        cp = QtGui.QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

class Board(QtGui.QFrame):
    BoardWidth = 20
    BoardHeight = 20
    Pieces = 4 #moving objects
    Margin = 5
    UP = 1
    DOWN = 2
    LEFT = 3
    RIGHT = 4

    def __init__(self, parent):
        QtGui.QFrame.__init__(self, parent)

        self.board = []
        self.piece_pos = [(None, None)] * (Board.Pieces+1) #last position stores hunter
        self.alive = Board.Pieces 
        self.steps = 0 #counter
        
        self.initiate_board()

        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def shapeAt(self, x, y):
        return self.board[(y * Board.BoardWidth) + x]

    def setShapeAt(self, x, y, shape):
        self.board[(y * Board.BoardWidth) + x] = shape
    
    def squareWidth(self):
        return self.contentsRect().width() / Board.BoardWidth

    def squareHeight(self):
        return self.contentsRect().height() / Board.BoardHeight

    def replaceShape(self, x, y, i, val): #only change part of the tuple (dir, has_fish, has_hunter)
        atuple = self.shapeAt(x,y)
        b = list(atuple)
        b[i] = val
        self.setShapeAt(x,y,tuple(b))
    
    def demo(self, path): 
        '''
        demo function: take a list of steps and demonstrate 
        '''
        upperbound = 50
         
        for i in range(upperbound):
            nextDir = path()
            QtTest.QTest.qWait(300)
            self.nextMove(nextDir)
    
    def greedy(self):
        '''
        return direction
        '''
        (x0, y0) = self.piece_pos[Board.Pieces]
        min_dis = Board.BoardWidth ** 2 + Board.BoardHeight **2 + 1
        (x_min, y_min) = (x0, y0)

        for (x,y) in self.livingFish():
            dist = (x - x0) ** 2 + (y - y0) ** 2
            if dist < min_dis:
                min_dis = dist
                (x_min, y_min) = (x,y)

        if abs(x_min - x0) >= abs(y_min - y0):
            return Board.RIGHT if x_min >= x0 else Board.LEFT
        else:
            return Board.DOWN if y_min >= y0 else Board.UP

    def random_path(self):
        return random.randrange(4)

    def livingFish(self):
        results = []
        for i in range(Board.Pieces):
            (x,y) = self.piece_pos[i]
            if self.shapeAt(x,y)[1]:
                results.append((x,y))
        return results
    
    def keyPressEvent(self, event):
        key = event.key()
        
        if key == QtCore.Qt.Key_D:
            self.demo(self.greedy)
            return None

        if key == QtCore.Qt.Key_Q:
            self.emit(QtCore.SIGNAL('closeApp'))
            return None
        
        if key == QtCore.Qt.Key_Left:
            self.nextMove(Board.LEFT)
        elif key == QtCore.Qt.Key_Right:
            self.nextMove(Board.RIGHT)
        elif key == QtCore.Qt.Key_Up:
            self.nextMove(Board.UP)
        elif key == QtCore.Qt.Key_Down:
            self.nextMove(Board.DOWN) 
    
    def nextMove(self, direction):
        #update hunters
        (hunt_x, hunt_y) = self.piece_pos[Board.Pieces] #hunter always at end
        (new_hunt_x, new_hunt_y) = (hunt_x, hunt_y)
        #take care of borders 
        x_left = max(0, hunt_x-1)
        x_right = min(Board.BoardWidth-1, hunt_x+1)
        y_up = max(0, hunt_y-1)
        y_dn = min(Board.BoardHeight-1, hunt_y+1)

        if direction == Board.LEFT: 
            new_hunt_x = x_left
        elif direction == Board.RIGHT: 
            new_hunt_x = x_right
        elif direction == Board.UP: 
            new_hunt_y = y_up 
        elif direction == Board.DOWN:
            new_hunt_y = y_dn
        self.tryMoveHunter(hunt_x, hunt_y, new_hunt_x, new_hunt_y)

        #update fishes
        for i in range(Board.Pieces):
            (x,y) = self.piece_pos[i]
            if self.shapeAt(x,y)[1]: #is marked as fish
                (new_fish_x, new_fish_y) = self.fishNext(x,y) #next destined move
                if ((new_hunt_x, new_hunt_y) == (new_fish_x, new_fish_y)) or \
                (((hunt_x - x)*(new_hunt_x - new_fish_x) == -1) and (new_hunt_y == new_fish_y)) or \
                (((hunt_y - y)*(new_hunt_y - new_fish_y) == -1) and (new_hunt_x == new_fish_x)): #bang!
                    self.alive -= 1
                    self.replaceShape(x, y, 1, False) #set has_fish to False
                    if self.alive == 0: #finish, display final message
                        self.winning()
                elif self.shapeAt(new_fish_x, new_fish_y)[1]: #two fishes crash
                    self.alive -= 1
                else:
                    self.tryMoveFish(x,y,i)

        self.update()

    def winning(self):
        reply = QtGui.QMessageBox.information(self, 'All caught!', 'Congratulations! You took %d steps' % self.steps, QtGui.QMessageBox.Ok, QtGui.QMessageBox.Ok)
        self.emit(QtCore.SIGNAL('closeApp'))
        self.close()

    def tryMoveHunter(self, old_x, old_y, new_x, new_y):
        self.replaceShape(old_x, old_y, 2, False) #update old cell
        self.replaceShape(new_x, new_y, 2, True) #new cell
        self.piece_pos[Board.Pieces] = (new_x,new_y) #update hunter position
        self.steps += 1
        self.emit(QtCore.SIGNAL('messageToStatusbar(QString)'), 'press q to exit; press d for demo; %d steps taken' % self.steps)

    def tryMoveFish(self, x, y, i):
        (new_x, new_y) = self.fishNext(x,y)
        self.replaceShape(x, y, 1, False)
        self.replaceShape(new_x, new_y, 1, True)
        self.piece_pos[i] = (new_x,new_y)

    def fishNext(self,x,y):
        x_left = max(0,x-1)
        x_right = min(Board.BoardWidth-1, x+1)
        y_up = max(0, y-1)
        y_dn = min(Board.BoardHeight-1, y+1)

        direction = self.shapeAt(x,y)[0]#current dir

        if direction == Board.UP: 
            return (x,y_up)
        elif direction == Board.DOWN: 
            return (x,y_dn)
        elif direction == Board.LEFT: 
            return (x_left,y)
        elif direction == Board.RIGHT: 
            return (x_right,y)
         
    
    def paintEvent(self, event):
        w = self.squareWidth()
        h = self.squareHeight()
        
        qp = QtGui.QPainter()
        qp.begin(self)
        
        #draw grids
        for y in range(1, Board.BoardHeight):
            qp.drawLine(0, y*h, w*Board.BoardWidth, y*h) #(x_0, y_0, x_1, y_1); horizontal line
        for x in range(1, Board.BoardWidth):
            qp.drawLine(x*w, 0, x*w, Board.BoardHeight*h)
        
        #draw shape matrix
        for x in range(Board.BoardWidth):
            for y in range(Board.BoardHeight):
                self.drawShape(qp, x, y, self.shapeAt(x,y))
        qp.end()
    
    def initiate_board(self):
        '''
        return initiate shape matrix of (arrow, has_fish, has_hunter)
        '''
        W = Board.BoardWidth
        H = Board.BoardHeight
        
        mat = [(0, False, False)] * (H*W) #(dir, has_fish, has_hunter)
        
        def drawEdge(x,y,w,h,clockwise):
            if clockwise == 1:
                for i in range(x, x+w-1):
                    mat[i+y*W] = (4, False, False) if not mat[i+y*W][1] else mat[i+y*W]
                for j in range(y, y+h-1):
                    mat[x+w-1+j*W] = (2, False, False) if not mat[x+w-1+j*W][1] else mat[x+w-1+j*W]
                for i in range(x+1, x+w):
                    mat[i+(y+h-1)*W] = (3, False, False) if not mat[i+(y+h-1)*W][1] else mat[i+(y+h-1)*W]
                for j in range(y+1, y+h):
                    mat[x+j*W] = (1, False, False) if not mat[x+j*W][1] else mat[x+j*W]
            else:
                for i in range(x+1, x+w):
                    mat[i+y*W] = (3, False, False) if not mat[i+y*W][1] else mat[i+y*W]
                for j in range(y+1, y+h):
                    mat[x+w-1+j*W] = (1, False, False) if not mat[x+w-1+j*W][1] else mat[x+w-1+j*W]
                for i in range(x, x+w-1):
                    mat[i+(y+h-1)*W] = (4, False, False) if not mat[i+(y+h-1)*W][1] else mat[i+(y+h-1)*W]
                for j in range(y, y+h-1):
                    mat[x+j*W] = (2, False, False) if not mat[x+j*W][1] else mat[x+j*W]

        #fishes
        for k in range(Board.Pieces):
            (x,y) = (random.randrange(1,W-1), random.randrange(1,H-1)) 
            self.piece_pos[k] = (x,y)
            #determine direction
            region = random.randrange(4)
            if region == 0:
                cw = random.choice([0,1])
                w = random.randrange(2,x+2)
                h = random.randrange(2,y+2)
                drawEdge(x-w+1,y-h+1,w,h,cw)
                if cw == 1:
                    mat[x+y*W] = (3,True,False)
                else:
                    mat[x+y*W] = (1, True, False)
            elif region == 1:
                cw = random.choice([0,1])
                w = random.randrange(2,W+1-x)
                h = random.randrange(2,y+2)
                drawEdge(x,y-h+1,w,h,cw)
                if cw == 1:
                    mat[x+y*W] = (1,True,False)
                else:
                    mat[x+y*W] = (4, True, False)
            elif region == 2:
                cw = random.choice([0,1])
                w = random.randrange(2,x+2)
                h = random.randrange(2,H+1-y)
                drawEdge(x-w+1,y,w,h,cw)
                if cw == 1:
                    mat[x+y*W] = (2,True,False)
                else:
                    mat[x+y*W] = (3, True, False)
            elif region == 3:
                cw = random.choice([0,1])
                w = random.randrange(2,W+1-x)
                h = random.randrange(2,H+1-y)
                drawEdge(x,y,w,h,cw)
                if cw == 1:
                    mat[x+y*W] = (4,True,False)
                else:
                    mat[x+y*W] = (2, True, False)

        
        #hunter
        (x,y) = (random.randrange(W), random.randrange(H))
        self.piece_pos[self.alive] = (x,y)
        mat[x+y*W] = (0, False, True)
        self.board = mat

    def drawShape(self, painter, x, y, shape):
        w = self.squareWidth()
        h = self.squareHeight()
        m = Board.Margin
        
        if shape[0] == Board.UP: #up arrow
            position = [(0.25, 0.75), (0.5, 0.25), (0.75, 0.75)]
        elif shape[0] == Board.DOWN: #down arrow
            position = [(0.25, 0.25), (0.5, 0.75), (0.75, 0.25)]
        elif shape[0] == Board.LEFT: #left arrow
            position = [(0.75, 0.25), (0.25, 0.5), (0.75, 0.75)]
        elif shape[0] == Board.RIGHT: #right arrow
            position = [(0.25, 0.25), (0.75, 0.5), (0.25, 0.75)]

        if shape[0] != 0:
            painter.setPen(QtCore.Qt.black)
            painter.drawLine(x*w + position[0][0]*w, y*h + position[0][1]*h, x*w + position[1][0]*w, y*h + position[1][1]*h)
            painter.drawLine(x*w + position[1][0]*w, y*h + position[1][1]*h, x*w + position[2][0]*w, y*h + position[2][1]*h)
        
        if shape[2]: #has_hunter --> draw circle
            painter.setBrush(QtCore.Qt.red)
            painter.drawEllipse(x*w+0.5*m, y*h+0.5*m, w-m, h-m)
        elif shape[1] and shape[0] == Board.UP: #has_fish --> hunder has priority over fish
            painter.setPen(QtCore.Qt.blue)
            painter.drawLine(x*w + 0.25*w -m, y*h + 0.75*h + m, x*w + 0.5*w, y*h + 0.25*h - m)
            painter.drawLine(x*w + 0.5*w, y*h + 0.25*h - m, x*w + 0.75*w + m, y*h + 0.75*h + m)
            painter.drawLine(x*w + 0.75*w + m, y*h + 0.75*h + m, x*w + 0.25*w - m, y*h + 0.75*h + m)
        elif shape[1] and shape[0] == Board.DOWN: #has_fish --> down arrow
            painter.setPen(QtCore.Qt.blue)
            painter.drawLine(x*w + 0.25*w -m, y*h + 0.25*h - m, x*w + 0.5*w, y*h + 0.75*h + m)
            painter.drawLine(x*w + 0.5*w, y*h + 0.75*h + m, x*w + 0.75*w + m, y*h + 0.25*h - m)
            painter.drawLine(x*w + 0.75*w + m, y*h + 0.25*h - m, x*w + 0.25*w - m, y*h + 0.25*h - m)
        elif shape[1] and shape[0] == Board.LEFT: #has_fish --> left arrow
            painter.setPen(QtCore.Qt.blue)
            painter.drawLine(x*w + 0.25*w -m, y*h + 0.5*h, x*w + 0.75*w + m, y*h + 0.25*h - m)
            painter.drawLine(x*w + 0.75*w + m, y*h + 0.25*h - m, x*w + 0.75*w + m, y*h + 0.75*h + m)
            painter.drawLine(x*w + 0.75*w + m, y*h + 0.75*h + m, x*w + 0.25*w - m, y*h + 0.5*h)
        elif shape[1] and shape[0] == Board.RIGHT: #has_fish --> right arrow
            painter.setPen(QtCore.Qt.blue)
            painter.drawLine(x*w + 0.25*w -m, y*h + 0.25*h - m, x*w + 0.75*w + m, y*h + 0.5*h)
            painter.drawLine(x*w + 0.75*w + m, y*h + 0.5*h, x*w + 0.25*w - m, y*h + 0.75*h + m)
            painter.drawLine(x*w + 0.25*w - m, y*h + 0.75*h + m, x*w + 0.25*w - m, y*h + 0.25*h - m)

class Arrows(object):
    NoShape = 0
    Up = Board.UP
    Down = Board.DOWN
    Left = Board.LEFT
    Right = Board.RIGHT

class Shape(object):
    #(arrow, has_fish, has_hunter)
    def __init__(self):
        self.pieceShape = (Arrows.NoShape, False, False)
        selt.setShape(Arrows.NoShape, False, False)

    def shape(self):
        return self.pieceShape

    def setShape(self, arrow, has_fish, has_hunter):
        self.pieceShape = (arrow, has_fish, has_hunter)

def main():
    app = QtGui.QApplication(sys.argv)
    fishy = Fishy()
    fishy.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    main()

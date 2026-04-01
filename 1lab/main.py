from copy import deepcopy

WHITE = "white"
BLACK = "black"

letters = "abcdefgh"


def parse_pos(pos):
    return 8 - int(pos[1]), letters.index(pos[0])


def to_notation(pos):
    return letters[pos[1]] + str(8 - pos[0])


class Piece:
    def __init__(self, color):
        self.color = color
        self.moved = False

    def enemy(self, other):
        return other and other.color != self.color

    def moves_in_directions(self, board, pos, dirs):
        moves = []
        x, y = pos
        for dx, dy in dirs:
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                t = board.get(nx, ny)
                if t is None:
                    moves.append((nx, ny))
                elif self.enemy(t):
                    moves.append((nx, ny))
                    break
                else:
                    break
                nx += dx
                ny += dy
        return moves


class Pawn(Piece):
    def get_moves(self, board, pos, for_attack=False):
        moves = []
        x, y = pos
        d = -1 if self.color == WHITE else 1

        if not for_attack:
            if board.get(x + d, y) is None:
                moves.append((x + d, y))
                if not self.moved and board.get(x + 2 * d, y) is None:
                    moves.append((x + 2 * d, y))

        for dy in [-1, 1]:
            nx, ny = x + d, y + dy
            if 0 <= ny < 8:
                if for_attack or self.enemy(board.get(nx, ny)):
                    moves.append((nx, ny))

        return moves

    def __repr__(self):
        return "♙" if self.color == WHITE else "♟"


class Rook(Piece):
    def get_moves(self, b, p, for_attack=False):
        return self.moves_in_directions(b, p, [(1,0),(-1,0),(0,1),(0,-1)])
    def __repr__(self): return "♖" if self.color == WHITE else "♜"


class Bishop(Piece):
    def get_moves(self, b, p, for_attack=False):
        return self.moves_in_directions(b, p, [(1,1),(-1,-1),(1,-1),(-1,1)])
    def __repr__(self): return "♗" if self.color == WHITE else "♝"


class Queen(Piece):
    def get_moves(self, b, p, for_attack=False):
        return self.moves_in_directions(b, p,
            [(1,0),(-1,0),(0,1),(0,-1),(1,1),(-1,-1),(1,-1),(-1,1)])
    def __repr__(self): return "♕" if self.color == WHITE else "♛"


class Knight(Piece):
    def get_moves(self, b, p, for_attack=False):
        moves=[]
        x,y=p
        for dx,dy in [(2,1),(2,-1),(-2,1),(-2,-1),(1,2),(1,-2),(-1,2),(-1,-2)]:
            nx,ny=x+dx,y+dy
            if 0<=nx<8 and 0<=ny<8:
                t=b.get(nx,ny)
                if t is None or self.enemy(t):
                    moves.append((nx,ny))
        return moves
    def __repr__(self): return "♘" if self.color == WHITE else "♞"


class King(Piece):
    def get_moves(self, b, p, for_attack=False):
        moves=[]
        x,y=p

        for dx in [-1,0,1]:
            for dy in [-1,0,1]:
                if dx==0 and dy==0: continue
                nx,ny=x+dx,y+dy
                if 0<=nx<8 and 0<=ny<8:
                    t=b.get(nx,ny)
                    if t is None or self.enemy(t):
                        moves.append((nx,ny))

        if for_attack:
            return moves

        if not self.moved and not b.is_check(self.color):
            row = x

            rook = b.get(row,7)
            if isinstance(rook,Rook) and not rook.moved:
                if all(b.get(row,c) is None for c in [5,6]):
                    moves.append((row,6))

            rook = b.get(row,0)
            if isinstance(rook,Rook) and not rook.moved:
                if all(b.get(row,c) is None for c in [1,2,3]):
                    moves.append((row,2))

        return moves

    def __repr__(self): return "♔" if self.color == WHITE else "♚"


class Board:
    def __init__(self):
        self.grid=[[None]*8 for _ in range(8)]
        self.history=[]
        self.setup()

    def setup(self):
        for i in range(8):
            self.grid[6][i]=Pawn(WHITE)
            self.grid[1][i]=Pawn(BLACK)

        self.grid[7]=[Rook(WHITE),Knight(WHITE),Bishop(WHITE),Queen(WHITE),
                      King(WHITE),Bishop(WHITE),Knight(WHITE),Rook(WHITE)]
        self.grid[0]=[Rook(BLACK),Knight(BLACK),Bishop(BLACK),Queen(BLACK),
                      King(BLACK),Bishop(BLACK),Knight(BLACK),Rook(BLACK)]

    def get(self,x,y):
        if 0<=x<8 and 0<=y<8:
            return self.grid[x][y]
        return None

    def find_king(self,color):
        for i in range(8):
            for j in range(8):
                p=self.grid[i][j]
                if isinstance(p,King) and p.color==color:
                    return (i,j)

    def is_check(self,color):
        king_pos=self.find_king(color)
        for i in range(8):
            for j in range(8):
                p=self.grid[i][j]
                if p and p.color!=color:
                    if king_pos in p.get_moves(self,(i,j),True):
                        return True
        return False

    def move(self,start,end):
        piece=self.get(*start)
        self.history.append(deepcopy(self.grid))

        if isinstance(piece, King) and abs(end[1]-start[1])==2:
            if end[1]==6:
                rook=self.get(start[0],7)
                self.grid[start[0]][5]=rook
                self.grid[start[0]][7]=None
                rook.moved=True
            else:
                rook=self.get(start[0],0)
                self.grid[start[0]][3]=rook
                self.grid[start[0]][0]=None
                rook.moved=True

        self.grid[end[0]][end[1]]=piece
        self.grid[start[0]][start[1]]=None
        piece.moved=True

        if isinstance(piece,Pawn):
            if (piece.color==WHITE and end[0]==0) or \
               (piece.color==BLACK and end[0]==7):
                self.grid[end[0]][end[1]]=Queen(piece.color)

    def undo(self):
        if self.history:
            self.grid=self.history.pop()

    def print(self):
        print("  a b c d e f g h")
        for i,row in enumerate(self.grid):
            print(8-i," ".join(str(p) if p else "." for p in row))
        print()


class Game:
    def __init__(self):
        self.board=Board()
        self.turn=WHITE

    def legal_moves(self,pos):
        piece=self.board.get(*pos)
        if not piece or piece.color!=self.turn:
            return []

        moves=[]
        for m in piece.get_moves(self.board,pos):
            copy=deepcopy(self.board)
            copy.move(pos,m)
            if not copy.is_check(self.turn):
                moves.append(m)
        return moves

    def has_moves(self):
        for i in range(8):
            for j in range(8):
                if self.legal_moves((i,j)):
                    return True
        return False

    def play(self):
        while True:
            self.board.print()

            if self.board.is_check(self.turn):
                print("ШАХ!")

            if not self.has_moves():
                if self.board.is_check(self.turn):
                    print("МАТ!")
                else:
                    print("ПАТ!")
                break

            print(f"Ход: {'Белые' if self.turn==WHITE else 'Чёрные'}")
            cmd=input("Введите ход (e2 e4) или 'откат': ")

            if cmd=="откат":
                self.board.undo()
                self.turn=BLACK if self.turn==WHITE else WHITE
                continue

            try:
                s,e=cmd.split()
                x1,y1=parse_pos(s)
                x2,y2=parse_pos(e)
            except:
                print("Ошибка ввода")
                continue

            moves=self.legal_moves((x1,y1))
            print("Возможные ходы:", [to_notation(m) for m in moves])

            if (x2,y2) in moves:
                self.board.move((x1,y1),(x2,y2))
                self.turn=BLACK if self.turn==WHITE else WHITE
            else:
                print("Недопустимый ход")


if __name__=="__main__":
    Game().play()
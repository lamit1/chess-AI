import chess
import chess.svg
import chess.polyglot
import time
import traceback
import chess.pgn
import chess.engine
from flask import Flask, Response, request
import webbrowser
import pyttsx3


# Các bảng đánh giá vị trí từng loại quân
pawntable = [
    0, 0, 0, 0, 0, 0, 0, 0,
    5, 10, 10, -20, -20, 10, 10, 5,
    5, -5, -10, 0, 0, -10, -5, 5,
    0, 0, 0, 20, 20, 0, 0, 0,
    5, 5, 10, 25, 25, 10, 5, 5,
    10, 10, 20, 30, 30, 20, 10, 10,
    50, 50, 50, 50, 50, 50, 50, 50,
    0, 0, 0, 0, 0, 0, 0, 0]

knightstable = [
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20, 0, 5, 5, 0, -20, -40,
    -30, 5, 10, 15, 15, 10, 5, -30,
    -30, 0, 15, 20, 20, 15, 0, -30,
    -30, 5, 15, 20, 20, 15, 5, -30,
    -30, 0, 10, 15, 15, 10, 0, -30,
    -40, -20, 0, 0, 0, 0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50]

bishopstable = [
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10, 5, 0, 0, 0, 0, 5, -10,
    -10, 10, 10, 10, 10, 10, 10, -10,
    -10, 0, 10, 10, 10, 10, 0, -10,
    -10, 5, 5, 10, 10, 5, 5, -10,
    -10, 0, 5, 10, 10, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -10, -10, -10, -10, -20]

rookstable = [
    0, 0, 0, 5, 5, 0, 0, 0,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    -5, 0, 0, 0, 0, 0, 0, -5,
    5, 10, 10, 10, 10, 10, 10, 5,
    0, 0, 0, 0, 0, 0, 0, 0]

queenstable = [
    -20, -10, -10, -5, -5, -10, -10, -20,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -10, 5, 5, 5, 5, 5, 0, -10,
    0, 0, 5, 5, 5, 5, 0, -5,
    -5, 0, 5, 5, 5, 5, 0, -5,
    -10, 0, 5, 5, 5, 5, 0, -10,
    -10, 0, 0, 0, 0, 0, 0, -10,
    -20, -10, -10, -5, -5, -10, -10, -20]

kingstable = [
    20, 30, 10, 0, 0, 10, 30, 20,
    20, 20, 0, 0, 0, 0, 20, 20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30]

#Hàm đánh giá bàn cờ
def evaluate_board():
    #Nếu chiếu tướng
    if board.is_checkmate():
        if board.turn:
            return -9999
        else:
            return 9999
    #Nếu hòa
    if board.is_stalemate():
        return 0
    #Nếu không đủ quân để chiếu tướng
    if board.is_insufficient_material():
        return 0
    #Số lượng từng loại quân 2 bên
    wp = len(board.pieces(chess.PAWN, chess.WHITE))
    bp = len(board.pieces(chess.PAWN, chess.BLACK))
    wn = len(board.pieces(chess.KNIGHT, chess.WHITE))
    bn = len(board.pieces(chess.KNIGHT, chess.BLACK))
    wb = len(board.pieces(chess.BISHOP, chess.WHITE))
    bb = len(board.pieces(chess.BISHOP, chess.BLACK))
    wr = len(board.pieces(chess.ROOK, chess.WHITE))
    br = len(board.pieces(chess.ROOK, chess.BLACK))
    wq = len(board.pieces(chess.QUEEN, chess.WHITE))
    bq = len(board.pieces(chess.QUEEN, chess.BLACK))

    # Khởi tạo giá trị đánh và các yếu tố khác như số quân được bảo vệ và số tốt thông
    material_value = 0
    protected_pieces = 0
    protected_pieces = 0
    passed_pawns = 0
    passed_pawns = 0

    # Tính số quân bị tấn công và số quân tốt thông
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece is not None:
            if piece.color:
                if board.is_attacked_by(chess.BLACK, square):
                    protected_pieces -= 1
                if piece.piece_type == chess.PAWN and not board.attacks(square):
                    passed_pawns -= 1
            else:
                if board.is_attacked_by(chess.WHITE, square):
                    protected_pieces += 1
                if piece.piece_type == chess.PAWN and not board.attacks(square):
                    passed_pawns += 1


    #Đánh giá về chất lượng và số lượng loại quân giữa 2 bên
    material_value += 100 * (wp - bp) + 320 * (wn - bn) + 330 * (wb - bb) + 500 * (wr - br) + 900 * (wq - bq)
    + protected_pieces * 15 + passed_pawns * 30
    #Đánh giá về vị trí của của từng loại quân
    pawnsq = sum([pawntable[i] for i in board.pieces(chess.PAWN, chess.WHITE)])
    pawnsq = pawnsq + sum([-pawntable[chess.square_mirror(i)]
                           for i in board.pieces(chess.PAWN, chess.BLACK)])
    knightsq = sum([knightstable[i] for i in board.pieces(chess.KNIGHT, chess.WHITE)])
    knightsq = knightsq + sum([-knightstable[chess.square_mirror(i)]
                               for i in board.pieces(chess.KNIGHT, chess.BLACK)])
    bishopsq = sum([bishopstable[i] for i in board.pieces(chess.BISHOP, chess.WHITE)])
    bishopsq = bishopsq + sum([-bishopstable[chess.square_mirror(i)]
                               for i in board.pieces(chess.BISHOP, chess.BLACK)])
    rooksq = sum([rookstable[i] for i in board.pieces(chess.ROOK, chess.WHITE)])
    rooksq = rooksq + sum([-rookstable[chess.square_mirror(i)]
                           for i in board.pieces(chess.ROOK, chess.BLACK)])
    queensq = sum([queenstable[i] for i in board.pieces(chess.QUEEN, chess.WHITE)])
    queensq = queensq + sum([-queenstable[chess.square_mirror(i)]
                             for i in board.pieces(chess.QUEEN, chess.BLACK)])
    kingsq = sum([kingstable[i] for i in board.pieces(chess.KING, chess.WHITE)])
    kingsq = kingsq + sum([-kingstable[chess.square_mirror(i)]
                           for i in board.pieces(chess.KING, chess.BLACK)])
    #Tổng thành phần đánh giá của chất lượng, số lượng và vị trí và các yếu tố khác
    eval = material_value + pawnsq + knightsq + bishopsq + rooksq + queensq + kingsq
    print(passed_pawns, protected_pieces)
    if board.turn:
        return eval
    else:
        return -eval


# Tìm kiếm nước đi tốt nhất sử dụng alpha-beta
def alphabeta(alpha, beta, depthleft):
    bestscore = -9999
    if (depthleft == 0):
        return quiesce(alpha, beta)
    for move in board.legal_moves:
        board.push(move)
        score = -alphabeta(-beta, -alpha, depthleft - 1)
        board.pop()
        if (score >= beta):
            return score
        if (score > bestscore):
            bestscore = score
        if (score > alpha):
            alpha = score
    return bestscore


def quiesce(alpha, beta):
    stand_pat = evaluate_board()
    if (stand_pat >= beta):
        return beta
    if (alpha < stand_pat):
        alpha = stand_pat

    for move in board.legal_moves:
        if board.is_capture(move):
            board.push(move)
            score = -quiesce(-beta, -alpha)
            board.pop()

            if (score >= beta):
                return beta
            if (score > alpha):
                alpha = score
    return alpha

# Hàm giúp máy tìm kiếm nước đi.
# Nếu nước đi nằm trong opening book thì sẽ đi, nếu không sẽ sử dụng hàm đánh giá và alpha-beta
def selectmove(depth):
    try:
        move = chess.polyglot.MemoryMappedReader("C:/Users/your_path/opening.bin").weighted_choice(board).move
        return move
    except:
        bestMove = chess.Move.null()
        bestValue = -99999
        alpha = -100000
        beta = 100000
        for move in board.legal_moves:
            board.push(move)
            boardValue = -alphabeta(-beta, -alpha, depth - 1)
            if boardValue > bestValue:
                bestValue = boardValue
                bestMove = move
            if (boardValue > alpha):
                alpha = boardValue
            board.pop()
        return bestMove




# Hàm di chuyển với độ sâu là 3
def devmove():
    move = selectmove(3)
    board.push(move)


app = Flask(__name__)


# Giao diện với Flask
@app.route("/")
def main():
    global count, board
    if count == 1:
        count += 1
    ret = '<html><head>'
    ret += '<style>input {font-size: 20px; } button { font-size: 20px;} p {font-size: 20px} * { margin:5px } </style>'
    ret += '</head><body>'
    ret += '<div class="container" style="display:flex">'
    ret += '<img width=750 height=750 src="/board.svg?%f" style="flex:1"></img></br>' % time.time()
    ret += '<div class="request" style="flex:1 flex-direction:column">'
    ret += '<form action="/newgame/" method="post"><button name="New Game" type="submit">Game mới</button></form>'
    ret += '<form action="/undo/" method="post"><button name="Undo" type="submit">Đi lại</button></form>'
    ret += '<form action="/move/"><input type="submit" value="Tạo nước người đi:"><input name="move" type="text"></input></form>'
    ret += '<form action="/chess/" method="post"><button name="Comp Move" type="submit">Tạo nước đi của máy</button></form>'
    ret += '</div>'
    ret += '</div>'
    if board.is_stalemate():
        ret += '<p>Hòa cờ</p>'
    elif board.is_checkmate():
        ret += '<p>Chiếu tướng</p>'
    elif board.is_insufficient_material():
        ret += '<p>Hòa cờ do không đủ quân</p>'
    elif board.is_check():
        ret += '<p>Chiếu</p>'
    return ret


# Biểu diễn bàn cờ
@app.route("/board.svg/")
def board():
    return Response(chess.svg.board(board=board, size=700), mimetype='image/svg+xml')


# Người đi
@app.route("/move/")
def move():
    try:
        move = request.args.get('move', default="")
        board.push_san(move)
    except Exception:
        traceback.print_exc()
    return main()



# Máy đi
@app.route("/chess/", methods=['POST'])
def dev():
    try:
        devmove()
    except Exception:
        traceback.print_exc()
    return main()


#Game mới
@app.route("/newgame/", methods=['POST'])
def game():
    board.reset()
    return main()

# Đi lại
@app.route("/undo/", methods=['POST'])
def undo():
    try:
        board.pop()
    except Exception:
        traceback.print_exc()
    return main()


# Hàm main
if __name__ == '__main__':
    count = 1
    board = chess.Board()
    webbrowser.open("http://127.0.0.1:5000/")
    app.run()

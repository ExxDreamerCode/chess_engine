import copy

EMPTY = '.'
W_PAWN = 'P'
W_KNIGHT = 'N'
W_BISHOP = 'B'
W_ROOK = 'R'
W_QUEEN = 'Q'
W_KING = 'K'
B_PAWN = 'p'
B_KNIGHT = 'n'
B_BISHOP = 'b'
B_ROOK = 'r'
B_QUEEN = 'q'
B_KING = 'k'

PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
    'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000
}

def mirror_vertical(table):
    return list(reversed(table))

PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [20, 20, 20,-10,-10, 20, 20, 20],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [0,  0,  0, 25, 25,  0,  0,  0],
    [5,  5, 10, 27, 27, 10,  5,  5],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-22,  0,  2,  2,  0,-22,-40],
    [-30,  2, 12, 17, 17, 12,  2,-30],
    [-30,  7, 17, 22, 22, 17,  7,-30],
    [-30,  2, 17, 22, 22, 17,  2,-30],
    [-30,  5, 12, 17, 17, 12,  5,-30],
    [-40,-22,  2,  5,  5,  2,-22,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  5,  0,  0,  0,  0,  5,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  0, 10, 12, 12, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0,  5, 10, 10,  5,  0,-10],
    [-10,  5,  5,  5,  5,  5,  5,-10],
    [-20,-10,-10,-10,-10,-10,-10,-20]
]

ROOK_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10, 10, 10, 10, 10,  5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [-5,  0,  0,  0,  0,  0,  0, -5],
    [0,  0,  0,  5,  5,  0,  0,  0]
]

QUEEN_TABLE = [
    [-20,-10,-10, -5, -5,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0,  5,  5,  5,  5,  0,-10],
    [-5,  0,  5,  5,  5,  5,  0, -5],
    [0,  0,  5,  5,  5,  5,  0, -5],
    [-10,  5,  5,  5,  5,  5,  0,-10],
    [-10,  0,  5,  0,  0,  0,  0,-10],
    [-20,-10,-10, -5, -5,-10,-10,-20]
]

KING_MIDDLE_TABLE = [
    [20, 30, 10,  0,  0, 10, 30, 20],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30]
]

KING_ENDGAME_TABLE = [
    [-50,-40,-30,-20,-20,-30,-40,-50],
    [-30,-20,-10,  0,  0,-10,-20,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 30, 40, 40, 30,-10,-30],
    [-30,-10, 20, 30, 30, 20,-10,-30],
    [-30,-30,  0,  0,  0,  0,-30,-30],
    [-50,-30,-30,-30,-30,-30,-30,-50]
]

PAWN_ENDGAME_TABLE = [
    [0,   0,   0,   0,   0,   0,   0,   0],
    [80,  80,  90, 100, 100, 90,  80,  80],
    [50,  50,  60,  80,  80,  60,  50,  50],
    [20,  20,  30,  40,  40,  30,  20,  20],
    [5,   5,  10,  20,  20,  10,   5,   5],
    [0,   0,   0,   0,   0,   0,   0,   0],
    [0,   0,   0,   0,   0,   0,   0,   0],
    [0,   0,   0,   0,   0,   0,   0,   0]
]

KING_ACTIVITY_TABLE = [
    [10, 20, 30, 30, 30, 30, 20, 10],
    [20, 30, 40, 40, 40, 40, 30, 20],
    [30, 40, 50, 50, 50, 50, 40, 30],
    [30, 40, 50, 60, 60, 50, 40, 30],
    [30, 40, 50, 60, 60, 50, 40, 30],
    [30, 40, 50, 50, 50, 50, 40, 30],
    [20, 30, 40, 40, 40, 40, 30, 20],
    [10, 20, 30, 30, 30, 30, 20, 10]
]


class Board:

    def __init__(self):
        self.board = self.get_initial_board()
        self.turn = 'white'
        self.en_passant_target = None
        self.last_move = None
        self.move_history = []
        self.position_history = {}
        self.halfmove_clock = 0
        self.fullmove_number = 1

        self.castling_rights = {
            'white_kingside': True,
            'white_queenside': True,
            'black_kingside': True,
            'black_queenside': True
        }

    def get_initial_board(self):
        return [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]

    def get_state(self):
        return (self.turn, self.en_passant_target, self.last_move,
                [row[:] for row in self.board],
                dict(self.castling_rights),
                self.halfmove_clock,
                self.fullmove_number,
                self.move_history[:],
                dict(self.position_history))

    def set_state(self, state):
        if len(state) == 9:
            (self.turn, self.en_passant_target, self.last_move, self.board,
             self.castling_rights, self.halfmove_clock, self.fullmove_number,
             self.move_history, self.position_history) = state
        elif len(state) == 8:
            (self.turn, self.en_passant_target, self.last_move, self.board,
             self.castling_rights, self.halfmove_clock, self.fullmove_number,
             self.move_history) = state
        elif len(state) == 7:
            (self.turn, self.en_passant_target, self.last_move, self.board,
             self.castling_rights, self.halfmove_clock, self.fullmove_number) = state
        elif len(state) == 5:
            self.turn, self.en_passant_target, self.last_move, self.board, self.castling_rights = state
        else:
            self.turn, self.en_passant_target, self.last_move, self.board = state

    def square_to_coord(self, square):
        col_map = {'a': 0, 'b': 1, 'c': 2, 'd': 3, 'e': 4, 'f': 5, 'g': 6, 'h': 7}
        col = col_map[square[0]]
        row = 8 - int(square[1])
        return row, col

    def coord_to_square(self, row, col):
        col_map = {0: 'a', 1: 'b', 2: 'c', 3: 'd', 4: 'e', 5: 'f', 6: 'g', 7: 'h'}
        return col_map[col] + str(8 - row)

    def get_piece_color(self, piece):
        if piece == '.':
            return None
        return 'white' if piece.isupper() else 'black'

    def find_king(self, board, color):
        target = 'K' if color == 'white' else 'k'
        for row in range(8):
            for col in range(8):
                if board[row][col] == target:
                    return (row, col)
        return None

    def get_material_count(self):
        white = 0
        black = 0
        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9}
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.':
                    value = piece_values.get(piece.lower(), 0)
                    if piece.isupper():
                        white += value
                    else:
                        black += value
        return white, black

    def get_total_material(self):
        total = 0
        piece_values = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9}
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and piece.lower() != 'k':
                    total += piece_values.get(piece.lower(), 0)
        return total

    def can_piece_attack(self, from_row, from_col, to_row, to_col):
        piece = self.board[from_row][from_col]
        piece_type = piece.lower()
        dr = to_row - from_row
        dc = to_col - from_col

        if piece_type == 'p':
            direction = -1 if piece.isupper() else 1
            return dr == direction and abs(dc) == 1
        elif piece_type == 'n':
            return (abs(dr) == 2 and abs(dc) == 1) or (abs(dr) == 1 and abs(dc) == 2)
        elif piece_type in ['b', 'r', 'q']:
            if piece_type == 'b' and not (dr != 0 and dc != 0):
                return False
            if piece_type == 'r' and not (dr == 0 or dc == 0):
                return False
            if piece_type == 'q' and not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
                return False
            step_r = 1 if dr > 0 else -1 if dr < 0 else 0
            step_c = 1 if dc > 0 else -1 if dc < 0 else 0
            r, c = from_row + step_r, from_col + step_c
            while (r, c) != (to_row, to_col):
                if not (0 <= r < 8 and 0 <= c < 8) or self.board[r][c] != '.':
                    return False
                r += step_r
                c += step_c
            return True
        elif piece_type == 'k':
            return max(abs(dr), abs(dc)) == 1
        return False

    def can_piece_attack_on_board(self, board, from_row, from_col, to_row, to_col):
        piece = board[from_row][from_col]
        piece_type = piece.lower()
        dr = to_row - from_row
        dc = to_col - from_col

        if piece_type == 'p':
            direction = -1 if piece.isupper() else 1
            return dr == direction and abs(dc) == 1
        elif piece_type == 'n':
            return (abs(dr) == 2 and abs(dc) == 1) or (abs(dr) == 1 and abs(dc) == 2)
        elif piece_type in ['b', 'r', 'q']:
            if piece_type == 'b' and not (dr != 0 and dc != 0):
                return False
            if piece_type == 'r' and not (dr == 0 or dc == 0):
                return False
            if piece_type == 'q' and not (dr == 0 or dc == 0 or abs(dr) == abs(dc)):
                return False
            step_r = 1 if dr > 0 else -1 if dr < 0 else 0
            step_c = 1 if dc > 0 else -1 if dc < 0 else 0
            r, c = from_row + step_r, from_col + step_c
            while (r, c) != (to_row, to_col):
                if not (0 <= r < 8 and 0 <= c < 8) or board[r][c] != '.':
                    return False
                r += step_r
                c += step_c
            return True
        elif piece_type == 'k':
            return max(abs(dr), abs(dc)) == 1
        return False

    def is_square_attacked(self, square, color):
        if isinstance(square, str):
            row, col = self.square_to_coord(square)
        else:
            row, col = square
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '.' and self.get_piece_color(piece) == color:
                    if self.can_piece_attack(r, c, row, col):
                        return True
        return False

    def is_square_attacked_on_board(self, board, row, col, color):
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece != '.' and self.get_piece_color(piece) == color:
                    if self.can_piece_attack_on_board(board, r, c, row, col):
                        return True
        return False

    def get_piece_moves(self, row, col):
        piece = self.board[row][col]
        color = self.get_piece_color(piece)
        if not color:
            return []

        moves = []
        piece_type = piece.lower()

        if piece_type == 'p':
            direction = -1 if color == 'white' else 1
            start_row = 6 if color == 'white' else 1
            new_row = row + direction
            if 0 <= new_row < 8 and self.board[new_row][col] == '.':
                moves.append((new_row, col))
                new_row2 = row + 2*direction
                if row == start_row and self.board[new_row2][col] == '.':
                    moves.append((new_row2, col))
            for dc in [-1, 1]:
                new_row, new_col = row + direction, col + dc
                if 0 <= new_row < 8 and 0 <= new_col < 8:
                    target = self.board[new_row][new_col]
                    if target != '.' and self.get_piece_color(target) != color:
                        moves.append((new_row, new_col))
                    en_passant_coord = self.coord_to_square(new_row, new_col)
                    if self.en_passant_target and self.en_passant_target == en_passant_coord:
                        moves.append((new_row, new_col))

        elif piece_type == 'n':
            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                           (1, -2), (1, 2), (2, -1), (2, 1)]
            for dr, dc in knight_moves:
                new_r, new_c = row + dr, col + dc
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    target = self.board[new_r][new_c]
                    if target == '.' or self.get_piece_color(target) != color:
                        moves.append((new_r, new_c))

        elif piece_type in ['b', 'r', 'q']:
            if piece_type == 'b':
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
            elif piece_type == 'r':
                directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
            else:
                directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                             (-1, 0), (1, 0), (0, -1), (0, 1)]
            for dr, dc in directions:
                for step in range(1, 8):
                    new_r, new_c = row + dr*step, col + dc*step
                    if not (0 <= new_r < 8 and 0 <= new_c < 8):
                        break
                    target = self.board[new_r][new_c]
                    if target == '.':
                        moves.append((new_r, new_c))
                    else:
                        if self.get_piece_color(target) != color:
                            moves.append((new_r, new_c))
                        break

        elif piece_type == 'k':
            king_moves = [(-1, -1), (-1, 0), (-1, 1),
                         (0, -1), (0, 1),
                         (1, -1), (1, 0), (1, 1)]
            for dr, dc in king_moves:
                new_r, new_c = row + dr, col + dc
                if 0 <= new_r < 8 and 0 <= new_c < 8:
                    target = self.board[new_r][new_c]
                    if target == '.' or self.get_piece_color(target) != color:
                        moves.append((new_r, new_c))

            opponent_color = 'black' if color == 'white' else 'white'
            if not self.is_square_attacked((row, col), opponent_color):
                if color == 'white':
                    if (self.castling_rights['white_kingside'] and
                        self.board[7][7] == 'R' and
                        self.board[7][5] == '.' and self.board[7][6] == '.' and
                        not self.is_square_attacked((7, 5), opponent_color) and
                        not self.is_square_attacked((7, 6), opponent_color)):
                        moves.append((7, 6))
                    if (self.castling_rights['white_queenside'] and
                        self.board[7][0] == 'R' and
                        self.board[7][1] == '.' and self.board[7][2] == '.' and
                        self.board[7][3] == '.' and
                        not self.is_square_attacked((7, 3), opponent_color) and
                        not self.is_square_attacked((7, 2), opponent_color)):
                        moves.append((7, 2))
                else:
                    if (self.castling_rights['black_kingside'] and
                        self.board[0][7] == 'r' and
                        self.board[0][5] == '.' and self.board[0][6] == '.' and
                        not self.is_square_attacked((0, 5), opponent_color) and
                        not self.is_square_attacked((0, 6), opponent_color)):
                        moves.append((0, 6))
                    if (self.castling_rights['black_queenside'] and
                        self.board[0][0] == 'r' and
                        self.board[0][1] == '.' and self.board[0][2] == '.' and
                        self.board[0][3] == '.' and
                        not self.is_square_attacked((0, 3), opponent_color) and
                        not self.is_square_attacked((0, 2), opponent_color)):
                        moves.append((0, 2))
        return moves

    def is_move_legal(self, start, end):
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        piece_color = self.get_piece_color(piece)

        temp_board = [row[:] for row in self.board]

        if piece.lower() == 'k' and abs(start_col - end_col) == 2:
            direction = 1 if end_col > start_col else -1
            for c in range(start_col + direction, end_col + direction, direction):
                check_board = [row[:] for row in self.board]
                check_board[start_row][c] = piece
                check_board[start_row][start_col] = '.'
                opponent_color = 'black' if piece_color == 'white' else 'white'
                if self.is_square_attacked_on_board(check_board, start_row, c, opponent_color):
                    return False

            temp_board[end_row][end_col] = piece
            temp_board[start_row][start_col] = '.'
            if end_col > start_col:
                temp_board[start_row][5] = temp_board[start_row][7]
                temp_board[start_row][7] = '.'
            else:
                temp_board[start_row][3] = temp_board[start_row][0]
                temp_board[start_row][0] = '.'
        else:
            temp_board[end_row][end_col] = piece
            temp_board[start_row][start_col] = '.'
            if piece.lower() == 'p' and (end_row == 0 or end_row == 7):
                temp_board[end_row][end_col] = 'Q' if piece.isupper() else 'q'

        king_pos = None
        king_char = 'K' if piece_color == 'white' else 'k'
        for r in range(8):
            for c in range(8):
                if temp_board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break

        if not king_pos:
            return False

        opponent_color = 'black' if piece_color == 'white' else 'white'
        if self.is_square_attacked_on_board(temp_board, king_pos[0], king_pos[1], opponent_color):
            return False

        return True

    def get_all_legal_moves(self, color=None):
        if color is None:
            color = self.turn
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == color:
                    moves = self.get_piece_moves(row, col)
                    for move in moves:
                        if self.is_move_legal((row, col), move):
                            all_moves.append(((row, col), move))
        return all_moves

    def make_move(self, start, end, promotion='q', record_history=True):
        start_row, start_col = start
        end_row, end_col = end
        piece = self.board[start_row][start_col]
        captured = self.board[end_row][end_col]

        if piece.lower() == 'p' or captured != '.':
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1

        if record_history:
            self.move_history.append({
                'start': start,
                'end': end,
                'piece': piece,
                'captured': captured,
                'en_passant': self.en_passant_target,
                'promotion': None
            })

        self.last_move = (start, end)

        if piece == 'K':
            self.castling_rights['white_kingside'] = False
            self.castling_rights['white_queenside'] = False
        elif piece == 'k':
            self.castling_rights['black_kingside'] = False
            self.castling_rights['black_queenside'] = False

        if piece == 'R':
            if start == (7, 7):
                self.castling_rights['white_kingside'] = False
            elif start == (7, 0):
                self.castling_rights['white_queenside'] = False
        elif piece == 'r':
            if start == (0, 7):
                self.castling_rights['black_kingside'] = False
            elif start == (0, 0):
                self.castling_rights['black_queenside'] = False

        if captured == 'R':
            if end == (7, 7):
                self.castling_rights['white_kingside'] = False
            elif end == (7, 0):
                self.castling_rights['white_queenside'] = False
        elif captured == 'r':
            if end == (0, 7):
                self.castling_rights['black_kingside'] = False
            elif end == (0, 0):
                self.castling_rights['black_queenside'] = False

        if piece.lower() == 'p' and captured == '.' and start_col != end_col:
            self.board[start_row][end_col] = '.'

        if piece.lower() == 'k' and abs(start_col - end_col) == 2:
            if end_col > start_col:
                self.board[start_row][5] = self.board[start_row][7]
                self.board[start_row][7] = '.'
            else:
                self.board[start_row][3] = self.board[start_row][0]
                self.board[start_row][0] = '.'

        self.board[end_row][end_col] = piece
        self.board[start_row][start_col] = '.'

        if piece.lower() == 'p' and (end_row == 0 or end_row == 7):
            prom_piece = promotion.upper() if piece.isupper() else promotion
            self.board[end_row][end_col] = prom_piece
            if record_history:
                self.move_history[-1]['promotion'] = promotion

        self.en_passant_target = None
        if piece.lower() == 'p' and abs(start_row - end_row) == 2:
            target_row = (start_row + end_row) // 2
            self.en_passant_target = self.coord_to_square(target_row, start_col)

        if self.turn == 'black':
            self.fullmove_number += 1

        self.turn = 'black' if self.turn == 'white' else 'white'

        board_hash = self.get_board_hash()
        self.position_history[board_hash] = self.position_history.get(board_hash, 0) + 1

    def get_board_hash(self):
        board_tuple = tuple(tuple(row) for row in self.board)
        return hash((board_tuple, self.turn, self.en_passant_target,
                     tuple(self.castling_rights.items())))

    def is_in_check(self, color=None):
        if color is None:
            color = self.turn
        king_pos = self.find_king(self.board, color)
        if not king_pos:
            return False
        opponent_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked((king_pos[0], king_pos[1]), opponent_color)

    def is_checkmate(self):
        if not self.is_in_check(self.turn):
            return False
        return len(self.get_all_legal_moves()) == 0

    def is_stalemate(self):
        if self.is_in_check(self.turn):
            return False
        return len(self.get_all_legal_moves()) == 0

    def is_threefold_repetition(self):
        board_hash = self.get_board_hash()
        return self.position_history.get(board_hash, 0) >= 3

    def is_fifty_move_rule(self):
        return self.halfmove_clock >= 100

    def is_insufficient_material(self):
        pieces = {'white': [], 'black': []}

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.':
                    color = 'white' if piece.isupper() else 'black'
                    pieces[color].append(piece.lower())

        white_pieces = pieces['white']
        black_pieces = pieces['black']

        if len(white_pieces) == 1 and len(black_pieces) == 1:
            return True

        if len(white_pieces) == 1 and len(black_pieces) == 2:
            if 'n' in black_pieces or 'b' in black_pieces:
                return True
        if len(black_pieces) == 1 and len(white_pieces) == 2:
            if 'n' in white_pieces or 'b' in white_pieces:
                return True

        if (len(white_pieces) == 2 and len(black_pieces) == 2 and
            'b' in white_pieces and 'b' in black_pieces):
            white_bishop_sq = None
            black_bishop_sq = None
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece == 'B':
                        white_bishop_sq = (row, col)
                    elif piece == 'b':
                        black_bishop_sq = (row, col)

            if white_bishop_sq and black_bishop_sq:
                white_bishop_color = (white_bishop_sq[0] + white_bishop_sq[1]) % 2
                black_bishop_color = (black_bishop_sq[0] + black_bishop_sq[1]) % 2
                if white_bishop_color == black_bishop_color:
                    return True

        return False

    def is_draw(self, advantage_tolerance=400):
        if self.is_stalemate():
            return True, "stalemate"
        if self.is_fifty_move_rule():
            return True, "fifty_moves"
        if self.is_insufficient_material():
            return True, "insufficient_material"

        white_score, black_score = self.get_material_count()
        advantage = abs(white_score - black_score)

        if self.is_threefold_repetition():
            if advantage < advantage_tolerance:
                return True, "threefold_repetition"

        return False, None
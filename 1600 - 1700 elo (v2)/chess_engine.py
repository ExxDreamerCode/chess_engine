import copy
import math
import random
import time
from opening_book import find_book_moves


PIECE_VALUES = {
    'P': 100, 'N': 320, 'B': 330, 'R': 500, 'Q': 900, 'K': 20000,
    'p': -100, 'n': -320, 'b': -330, 'r': -500, 'q': -900, 'k': -20000
}

PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

BISHOP_TABLE = [
    [-20,-10,-10,-10,-10,-10,-10,-20],
    [-10,  0,  0,  0,  0,  0,  0,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10,  5,  5, 10, 10,  5,  5,-10],
    [-10,  0, 10, 10, 10, 10,  0,-10],
    [-10, 10, 10, 10, 10, 10, 10,-10],
    [-10,  5,  0,  0,  0,  0,  5,-10],
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

KING_TABLE_MIDDLE = [
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-30,-40,-40,-50,-50,-40,-40,-30],
    [-20,-30,-30,-40,-40,-30,-30,-20],
    [-10,-20,-20,-20,-20,-20,-20,-10],
    [20, 20,  0,  0,  0,  0, 20, 20],
    [20, 30, 10,  0,  0, 10, 30, 20]
]

KING_TABLE_END = [
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
    [120, 120, 120, 120, 120, 120, 120, 120],
    [80,  80,  90,  100, 100, 90,  80,  80],
    [50,  50,  60,  80,  80,  60,  50,  50],
    [20,  20,  30,  40,  40,  30,  20,  20],
    [5,   5,   10,  20,  20,  10,  5,   5],
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

transposition_table = {}


class ChessEngine:
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
                self.fullmove_number)
    
    def set_state(self, state):
        if len(state) == 7:
            self.turn, self.en_passant_target, self.last_move, self.board, self.castling_rights, self.halfmove_clock, self.fullmove_number = state
        elif len(state) == 5:
            self.turn, self.en_passant_target, self.last_move, self.board, self.castling_rights = state
        else:
            self.turn, self.en_passant_target, self.last_move, self.board = state
    
    def get_board_hash(self):
        board_tuple = tuple(tuple(row) for row in self.board)
        return hash((board_tuple, self.turn, self.en_passant_target, 
                     tuple(self.castling_rights.items())))
    
    def get_material_value(self):
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
    
    def is_square_defended(self, square, color):
        if isinstance(square, str):
            row, col = self.square_to_coord(square)
        else:
            row, col = square
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '.' and self.get_piece_color(piece) == color:
                    if piece.lower() != 'k':
                        moves = self.get_piece_moves(r, c)
                        if (row, col) in moves:
                            return True
        return False
    
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
    
    def evaluate_passed_pawns(self, is_endgame):
        score = 0
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                
                if piece == 'P':
                    is_passed = True
                    for r in range(row):
                        for c in [col - 1, col, col + 1]:
                            if 0 <= c < 8 and self.board[r][c] == 'p':
                                is_passed = False
                                break
                        if not is_passed:
                            break
                    
                    if is_passed:
                        progress = 7 - row
                        
                        if is_endgame:
                            passed_value = 50 + progress * 40
                            
                            moves_to_queen = progress
                            
                            opponent_king = self.find_king(self.board, 'black')
                            if opponent_king:
                                king_row, king_col = opponent_king
                                king_distance = max(abs(king_row - row), abs(king_col - col))
                                if king_distance <= moves_to_queen + 1:
                                    passed_value -= (moves_to_queen - king_distance) * 20
                            
                            for r in range(8):
                                if self.board[r][col] == 'R':
                                    passed_value += 30
                                    break
                            
                            is_defended = False
                            if col > 0 and row + 1 < 8 and self.board[row + 1][col - 1] == 'P':
                                is_defended = True
                            if col < 7 and row + 1 < 8 and self.board[row + 1][col + 1] == 'P':
                                is_defended = True
                            if is_defended:
                                passed_value += 40
                            
                            score += passed_value
                        else:
                            score += 30 + progress * 20
                
                elif piece == 'p':
                    is_passed = True
                    for r in range(row + 1, 8):
                        for c in [col - 1, col, col + 1]:
                            if 0 <= c < 8 and self.board[r][c] == 'P':
                                is_passed = False
                                break
                        if not is_passed:
                            break
                    
                    if is_passed:
                        progress = row
                        
                        if is_endgame:
                            passed_value = 50 + progress * 40
                            
                            moves_to_queen = progress
                            
                            opponent_king = self.find_king(self.board, 'white')
                            if opponent_king:
                                king_row, king_col = opponent_king
                                king_distance = max(abs(king_row - row), abs(king_col - col))
                                if king_distance <= moves_to_queen + 1:
                                    passed_value -= (moves_to_queen - king_distance) * 20
                            
                            for r in range(8):
                                if self.board[r][col] == 'r':
                                    passed_value += 30
                                    break
                            
                            is_defended = False
                            if col > 0 and row - 1 >= 0 and self.board[row - 1][col - 1] == 'p':
                                is_defended = True
                            if col < 7 and row - 1 >= 0 and self.board[row - 1][col + 1] == 'p':
                                is_defended = True
                            if is_defended:
                                passed_value += 40
                            
                            score -= passed_value
                        else:
                            score -= 30 + progress * 20
        
        return score

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
                        not self.is_square_attacked((7, 2), opponent_color) and 
                        not self.is_square_attacked((7, 1), opponent_color)):
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
                        not self.is_square_attacked((0, 2), opponent_color) and 
                        not self.is_square_attacked((0, 1), opponent_color)):
                        moves.append((0, 2))
        return moves
    
    def can_piece_attack_on_board(self, from_row, from_col, to_row, to_col, board):
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
    
    def is_square_attacked_on_board(self, board, row, col, color):
        for r in range(8):
            for c in range(8):
                piece = board[r][c]
                if piece != '.' and self.get_piece_color(piece) == color:
                    if self.can_piece_attack_on_board(r, c, row, col, board):
                        return True
        return False
    
    def is_move_legal(self, start, end, strict_check=False):
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
    
    def get_all_legal_moves(self, color=None, strict_check=False):
        if color is None:
            color = self.turn
        all_moves = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == color:
                    moves = self.get_piece_moves(row, col)
                    for move in moves:
                        if self.is_move_legal((row, col), move, strict_check):
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
        
        if record_history:
            board_hash = self.get_board_hash()
            self.position_history[board_hash] = self.position_history.get(board_hash, 0) + 1
    
    def find_king(self, board, color):
        target = 'K' if color == 'white' else 'k'
        for row in range(8):
            for col in range(8):
                if board[row][col] == target:
                    return (row, col)
        return None
    
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
    
    def is_draw(self, advantage_tolerance=300):
        if self.is_stalemate():
            return True, "stalemate"
        if self.is_fifty_move_rule():
            return True, "fifty_moves"
        if self.is_insufficient_material():
            return True, "insufficient_material"
        
        white_score, black_score = self.get_material_value()
        total_score = white_score - black_score
        advantage = abs(total_score)
        
        if self.is_threefold_repetition():
            if advantage < advantage_tolerance:
                return True, "threefold_repetition"
            else:
                return False, None
        
        return False, None
    
    def get_pawn_structure_score(self):
        score = 0
        white_pawns = []
        black_pawns = []
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == 'P':
                    white_pawns.append((row, col))
                elif piece == 'p':
                    black_pawns.append((row, col))
        
        for row, col in white_pawns:
            is_passed = True
            for r in range(row):
                for c in [col - 1, col, col + 1]:
                    if 0 <= c < 8 and self.board[r][c] == 'p':
                        is_passed = False
                        break
                if not is_passed:
                    break
            if is_passed:
                progress = 7 - row
                score += progress * 30
                
                is_defended = False
                for c in [col - 1, col + 1]:
                    if 0 <= c < 8 and self.board[row][c] == 'P':
                        is_defended = True
                        break
                if is_defended:
                    score += 40
        
        for row, col in black_pawns:
            is_passed = True
            for r in range(row + 1, 8):
                for c in [col - 1, col, col + 1]:
                    if 0 <= c < 8 and self.board[r][c] == 'P':
                        is_passed = False
                        break
                if not is_passed:
                    break
            if is_passed:
                progress = row
                score -= progress * 30
                
                is_defended = False
                for c in [col - 1, col + 1]:
                    if 0 <= c < 8 and self.board[row][c] == 'p':
                        is_defended = True
                        break
                if is_defended:
                    score -= 40
        
        white_cols = [c for _, c in white_pawns]
        black_cols = [c for _, c in black_pawns]
        
        for col in range(8):
            if white_cols.count(col) > 1:
                score -= 30
            if black_cols.count(col) > 1:
                score += 30
        
        for row, col in white_pawns:
            is_isolated = True
            for c in [col - 1, col + 1]:
                if 0 <= c < 8 and c in white_cols:
                    is_isolated = False
                    break
            if is_isolated:
                score -= 20
        
        for row, col in black_pawns:
            is_isolated = True
            for c in [col - 1, col + 1]:
                if 0 <= c < 8 and c in black_cols:
                    is_isolated = False
                    break
            if is_isolated:
                score += 20
        
        return score
    
    def evaluate_board(self):
        score = 0
        
        white_pawn_attacks = set()
        black_pawn_attacks = set()
        white_material = 0
        black_material = 0
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == 'P':
                    white_material += 1
                    for dc in [-1, 1]:
                        if 0 <= row - 1 < 8 and 0 <= col + dc < 8:
                            white_pawn_attacks.add((row - 1, col + dc))
                elif piece == 'p':
                    black_material += 1
                    for dc in [-1, 1]:
                        if 0 <= row + 1 < 8 and 0 <= col + dc < 8:
                            black_pawn_attacks.add((row + 1, col + dc))
                elif piece != '.' and piece.lower() != 'k':
                    value = {'n': 3, 'b': 3, 'r': 5, 'q': 9}.get(piece.lower(), 0)
                    if piece.isupper():
                        white_material += value
                    else:
                        black_material += value
        
        total_material = white_material + black_material
        is_endgame = total_material < 20
        
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece == '.':
                    continue
                
                score += PIECE_VALUES[piece]
                
                pos_score = 0
                if piece == 'P':
                    if is_endgame:
                        pos_score = PAWN_ENDGAME_TABLE[row][col]
                    else:
                        pos_score = PAWN_TABLE[row][col]
                elif piece == 'p':
                    if is_endgame:
                        pos_score = -PAWN_ENDGAME_TABLE[7-row][col]
                    else:
                        pos_score = -PAWN_TABLE[7-row][col]
                elif piece == 'N':
                    pos_score = KNIGHT_TABLE[row][col]
                elif piece == 'n':
                    pos_score = -KNIGHT_TABLE[7-row][col]
                elif piece == 'B':
                    pos_score = BISHOP_TABLE[row][col]
                elif piece == 'b':
                    pos_score = -BISHOP_TABLE[7-row][col]
                elif piece == 'R':
                    pos_score = ROOK_TABLE[row][col]
                elif piece == 'r':
                    pos_score = -ROOK_TABLE[7-row][col]
                elif piece == 'Q':
                    pos_score = QUEEN_TABLE[row][col]
                elif piece == 'q':
                    pos_score = -QUEEN_TABLE[7-row][col]
                elif piece == 'K':
                    pos_score = KING_TABLE_END[row][col] if is_endgame else KING_TABLE_MIDDLE[row][col]
                    if is_endgame:
                        pos_score += KING_ACTIVITY_TABLE[row][col]
                elif piece == 'k':
                    pos_score = -KING_TABLE_END[7-row][col] if is_endgame else -KING_TABLE_MIDDLE[7-row][col]
                    if is_endgame:
                        pos_score -= KING_ACTIVITY_TABLE[7-row][col]
                
                score += pos_score
                
                if piece.isupper() and piece not in ['P', 'K']:
                    if (row, col) in black_pawn_attacks:
                        piece_type = piece.lower()
                        penalty = {'q': 300, 'r': 250, 'b': 200, 'n': 200}.get(piece_type, 0)
                        score -= penalty
                elif piece.islower() and piece not in ['p', 'k']:
                    if (row, col) in white_pawn_attacks:
                        piece_type = piece.lower()
                        penalty = {'q': 300, 'r': 250, 'b': 200, 'n': 200}.get(piece_type, 0)
                        score += penalty
        
        if is_endgame:
            score += self.get_pawn_structure_score()
        
        if is_endgame:
            white_king_pos = self.find_king(self.board, 'white')
            black_king_pos = self.find_king(self.board, 'black')
            
            for row in range(8):
                for col in range(8):
                    piece = self.board[row][col]
                    if piece == 'P':
                        is_passed = True
                        for r in range(row):
                            for c in [col - 1, col, col + 1]:
                                if 0 <= c < 8 and self.board[r][c] == 'p':
                                    is_passed = False
                                    break
                            if not is_passed:
                                break
                        if is_passed:
                            if white_king_pos:
                                dist = max(abs(white_king_pos[0] - row), abs(white_king_pos[1] - col))
                                score += max(0, (7 - dist)) * 10
                            if black_king_pos:
                                dist = max(abs(black_king_pos[0] - row), abs(black_king_pos[1] - col))
                                score -= max(0, (7 - dist)) * 5
                    
                    elif piece == 'p':
                        is_passed = True
                        for r in range(row + 1, 8):
                            for c in [col - 1, col, col + 1]:
                                if 0 <= c < 8 and self.board[r][c] == 'P':
                                    is_passed = False
                                    break
                            if not is_passed:
                                break
                        if is_passed:
                            if black_king_pos:
                                dist = max(abs(black_king_pos[0] - row), abs(black_king_pos[1] - col))
                                score -= max(0, (7 - dist)) * 10
                            if white_king_pos:
                                dist = max(abs(white_king_pos[0] - row), abs(white_king_pos[1] - col))
                                score += max(0, (7 - dist)) * 5
        
        passed_pawn_score = self.evaluate_passed_pawns(is_endgame)
        score += passed_pawn_score
        
        if is_endgame:
            white_pawn_rows = [row for row in range(8) for col in range(8) if self.board[row][col] == 'P']
            black_pawn_rows = [row for row in range(8) for col in range(8) if self.board[row][col] == 'p']
            
            if white_pawn_rows:
                max_white_progress = max(7 - row for row in white_pawn_rows)
                if max_white_progress >= 5:
                    black_king = self.find_king(self.board, 'black')
                    if black_king:
                        king_distance = max(abs(black_king[0] - 7), abs(black_king[1]))
                        if king_distance > max_white_progress:
                            score += (max_white_progress - 2) * 50
            
            if black_pawn_rows:
                max_black_progress = max(row for row in black_pawn_rows)
                if max_black_progress <= 2:
                    white_king = self.find_king(self.board, 'white')
                    if white_king:
                        king_distance = max(abs(white_king[0] - 0), abs(white_king[1]))
                        if king_distance > (7 - max_black_progress):
                            score -= (max_black_progress - 2) * 50
        
        return score
    
    def evaluate_board_quick(self):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.':
                    score += PIECE_VALUES[piece]
        return score


class ChessAI:
    def __init__(self, engine, depth=4):
        self.engine = engine
        self.depth = depth
        self.nodes_searched = 0
        self.killer_moves = [[None, None] for _ in range(64)]
        self.history_table = {}
        self.max_mate_depth = 10
        self.rep_penalty = 300
    
    def order_moves(self, moves, depth):
        def move_score(move):
            start, end = move
            score = 0
            piece = self.engine.board[start[0]][start[1]].lower()
            
            target = self.engine.board[end[0]][end[1]]
            if target != '.':
                victim_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
                attacker_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
                attacker = piece
                victim = target.lower()
                score = 10000 + victim_values.get(victim, 0) - attacker_values.get(attacker, 0)
            
            if self.killer_moves[depth][0] == move:
                score = max(score, 9000)
            elif self.killer_moves[depth][1] == move:
                score = max(score, 8000)
            
            move_key = (start, end)
            if move_key in self.history_table:
                score = max(score, min(self.history_table[move_key], 7000))
            
            if piece == 'p' and (end[0] == 0 or end[0] == 7):
                score += 8000
            
            if piece == 'p':
                white_material, black_material = self.engine.get_material_value()
                total_material = white_material + black_material
                if total_material < 20:
                    score += 2000
                    if (self.engine.turn == 'white' and end[0] < start[0]) or \
                       (self.engine.turn == 'black' and end[0] > start[0]):
                        score += 3000
            
            return score
        
        return sorted(moves, key=move_score, reverse=True)
    
    def quiescence_search(self, alpha, beta, maximizing, depth_remaining=4):
        stand_pat = self.engine.evaluate_board()
        
        if depth_remaining <= 0:
            return stand_pat, None
        
        if maximizing:
            if stand_pat >= beta:
                return beta, None
            if alpha < stand_pat:
                alpha = stand_pat
        else:
            if stand_pat <= alpha:
                return alpha, None
            if beta > stand_pat:
                beta = stand_pat
        
        capture_moves = []
        for row in range(8):
            for col in range(8):
                piece = self.engine.board[row][col]
                if piece != '.' and self.engine.get_piece_color(piece) == self.engine.turn:
                    moves = self.engine.get_piece_moves(row, col)
                    for move in moves:
                        target = self.engine.board[move[0]][move[1]]
                        if target != '.' and self.engine.get_piece_color(target) != self.engine.turn:
                            capture_moves.append(((row, col), move))
        
        if not capture_moves:
            return stand_pat, None
        
        def move_priority(move):
            start, end = move
            victim = self.engine.board[end[0]][end[1]].lower()
            attacker = self.engine.board[start[0]][start[1]].lower()
            victim_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
            attacker_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
            return victim_values.get(victim, 0) - attacker_values.get(attacker, 0)
        
        capture_moves.sort(key=move_priority, reverse=True)
        
        if depth_remaining <= 2 and len(capture_moves) > 15:
            capture_moves = capture_moves[:15]
        
        for move in capture_moves:
            if not self.engine.is_move_legal(move[0], move[1]):
                continue
            
            state = self.engine.get_state()
            self.engine.make_move(move[0], move[1], record_history=False)
            
            score_result, _ = self.quiescence_search(alpha, beta, not maximizing, depth_remaining - 1)
            
            self.engine.set_state(state)
            
            if maximizing:
                if score_result >= beta:
                    return beta, None
                if score_result > alpha:
                    alpha = score_result
            else:
                if score_result <= alpha:
                    return alpha, None
                if score_result < beta:
                    beta = score_result
        
        return alpha if maximizing else beta, None
    
    def minimax(self, depth, alpha, beta, maximizing):
        self.nodes_searched += 1
        
        board_hash = self.engine.get_board_hash()
        if board_hash in transposition_table:
            tt_entry = transposition_table[board_hash]
            if tt_entry['depth'] >= depth:
                if tt_entry['flag'] == 'exact':
                    return tt_entry['value'], tt_entry['move']
                elif tt_entry['flag'] == 'alpha' and tt_entry['value'] <= alpha:
                    return tt_entry['value'], tt_entry['move']
                elif tt_entry['flag'] == 'beta' and tt_entry['value'] >= beta:
                    return tt_entry['value'], tt_entry['move']
        
        if depth == 0:
            q_score, _ = self.quiescence_search(alpha, beta, maximizing, depth_remaining=4)
            return q_score, None
        
        moves = self.engine.get_all_legal_moves()
        if not moves:
            if self.engine.is_in_check(self.engine.turn):
                return -100000 - depth if maximizing else 100000 + depth, None
            return 0, None
        
        moves = self.order_moves(moves, depth)
        
        best_move = moves[0] if moves else None
        original_alpha = alpha
        
        white_score, black_score = self.engine.get_material_value()
        current_advantage = white_score - black_score
        if self.engine.turn == 'black':
            current_advantage = -current_advantage
        
        REPETITION_PENALTY_THRESHOLD = 200
        
        if maximizing:
            max_eval = -math.inf
            for i, move in enumerate(moves):
                state = self.engine.get_state()
                self.engine.make_move(move[0], move[1], record_history=False)
                
                eval_penalty = 0
                if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2:
                    eval_penalty = self.rep_penalty
                
                if i >= 4 and depth >= 3:
                    eval_result, _ = self.minimax(depth - 2, alpha, beta, False)
                    eval_result -= eval_penalty
                    if eval_result <= alpha:
                        self.engine.set_state(state)
                        continue
                
                eval_result, _ = self.minimax(depth - 1, alpha, beta, False)
                eval_result -= eval_penalty
                self.engine.set_state(state)
                
                if eval_result > max_eval:
                    max_eval = eval_result
                    best_move = move
                    
                alpha = max(alpha, eval_result)
                if beta <= alpha:
                    if self.engine.board[move[1][0]][move[1][1]] == '.':
                        if self.killer_moves[depth][0] != move:
                            self.killer_moves[depth][1] = self.killer_moves[depth][0]
                            self.killer_moves[depth][0] = move
                    break
            
            if best_move:
                if max_eval <= original_alpha:
                    flag = 'alpha'
                elif max_eval >= beta:
                    flag = 'beta'
                else:
                    flag = 'exact'
                transposition_table[board_hash] = {
                    'value': max_eval, 'depth': depth, 'move': best_move, 'flag': flag
                }
            
            return max_eval, best_move
        else:
            min_eval = math.inf
            for i, move in enumerate(moves):
                state = self.engine.get_state()
                self.engine.make_move(move[0], move[1], record_history=False)
                
                eval_penalty = 0
                if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2:
                    eval_penalty = self.rep_penalty
                
                if i >= 4 and depth >= 3:
                    eval_result, _ = self.minimax(depth - 2, alpha, beta, True)
                    eval_result += eval_penalty
                    if eval_result >= beta:
                        self.engine.set_state(state)
                        continue
                
                eval_result, _ = self.minimax(depth - 1, alpha, beta, True)
                eval_result += eval_penalty
                self.engine.set_state(state)
                
                if eval_result < min_eval:
                    min_eval = eval_result
                    best_move = move
                    
                beta = min(beta, eval_result)
                if beta <= alpha:
                    if self.engine.board[move[1][0]][move[1][1]] == '.':
                        if self.killer_moves[depth][0] != move:
                            self.killer_moves[depth][1] = self.killer_moves[depth][0]
                            self.killer_moves[depth][0] = move
                    break
            
            if best_move:
                if min_eval <= original_alpha:
                    flag = 'alpha'
                elif min_eval >= beta:
                    flag = 'beta'
                else:
                    flag = 'exact'
                transposition_table[board_hash] = {
                    'value': min_eval, 'depth': depth, 'move': best_move, 'flag': flag
                }
            
            return min_eval, best_move
    
    def find_mate_in(self, max_depth):
        for mate_depth in range(1, max_depth + 1):
            self.nodes_searched = 0
            
            moves = self.engine.get_all_legal_moves()
            for move in moves:
                if not self.engine.is_move_legal(move[0], move[1]):
                    continue
                
                state = self.engine.get_state()
                self.engine.make_move(move[0], move[1], record_history=False)
                
                score, _ = self.minimax(mate_depth - 1, -math.inf, math.inf, 
                                       self.engine.turn == 'black')
                
                self.engine.set_state(state)
                
                if (self.engine.turn == 'white' and score > 90000) or \
                   (self.engine.turn == 'black' and score < -90000):
                    return move, mate_depth
            
            if mate_depth >= 6:
                break
        
        return None, 0
    
    def search_progress_moves(self, moves):
        scored_moves = []
        
        for move in moves:
            start, end = move
            piece = self.engine.board[start[0]][start[1]]
            
            state = self.engine.get_state()
            self.engine.make_move(start, end, record_history=False)
            
            opponent_color = 'black' if self.engine.turn == 'white' else 'white'
            opponent_king = self.engine.find_king(self.engine.board, opponent_color)
            
            if opponent_king:
                king_row, king_col = opponent_king
                edge_distance = min(king_row, 7 - king_row, king_col, 7 - king_col)
                edge_score = (3 - edge_distance) * 100
                
                attack_score = 0
                our_color = self.engine.turn
                for r in range(8):
                    for c in range(8):
                        p = self.engine.board[r][c]
                        if p != '.' and self.engine.get_piece_color(p) == our_color:
                            dist = max(abs(r - king_row), abs(c - king_col))
                            if dist <= 2:
                                attack_score += 50
                
                king_moves = self.engine.get_piece_moves(king_row, king_col)
                mobility_score = (8 - len(king_moves)) * 30
                
                white_material, black_material = self.engine.get_material_value()
                total_material = white_material + black_material
                
                score = self.engine.evaluate_board()
                
                total_score = score + edge_score + attack_score + mobility_score
                
                if total_material < 20 and piece.lower() == 'p':
                    if self.engine.turn == 'white':
                        progress = 7 - end[0]
                    else:
                        progress = end[0]
                    total_score += progress * 50
                
                if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2:
                    total_score -= 500
                
                scored_moves.append((move, total_score))
            
            self.engine.set_state(state)
        
        scored_moves.sort(key=lambda x: x[1], reverse=(self.engine.turn == 'white'))
        return scored_moves
    
    def is_move_safe(self, move):
        start, end = move
        piece = self.engine.board[start[0]][start[1]]
        piece_color = self.engine.get_piece_color(piece)
        opponent_color = 'black' if piece_color == 'white' else 'white'
        
        state = self.engine.get_state()
        self.engine.make_move(start, end, record_history=False)
        
        if self.engine.is_in_check(piece_color):
            self.engine.set_state(state)
            return False
        
        for row in range(8):
            for col in range(8):
                p = self.engine.board[row][col]
                if p != '.' and self.engine.get_piece_color(p) == piece_color:
                    if p.lower() == 'k':
                        continue
                    
                    attackers = []
                    for r2 in range(8):
                        for c2 in range(8):
                            attacker = self.engine.board[r2][c2]
                            if attacker != '.' and self.engine.get_piece_color(attacker) == opponent_color:
                                if self.engine.can_piece_attack_on_board(r2, c2, row, col, self.engine.board):
                                    attacker_value = abs(PIECE_VALUES.get(attacker, 0))
                                    attackers.append((attacker_value, attacker, (r2, c2)))
                    
                    if not attackers:
                        continue
                    
                    victim_value = abs(PIECE_VALUES.get(p, 0))
                    attackers.sort(key=lambda x: x[0])
                    
                    defenders = []
                    for r2 in range(8):
                        for c2 in range(8):
                            defender = self.engine.board[r2][c2]
                            if defender != '.' and self.engine.get_piece_color(defender) == piece_color:
                                if defender.lower() == 'k' and victim_value > 300:
                                    continue
                                if (r2, c2) != end:
                                    if self.engine.can_piece_attack_on_board(r2, c2, row, col, self.engine.board):
                                        defender_value = abs(PIECE_VALUES.get(defender, 0))
                                        defenders.append((defender_value, (r2, c2)))
                    
                    defenders.sort(key=lambda x: x[0])
                    
                    for attacker_value, attacker, att_pos in attackers:
                        has_good_defender = False
                        for defender_value, def_pos in defenders:
                            if defender_value <= attacker_value:
                                has_good_defender = True
                                break
                        
                        if not has_good_defender and attacker_value <= victim_value:
                            if attacker.lower() == 'p' and victim_value >= 300:
                                cheap_defender_exists = any(dv < 100 for dv, _ in defenders)
                                if not cheap_defender_exists:
                                    self.engine.set_state(state)
                                    return False
                            
                            can_recapture = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    recapturer = self.engine.board[r2][c2]
                                    if recapturer != '.' and self.engine.get_piece_color(recapturer) == piece_color:
                                        if self.engine.can_piece_attack_on_board(r2, c2, att_pos[0], att_pos[1], self.engine.board):
                                            recapturer_value = abs(PIECE_VALUES.get(recapturer, 0))
                                            if recapturer_value <= attacker_value:
                                                can_recapture = True
                                                break
                                    if can_recapture:
                                        break
                            
                            if not can_recapture:
                                self.engine.set_state(state)
                                return False
        
        self.engine.set_state(state)
        return True
    
    def evaluate_move_safety(self, move):
        start, end = move
        piece = self.engine.board[start[0]][start[1]]
        piece_color = self.engine.get_piece_color(piece)
        opponent_color = 'black' if piece_color == 'white' else 'white'
        
        state = self.engine.get_state()
        self.engine.make_move(start, end, record_history=False)
        
        penalty = 0
        
        for row in range(8):
            for col in range(8):
                p = self.engine.board[row][col]
                if p != '.' and self.engine.get_piece_color(p) == piece_color and p.lower() != 'k':
                    attackers = []
                    for r2 in range(8):
                        for c2 in range(8):
                            attacker = self.engine.board[r2][c2]
                            if attacker != '.' and self.engine.get_piece_color(attacker) == opponent_color:
                                if self.engine.can_piece_attack_on_board(r2, c2, row, col, self.engine.board):
                                    attacker_value = abs(PIECE_VALUES.get(attacker, 0))
                                    attackers.append((attacker_value, attacker))
                    
                    if not attackers:
                        continue
                    
                    victim_value = abs(PIECE_VALUES.get(p, 0))
                    
                    defenders = []
                    for r2 in range(8):
                        for c2 in range(8):
                            defender = self.engine.board[r2][c2]
                            if defender != '.' and self.engine.get_piece_color(defender) == piece_color:
                                if defender.lower() != 'k':
                                    if self.engine.can_piece_attack_on_board(r2, c2, row, col, self.engine.board):
                                        defender_value = abs(PIECE_VALUES.get(defender, 0))
                                        defenders.append(defender_value)
                    
                    defenders.sort()
                    
                    for attacker_value, attacker in attackers:
                        has_adequate_defender = any(dv <= attacker_value for dv in defenders)
                        
                        if not has_adequate_defender and attacker_value < victim_value:
                            loss = victim_value - attacker_value
                            penalty += loss
                            
                            if attacker_value < 100 and victim_value >= 300:
                                penalty += loss * 2
        
        self.engine.set_state(state)
        return penalty

    def should_avoid_repetition(self, advantage):
        if advantage > 250:
            return False
        if advantage > 100:
            return random.random() < 0.3
        return True

    def is_move_blunder(self, move):
        start, end = move
        piece = self.engine.board[start[0]][start[1]]
        piece_color = self.engine.get_piece_color(piece)
        opponent_color = 'black' if piece_color == 'white' else 'white'
        
        state = self.engine.get_state()
        self.engine.make_move(start, end, record_history=False)
        
        if self.engine.is_in_check(piece_color):
            self.engine.set_state(state)
            return True
        
        for row in range(8):
            for col in range(8):
                our_piece = self.engine.board[row][col]
                if our_piece == '.' or self.engine.get_piece_color(our_piece) != piece_color:
                    continue
                if our_piece.lower() == 'k':
                    continue
                
                our_value = abs(PIECE_VALUES.get(our_piece, 0))
                
                attackers = []
                for r2 in range(8):
                    for c2 in range(8):
                        attacker = self.engine.board[r2][c2]
                        if attacker != '.' and self.engine.get_piece_color(attacker) == opponent_color:
                            if self.engine.can_piece_attack_on_board(r2, c2, row, col, self.engine.board):
                                attackers.append((abs(PIECE_VALUES.get(attacker, 0)), (r2, c2)))
                if not attackers:
                    continue
                
                min_attacker_value = min(a[0] for a in attackers)
                
                defenders = []
                for r2 in range(8):
                    for c2 in range(8):
                        defender = self.engine.board[r2][c2]
                        if defender != '.' and self.engine.get_piece_color(defender) == piece_color:
                            if (r2, c2) != (row, col):
                                if self.engine.can_piece_attack_on_board(r2, c2, row, col, self.engine.board):
                                    defenders.append(abs(PIECE_VALUES.get(defender, 0)))
                
                if our_piece.lower() == 'p' and not defenders and attackers:
                    self.engine.set_state(state)
                    return True
                
                if our_piece.lower() == 'p' and defenders:
                    min_defender_value = min(defenders)
                    if min_attacker_value <= min_defender_value:
                        self.engine.set_state(state)
                        return True
                
                if not defenders and min_attacker_value < our_value:
                    self.engine.set_state(state)
                    return True
                
                if defenders:
                    min_defender_value = min(defenders)
                    if min_attacker_value <= min_defender_value and min_attacker_value < our_value:
                        self.engine.set_state(state)
                        return True
        
        self.engine.set_state(state)
        return False

    def get_best_move(self):
        self.nodes_searched = 0
        self.killer_moves = [[None, None] for _ in range(64)]
        
        white_score, black_score = self.engine.get_material_value()
        material_advantage = white_score - black_score
        if self.engine.turn == 'black':
            material_advantage = -material_advantage
        
        opponent_color = 'black' if self.engine.turn == 'white' else 'white'
        opponent_pieces = []
        for row in range(8):
            for col in range(8):
                piece = self.engine.board[row][col]
                if piece != '.' and self.engine.get_piece_color(piece) == opponent_color:
                    if piece.lower() != 'k':
                        opponent_pieces.append(piece.lower())
        
        book_moves = []
        book_move_found = False
        best_book_move = None
        best_book_score = -math.inf if self.engine.turn == 'white' else math.inf
        
        if len(self.engine.move_history) < 12:
            book_moves = find_book_moves(self.engine)
        
        all_legal_moves = self.engine.get_all_legal_moves()
        
        if not all_legal_moves:
            return None
        
        our_color = self.engine.turn
        
        if book_moves:
            legal_book_moves = [m for m in book_moves if m in all_legal_moves]
            
            if legal_book_moves:
                safe_book_moves = []
                
                for move in legal_book_moves:
                    if self.is_move_blunder(move):
                        continue
                    
                    state = self.engine.get_state()
                    self.engine.make_move(move[0], move[1], record_history=False)
                    
                    if self.engine.is_in_check(our_color):
                        self.engine.set_state(state)
                        continue
                    
                    new_white, new_black = self.engine.get_material_value()
                    if our_color == 'white':
                        material_loss = white_score - new_white
                    else:
                        material_loss = black_score - new_black
                    
                    if material_loss > 0:
                        self.engine.set_state(state)
                        continue
                    
                    rep_penalty = 0
                    if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2:
                        rep_penalty = 500
                    
                    score = self.engine.evaluate_board_quick() - rep_penalty
                    
                    self.engine.set_state(state)
                    
                    if self.is_move_safe(move):
                        safe_book_moves.append((move, score, True))
                    else:
                        penalty = self.evaluate_move_safety(move)
                        if penalty <= 50:
                            safe_book_moves.append((move, score - penalty, False))
                
                if safe_book_moves:
                    safe_book_moves.sort(key=lambda x: (x[2], x[1]), reverse=True)
                    best_book_move = safe_book_moves[0][0]
                    best_book_score = safe_book_moves[0][1]
                    book_move_found = True
        
        start_time = time.time()
        best_move = None
        TIME_LIMIT = 5.0
        best_moves_same_score = []
        
        search_depth = self.depth
        
        best_minimax_move = None
        best_minimax_score = -math.inf if our_color == 'white' else math.inf
        
        for depth in range(1, search_depth + 1):
            elapsed = time.time() - start_time
            if elapsed > TIME_LIMIT * 0.7:
                break
            
            self.nodes_searched = 0
            
            if self.engine.turn == 'white':
                best_score = -math.inf
                _, move = self.minimax(depth, -math.inf, math.inf, True)
                
                if move:
                    state = self.engine.get_state()
                    self.engine.make_move(move[0], move[1], record_history=False)
                    
                    score = self.engine.evaluate_board()
                    if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2:
                        score -= 200
                    
                    self.engine.set_state(state)
                    
                    if score > best_score:
                        best_moves_same_score = [move]
                        best_score = score
                    elif abs(score - best_score) < 15:
                        best_moves_same_score.append(move)
                    
                    best_move = move
                    best_minimax_score = score
            else:
                best_score = math.inf
                _, move = self.minimax(depth, -math.inf, math.inf, False)
                
                if move:
                    state = self.engine.get_state()
                    self.engine.make_move(move[0], move[1], record_history=False)
                    
                    score = self.engine.evaluate_board()
                    if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2:
                        score += 200
                    
                    self.engine.set_state(state)
                    
                    if score < best_score:
                        best_moves_same_score = [move]
                        best_score = score
                    elif abs(score - best_score) < 15:
                        best_moves_same_score.append(move)
                    
                    best_move = move
                    best_minimax_score = score
            
            if time.time() - start_time > TIME_LIMIT * 0.9:
                break
        
        best_minimax_move = best_move
        
        if book_move_found and best_minimax_move:
            if our_color == 'white':
                if best_minimax_score >= best_book_score - 100:
                    best_move = best_minimax_move
                else:
                    best_move = best_book_move
            else:
                if best_minimax_score <= best_book_score + 100:
                    best_move = best_minimax_move
                else:
                    best_move = best_book_move
        elif book_move_found:
            best_move = best_book_move
        elif best_minimax_move:
            best_move = best_minimax_move
        
        if not best_move:
            if all_legal_moves:
                best_move = all_legal_moves[0]
            else:
                return None
        
        if best_move:
            white_score, black_score = self.engine.get_material_value()
            current_advantage = white_score - black_score
            if self.engine.turn == 'black':
                current_advantage = -current_advantage
            
            state = self.engine.get_state()
            self.engine.make_move(best_move[0], best_move[1], record_history=False)
            
            leads_to_repetition = self.engine.position_history.get(
                self.engine.get_board_hash(), 0) >= 2
            
            self.engine.set_state(state)
            
            if leads_to_repetition:
                found_alternative = False
                
                if len(best_moves_same_score) > 1:
                    for move in best_moves_same_score:
                        if move == best_move:
                            continue
                        state = self.engine.get_state()
                        self.engine.make_move(move[0], move[1], record_history=False)
                        
                        is_rep = self.engine.position_history.get(
                            self.engine.get_board_hash(), 0) >= 2
                        
                        self.engine.set_state(state)
                        
                        if not is_rep:
                            best_move = move
                            found_alternative = True
                            break
                
                if not found_alternative:
                    for move in all_legal_moves:
                        if move == best_move:
                            continue
                        state = self.engine.get_state()
                        self.engine.make_move(move[0], move[1], record_history=False)
                        
                        if self.engine.is_in_check(self.engine.turn):
                            self.engine.set_state(state)
                            continue
                        
                        is_rep = self.engine.position_history.get(
                            self.engine.get_board_hash(), 0) >= 2
                        
                        self.engine.set_state(state)
                        
                        if not is_rep:
                            if self.is_move_safe(move):
                                best_move = move
                                found_alternative = True
                                break
            
            move_key = (best_move[0], best_move[1])
            self.history_table[move_key] = self.history_table.get(move_key, 0) + self.depth ** 2
        
        white_mat, black_mat = self.engine.get_material_value()
        total_advantage = white_mat - black_mat
        if self.engine.turn == 'black':
            total_advantage = -total_advantage
        
        if total_advantage > 300 and best_move:
            temp_state = self.engine.get_state()
            self.engine.make_move(best_move[0], best_move[1], record_history=False)
            leads_to_repetition = self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2
            self.engine.set_state(temp_state)
            
            if leads_to_repetition:
                found_alternative = False
                for move in all_legal_moves:
                    if move == best_move:
                        continue
                    
                    temp_state2 = self.engine.get_state()
                    self.engine.make_move(move[0], move[1], record_history=False)
                    is_repetition = self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2
                    self.engine.set_state(temp_state2)
                    
                    if not is_repetition and self.is_move_safe(move):
                        state3 = self.engine.get_state()
                        self.engine.make_move(move[0], move[1], record_history=False)
                        new_white, new_black = self.engine.get_material_value()
                        new_advantage = new_white - new_black
                        if self.engine.turn == 'black':
                            new_advantage = -new_advantage
                        self.engine.set_state(state3)
                        
                        if new_advantage > total_advantage - 100:
                            best_move = move
                            found_alternative = True
                            print(f"info string REPETITION AVOIDED: advantage={total_advantage}, found alternative {self.engine.coord_to_square(move[0][0], move[0][1])}{self.engine.coord_to_square(move[1][0], move[1][1])}")
                            break
                
                if not found_alternative:
                    if total_advantage > 500:
                        for move in all_legal_moves:
                            if move == best_move:
                                continue
                            temp_state3 = self.engine.get_state()
                            self.engine.make_move(move[0], move[1], record_history=False)
                            is_repetition = self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2
                            self.engine.set_state(temp_state3)
                            
                            if not is_repetition:
                                best_move = move
                                print(f"info string DESPERATE AVOIDANCE: advantage={total_advantage}, picked any non-repeating move")
                                break

        return best_move
import pygame
import copy
import math
import sys
import os
import urllib.request
from urllib.error import URLError
import zipfile
import io
import random

pygame.init()

BOARD_SIZE = 560
SQUARE_SIZE = BOARD_SIZE // 8
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
HIGHLIGHT = (255, 255, 0)
LAST_MOVE_COLOR = (170, 255, 170)
CHECK_COLOR = (255, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
GRAY = (128, 128, 128)


PNG_URLS = {
    'K': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wk.png',
    'Q': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wq.png',
    'R': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wr.png',
    'B': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wb.png',
    'N': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wn.png',
    'P': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wp.png',
    'k': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bk.png',
    'q': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bq.png',
    'r': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/br.png',
    'b': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bb.png',
    'n': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bn.png',
    'p': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bp.png'
}

PAWN_TABLE = [
    [0,  0,  0,  0,  0,  0,  0,  0],
    [5, 10, 10,-20,-20, 10, 10,  5],
    [5, -5,-10,  0,  0,-10, -5,  5],
    [0,  0,  0, 20, 20,  0,  0,  0],
    [5,  5, 10, 25, 25, 10,  5,  5],
    [10, 10, 20, 30, 30, 20, 10, 10],
    [50, 50, 50, 50, 50, 50, 50, 50],
    [0,  0,  0,  0,  0,  0,  0,  0]
]

KNIGHT_TABLE = [
    [-50,-40,-30,-30,-30,-30,-40,-50],
    [-40,-20,  0,  5,  5,  0,-20,-40],
    [-30,  5, 10, 15, 15, 10,  5,-30],
    [-30,  0, 15, 20, 20, 15,  0,-30],
    [-30,  5, 15, 20, 20, 15,  5,-30],
    [-30,  0, 10, 15, 15, 10,  0,-30],
    [-40,-20,  0,  0,  0,  0,-20,-40],
    [-50,-40,-30,-30,-30,-30,-40,-50]
]

class ChessEngine:
    def __init__(self):
        self.board = self.get_initial_board()
        self.turn = 'white'
        self.en_passant_target = None
        self.last_move = None
        self.move_history = []
        self.position_history = {}
        
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
                [row[:] for row in self.board])
    
    def set_state(self, state):
        self.turn, self.en_passant_target, self.last_move, self.board = state
    
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
        row, col = self.square_to_coord(square)
        
        for r in range(8):
            for c in range(8):
                piece = self.board[r][c]
                if piece != '.' and self.get_piece_color(piece) == color:
                    if self.can_piece_attack(r, c, row, col):
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
            if not self.is_square_attacked(self.coord_to_square(row, col), opponent_color):
                if color == 'white':
                    if (self.board[7][7] == 'R' and 
                        self.board[7][5] == '.' and 
                        self.board[7][6] == '.' and
                        not self.is_square_attacked('f1', opponent_color) and 
                        not self.is_square_attacked('g1', opponent_color)):
                        moves.append((7, 6))
                    if (self.board[7][0] == 'R' and 
                        self.board[7][1] == '.' and 
                        self.board[7][2] == '.' and 
                        self.board[7][3] == '.' and
                        not self.is_square_attacked('d1', opponent_color) and 
                        not self.is_square_attacked('c1', opponent_color) and 
                        not self.is_square_attacked('b1', opponent_color)):
                        moves.append((7, 2))
                else:
                    if (self.board[0][7] == 'r' and 
                        self.board[0][5] == '.' and 
                        self.board[0][6] == '.' and
                        not self.is_square_attacked('f8', opponent_color) and 
                        not self.is_square_attacked('g8', opponent_color)):
                        moves.append((0, 6))
                    if (self.board[0][0] == 'r' and 
                        self.board[0][1] == '.' and 
                        self.board[0][2] == '.' and 
                        self.board[0][3] == '.' and
                        not self.is_square_attacked('d8', opponent_color) and 
                        not self.is_square_attacked('c8', opponent_color) and 
                        not self.is_square_attacked('b8', opponent_color)):
                        moves.append((0, 2))
        
        return moves
    
    def is_move_legal(self, start, end):
        temp_board = [row[:] for row in self.board]
        
        start_row, start_col = start
        end_row, end_col = end
        piece = temp_board[start_row][start_col]
        
        if piece.lower() == 'k' and abs(start_col - end_col) == 2:
            direction = 1 if end_col > start_col else -1
            for c in range(start_col + direction, end_col + direction, direction):
                temp_board[start_row][c] = piece
                temp_board[start_row][start_col] = '.'
                king_color = self.get_piece_color(piece)
                king_char = 'K' if king_color == 'white' else 'k'
                king_pos = None
                for r in range(8):
                    for col in range(8):
                        if temp_board[r][col] == king_char:
                            king_pos = (r, col)
                            break
                    if king_pos:
                        break
                
                opponent_color = 'black' if king_color == 'white' else 'white'
                for r in range(8):
                    for col in range(8):
                        p = temp_board[r][col]
                        if p != '.' and self.get_piece_color(p) == opponent_color:
                            if self.can_piece_attack_on_board(r, col, king_pos[0], king_pos[1], temp_board):
                                return False
                temp_board[start_row][c] = '.'
                temp_board[start_row][start_col] = piece
            return True
        
        temp_board[end_row][end_col] = piece
        temp_board[start_row][start_col] = '.'
        
        if piece.lower() == 'p' and (end_row == 0 or end_row == 7):
            temp_board[end_row][end_col] = 'Q' if piece.isupper() else 'q'
        
        king_color = self.get_piece_color(piece)
        king_char = 'K' if king_color == 'white' else 'k'
        king_pos = None
        for r in range(8):
            for c in range(8):
                if temp_board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        
        if king_pos:
            opponent_color = 'black' if king_color == 'white' else 'white'
            for r in range(8):
                for c in range(8):
                    p = temp_board[r][c]
                    if p != '.' and self.get_piece_color(p) == opponent_color:
                        if self.can_piece_attack_on_board(r, c, king_pos[0], king_pos[1], temp_board):
                            return False
        
        return True
    
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
    
    def is_in_check(self, color):
        king_pos = self.find_king(self.board, color)
        if not king_pos:
            return False
        opponent_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked(self.coord_to_square(king_pos[0], king_pos[1]), opponent_color)
    
    def is_checkmate(self):
        if not self.is_in_check(self.turn):
            return False
        return len(self.get_all_legal_moves()) == 0
    
    def is_stalemate(self):
        if self.is_in_check(self.turn):
            return False
        return len(self.get_all_legal_moves()) == 0
    
    def get_board_hash(self):
        return ''.join(''.join(row) for row in self.board)
    
    def evaluate_board(self):
        piece_values = {
            'P': 10, 'N': 30, 'B': 30, 'R': 50, 'Q': 90, 'K': 900,
            'p': -10, 'n': -30, 'b': -30, 'r': -50, 'q': -90, 'k': -900
        }
        
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.':
                    score += piece_values[piece]
        
        return score

class ChessAI:
    def __init__(self, engine, depth=3):
        self.engine = engine
        self.depth = depth
    
    def minimax(self, depth, alpha, beta, maximizing):
        if depth == 0:
            return self.engine.evaluate_board(), None
        
        moves = self.engine.get_all_legal_moves()
        if not moves:
            if self.engine.is_in_check(self.engine.turn):
                return -10000 if maximizing else 10000, None
            return 0, None
        
        def move_priority(move):
            start, end = move
            target = self.engine.board[end[0]][end[1]]
            if target != '.':
                victim_val = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
                attacker_val = {'p': 1, 'n': 3, 'b': 3, 'r': 5, 'q': 9, 'k': 0}
                attacker = self.engine.board[start[0]][start[1]].lower()
                victim = target.lower()
                return 10 + victim_val.get(victim, 0) - attacker_val.get(attacker, 0)
            return 0
        moves.sort(key=move_priority, reverse=True)
        
        best_moves = []
        
        if maximizing:
            max_eval = -math.inf
            for move in moves:
                state = self.engine.get_state()
                
                self.engine.make_move(move[0], move[1])
                eval, _ = self.minimax(depth - 1, alpha, beta, False)
                
                self.engine.set_state(state)
                
                if eval > max_eval:
                    max_eval = eval
                    best_moves = [move]
                elif eval == max_eval:
                    best_moves.append(move)
                    
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            
            return max_eval, random.choice(best_moves) if best_moves else None
        else:
            min_eval = math.inf
            for move in moves:
                state = self.engine.get_state()
                
                self.engine.make_move(move[0], move[1])
                eval, _ = self.minimax(depth - 1, alpha, beta, True)
                
                self.engine.set_state(state)
                
                if eval < min_eval:
                    min_eval = eval
                    best_moves = [move]
                elif eval == min_eval:
                    best_moves.append(move)
                    
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            
            return min_eval, random.choice(best_moves) if best_moves else None
    
    def get_best_move(self):
        _, best_move = self.minimax(self.depth, -math.inf, math.inf, self.engine.turn == 'white')
        return best_move


class ChessGUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE + 150))
        pygame.display.set_caption("Chess Engine")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)
        
        self.engine = ChessEngine()
        self.ai = ChessAI(self.engine, depth=3)
        self.selected_piece = None
        self.valid_moves = []
        self.running = True
        self.ai_thinking = False
        self.game_over = False
        self.winner = None
        self.player_color = None
        self.piece_images = {}
        self.flipped = False
        
        if not os.path.exists('pieces'):
            os.makedirs('pieces')
        
        self.load_piece_images()
    
    def load_piece_images(self):
        pieces = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p']
        for piece in pieces:
            self.download_piece_image(piece)
    
    def download_piece_image(self, piece):
        prefix = 'w_' if piece.isupper() else 'b_'
        image_path = f'pieces/{prefix}{piece}.png'
        
        if os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path)
                self.piece_images[piece] = pygame.transform.scale(img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                return
            except:
                pass
        
        if piece in PNG_URLS:
            url = PNG_URLS[piece]
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    image_data = response.read()
                
                with open(image_path, 'wb') as f:
                    f.write(image_data)
                
                img = pygame.image.load(image_path)
                self.piece_images[piece] = pygame.transform.scale(img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                return
            except:
                pass
        
        self.create_fallback_image(piece, image_path)
    
    def create_fallback_image(self, piece, filename=None):
        size = SQUARE_SIZE - 10
        img = pygame.Surface((size, size), pygame.SRCALPHA)
        
        if piece.isupper():
            main_color = (255, 248, 220)
            dark_color = (200, 180, 140)
            outline_color = (80, 80, 80)
        else:
            main_color = (40, 40, 40)
            dark_color = (20, 20, 20)
            outline_color = (180, 180, 180)
        
        center = (size // 2, size // 2)
        radius = size // 3
        
        pygame.draw.circle(img, main_color, center, radius)
        pygame.draw.circle(img, outline_color, center, radius, 2)
        
        piece_type = piece.lower()
        
        if piece_type == 'p':
            pygame.draw.circle(img, dark_color, (center[0], center[1] - radius//2), radius//3)
        elif piece_type == 'n':
            pygame.draw.ellipse(img, main_color, (center[0] - radius//2, center[1] - radius//2, radius, radius))
            pygame.draw.rect(img, dark_color, (center[0] - radius//4, center[1] - radius//3, radius//2, radius//2))
        elif piece_type == 'b':
            points = [(center[0], center[1] - radius), (center[0] - radius//2, center[1] + radius//2), 
                     (center[0] + radius//2, center[1] + radius//2)]
            pygame.draw.polygon(img, main_color, points)
            pygame.draw.polygon(img, outline_color, points, 2)
        elif piece_type == 'r':
            pygame.draw.rect(img, main_color, (center[0] - radius, center[1] - radius, radius*2, radius*2))
            pygame.draw.rect(img, outline_color, (center[0] - radius, center[1] - radius, radius*2, radius*2), 2)
        elif piece_type == 'q':
            pygame.draw.circle(img, main_color, center, radius)
            pygame.draw.circle(img, outline_color, center, radius, 2)
            for i in range(-2, 3):
                pygame.draw.circle(img, dark_color, (center[0] + i * radius//3, center[1] - radius), 3)
        elif piece_type == 'k':
            pygame.draw.circle(img, main_color, center, radius)
            pygame.draw.circle(img, outline_color, center, radius, 2)
            pygame.draw.line(img, dark_color, (center[0], center[1] - radius), (center[0], center[1] + radius), 3)
            pygame.draw.line(img, dark_color, (center[0] - radius, center[1]), (center[0] + radius, center[1]), 3)
        
        self.piece_images[piece] = img
        
        if filename:
            try:
                pygame.image.save(img, filename)
            except:
                pass
    
    def choose_color(self):
        waiting = True
        while waiting:
            self.screen.fill(LIGHT_BROWN)
            
            title = self.big_font.render("Choose Color", True, BLACK)
            title_rect = title.get_rect(center=(BOARD_SIZE // 2, 200))
            self.screen.blit(title, title_rect)
            
            white_btn = pygame.Rect(BOARD_SIZE // 2 - 100, 300, 200, 50)
            pygame.draw.rect(self.screen, WHITE, white_btn)
            pygame.draw.rect(self.screen, BLACK, white_btn, 3)
            white_text = self.font.render("Play as White", True, BLACK)
            white_rect = white_text.get_rect(center=white_btn.center)
            self.screen.blit(white_text, white_rect)
            
            black_btn = pygame.Rect(BOARD_SIZE // 2 - 100, 380, 200, 50)
            pygame.draw.rect(self.screen, BLACK, black_btn)
            pygame.draw.rect(self.screen, WHITE, black_btn, 3)
            black_text = self.font.render("Play as Black", True, WHITE)
            black_rect = black_text.get_rect(center=black_btn.center)
            self.screen.blit(black_text, black_rect)
            
            pygame.display.flip()
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if white_btn.collidepoint(event.pos):
                        self.player_color = 'white'
                        self.flipped = False
                        waiting = False
                    elif black_btn.collidepoint(event.pos):
                        self.player_color = 'black'
                        self.flipped = True
                        waiting = False
        
        if self.player_color == 'black':
            self.ai_thinking = True
        
        return True
    
    def draw_board(self):
        for row in range(8):
            for col in range(8):
                display_row = 7 - row if self.flipped else row
                display_col = 7 - col if self.flipped else col
                color = LIGHT_BROWN if (display_row + display_col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(self.screen, color, 
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))
        
        for i in range(8):
            display_i = 7 - i if self.flipped else i
            letter = chr(ord('a') + display_i)
            text_color = BLACK if (7 + i) % 2 == 0 else WHITE
            text = self.small_font.render(letter, True, text_color)
            self.screen.blit(text, (i * SQUARE_SIZE + 5, BOARD_SIZE - 20))
            
            display_number = i + 1 if self.flipped else 8 - i
            number = str(display_number)
            text_color = BLACK if (i + 0) % 2 == 0 else WHITE
            text = self.small_font.render(number, True, text_color)
            self.screen.blit(text, (5, i * SQUARE_SIZE + 5))
        
        if self.engine.last_move:
            for pos in self.engine.last_move:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                s.set_alpha(100)
                s.fill(LAST_MOVE_COLOR)
                row, col = pos
                display_row = 7 - row if self.flipped else row
                display_col = 7 - col if self.flipped else col
                self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))
        
        if self.selected_piece:
            row, col = self.selected_piece
            display_row = 7 - row if self.flipped else row
            display_col = 7 - col if self.flipped else col
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(HIGHLIGHT)
            self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))
        
        for move in self.valid_moves:
            row, col = move
            display_row = 7 - row if self.flipped else row
            display_col = 7 - col if self.flipped else col
            center = (display_col * SQUARE_SIZE + SQUARE_SIZE // 2, display_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(self.screen, GREEN, center, SQUARE_SIZE // 6)
        
        if self.engine.is_in_check(self.engine.turn):
            king_pos = self.engine.find_king(self.engine.board, self.engine.turn)
            if king_pos:
                row, col = king_pos
                display_row = 7 - row if self.flipped else row
                display_col = 7 - col if self.flipped else col
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                s.set_alpha(150)
                s.fill(CHECK_COLOR)
                self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))
        
        for row in range(8):
            for col in range(8):
                piece = self.engine.board[row][col]
                if piece != '.' and piece in self.piece_images:
                    img = self.piece_images[piece]
                    display_row = 7 - row if self.flipped else row
                    display_col = 7 - col if self.flipped else col
                    x = display_col * SQUARE_SIZE + (SQUARE_SIZE - img.get_width()) // 2
                    y = display_row * SQUARE_SIZE + (SQUARE_SIZE - img.get_height()) // 2
                    self.screen.blit(img, (x, y))
        
        y_offset = BOARD_SIZE + 10
        
        if not self.game_over:
            turn_text = f"Turn: {'White' if self.engine.turn == 'white' else 'Black'}"
            turn_color = WHITE if self.engine.turn == 'white' else BLACK
            turn_surface = self.big_font.render(turn_text, True, turn_color)
            self.screen.blit(turn_surface, (20, y_offset + 5))
        else:
            if self.winner == 'white':
                win_text = "White wins!"
                win_color = WHITE
            elif self.winner == 'black':
                win_text = "Black wins!"
                win_color = BLACK
            else:
                win_text = "Stalemate!"
                win_color = GRAY
            
            win_surface = self.big_font.render(win_text, True, win_color)
            win_rect = win_surface.get_rect(topleft=(20, y_offset + 5))
            pygame.draw.rect(self.screen, DARK_BROWN, win_rect.inflate(10, 5))
            pygame.draw.rect(self.screen, BLACK, win_rect.inflate(10, 5), 2)
            self.screen.blit(win_surface, (20, y_offset + 5))
        
        if self.ai_thinking:
            thinking_text = self.small_font.render("AI thinking...", True, BLUE)
            self.screen.blit(thinking_text, (20, y_offset + 35))
        
        flip_btn = pygame.Rect(BOARD_SIZE - 250, y_offset + 5, 70, 35)
        pygame.draw.rect(self.screen, BLUE, flip_btn)
        pygame.draw.rect(self.screen, BLACK, flip_btn, 2)
        flip_text = self.small_font.render("Flip", True, WHITE)
        flip_rect = flip_text.get_rect(center=flip_btn.center)
        self.screen.blit(flip_text, flip_rect)
        
        restart_btn = pygame.Rect(BOARD_SIZE - 170, y_offset + 5, 70, 35)
        pygame.draw.rect(self.screen, DARK_BROWN, restart_btn)
        pygame.draw.rect(self.screen, BLACK, restart_btn, 2)
        restart_text = self.small_font.render("Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=restart_btn.center)
        self.screen.blit(restart_text, restart_rect)
        
        resign_btn = pygame.Rect(BOARD_SIZE - 90, y_offset + 5, 70, 35)
        pygame.draw.rect(self.screen, RED, resign_btn)
        pygame.draw.rect(self.screen, BLACK, resign_btn, 2)
        resign_text = self.small_font.render("Resign", True, WHITE)
        resign_rect = resign_text.get_rect(center=resign_btn.center)
        self.screen.blit(resign_text, resign_rect)
        
        white_material, black_material = self.engine.get_material_value()
        panel_rect = pygame.Rect(10, y_offset + 50, BOARD_SIZE - 20, 40)
        pygame.draw.rect(self.screen, GRAY, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)
        
        diff = white_material - black_material
        if diff > 0:
            material_text = f"White: {white_material}  Black: {black_material}  (+{diff})"
            diff_color = WHITE
        elif diff < 0:
            material_text = f"White: {white_material}  Black: {black_material}  ({diff})"
            diff_color = BLACK
        else:
            material_text = f"White: {white_material}  Black: {black_material}  (=)"
            diff_color = (200, 200, 0)
        
        material_surface = self.small_font.render(material_text, True, diff_color)
        material_rect = material_surface.get_rect(center=(BOARD_SIZE // 2, y_offset + 70))
        self.screen.blit(material_surface, material_rect)
        
        return {'flip': flip_btn, 'restart': restart_btn, 'resign': resign_btn}
    
    def show_promotion_menu(self):
        menu_rect = pygame.Rect(BOARD_SIZE // 2 - 100, BOARD_SIZE // 2 - 100, 200, 200)
        pygame.draw.rect(self.screen, LIGHT_BROWN, menu_rect)
        pygame.draw.rect(self.screen, BLACK, menu_rect, 3)
        
        pieces = [('q', 'Queen'), ('r', 'Rook'), ('n', 'Knight'), ('b', 'Bishop')]
        buttons = []
        
        for i, (piece, name) in enumerate(pieces):
            btn = pygame.Rect(menu_rect.x + 10, menu_rect.y + 10 + i * 45, 180, 40)
            pygame.draw.rect(self.screen, DARK_BROWN, btn)
            
            piece_key = piece.upper() if self.engine.turn == 'white' else piece
            if piece_key in self.piece_images:
                img = pygame.transform.scale(self.piece_images[piece_key], (30, 30))
                self.screen.blit(img, (btn.x + 10, btn.y + 5))
            
            text = self.font.render(name, True, WHITE)
            self.screen.blit(text, (btn.x + 50, btn.y + 10))
            buttons.append((btn, piece))
        
        pygame.display.flip()
        
        while True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn, piece in buttons:
                        if btn.collidepoint(event.pos):
                            return piece
                elif event.type == pygame.QUIT:
                    return 'q'
    
    def handle_click(self, pos):
        if self.game_over or self.engine.turn != self.player_color or self.ai_thinking:
            return True
        
        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE
        
        if not (0 <= row < 8 and 0 <= col < 8):
            return True
        
        actual_row = 7 - row if self.flipped else row
        actual_col = 7 - col if self.flipped else col
        
        if self.selected_piece is None:
            piece = self.engine.board[actual_row][actual_col]
            if piece != '.' and self.engine.get_piece_color(piece) == self.engine.turn:
                self.selected_piece = (actual_row, actual_col)
                moves = self.engine.get_piece_moves(actual_row, actual_col)
                self.valid_moves = [move for move in moves if self.engine.is_move_legal((actual_row, actual_col), move)]
        else:
            if (actual_row, actual_col) in self.valid_moves:
                start = self.selected_piece
                end = (actual_row, actual_col)
                piece = self.engine.board[start[0]][start[1]]
                
                if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
                    promotion = self.show_promotion_menu()
                    self.engine.make_move(start, end, promotion)
                else:
                    self.engine.make_move(start, end)
                
                self.selected_piece = None
                self.valid_moves = []
                
                if self.engine.is_checkmate():
                    self.game_over = True
                    self.winner = 'black' if self.engine.turn == 'white' else 'white'
                elif self.engine.is_stalemate():
                    self.game_over = True
                    self.winner = None
                else:
                    self.ai_thinking = True
            else:
                self.selected_piece = None
                self.valid_moves = []
        
        return True
    
    def resign(self):
        if not self.game_over:
            self.game_over = True
            self.winner = 'black' if self.player_color == 'white' else 'white'
            self.ai_thinking = False
    
    def ai_move(self):
        if self.game_over or self.engine.turn == self.player_color:
            self.ai_thinking = False
            return
        
        self.ai_thinking = True
        
        move = self.ai.get_best_move()
        
        if move:
            start, end = move
            piece = self.engine.board[start[0]][start[1]]
            promotion = 'q'
            if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
                promotion = 'q'
            
            self.engine.make_move(start, end, promotion)
            
            if self.engine.is_checkmate():
                self.game_over = True
                self.winner = 'black' if self.engine.turn == 'white' else 'white'
            elif self.engine.is_stalemate():
                self.game_over = True
                self.winner = None
        
        self.ai_thinking = False
    
    def restart_game(self):
        self.engine = ChessEngine()
        self.ai = ChessAI(self.engine, depth=3)
        self.selected_piece = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        self.ai_thinking = False
        
        if self.player_color == 'black':
            self.ai_thinking = True
    
    def run(self):
        if not self.choose_color():
            return
        
        running = True
        
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if hasattr(self, 'buttons'):
                        if self.buttons['flip'].collidepoint(event.pos):
                            self.flipped = not self.flipped
                        elif self.buttons['restart'].collidepoint(event.pos):
                            self.restart_game()
                        elif self.buttons['resign'].collidepoint(event.pos):
                            self.resign()
                        elif event.pos[1] < BOARD_SIZE:
                            self.handle_click(event.pos)
            
            if not self.game_over and self.ai_thinking:
                self.ai_move()
            
            self.buttons = self.draw_board()
            pygame.display.flip()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = ChessGUI()
    game.run()
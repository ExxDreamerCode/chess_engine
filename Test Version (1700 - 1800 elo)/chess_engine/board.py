import copy
from .constants import PIECE_VALUES, PAWN_TABLE, PAWN_ENDGAME_TABLE, KNIGHT_TABLE, BISHOP_TABLE, ROOK_TABLE, QUEEN_TABLE, KING_TABLE_MIDDLE, KING_TABLE_END, KING_ACTIVITY_TABLE


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
        self.tactical_cache = {}

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

    def is_in_check(self, color=None):
        if color is None:
            color = self.turn
        king_pos = self.find_king(self.board, color)
        if not king_pos:
            return False
        opponent_color = 'black' if color == 'white' else 'white'
        return self.is_square_attacked((king_pos[0], king_pos[1]), opponent_color)

    def find_king(self, board, color):
        target = 'K' if color == 'white' else 'k'
        for row in range(8):
            for col in range(8):
                if board[row][col] == target:
                    return (row, col)
        return None

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
                new_row2 = row + 2 * direction
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
                    new_r, new_c = row + dr * step, col + dc * step
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

    def is_move_check(self, start, end):
        temp_board = [row[:] for row in self.board]
        piece = temp_board[start[0]][start[1]]
        temp_board[end[0]][end[1]] = piece
        temp_board[start[0]][start[1]] = '.'
        opponent_color = 'black' if self.get_piece_color(piece) == 'white' else 'white'
        king_char = 'K' if opponent_color == 'white' else 'k'
        king_pos = None
        for r in range(8):
            for c in range(8):
                if temp_board[r][c] == king_char:
                    king_pos = (r, c)
                    break
            if king_pos:
                break
        if not king_pos:
            return False
        return self.is_square_attacked_on_board(temp_board, king_pos[0], king_pos[1],
                                               self.get_piece_color(piece))

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
            self.tactical_cache.clear()

    def is_checkmate(self):
        if not self.is_in_check(self.turn):
            return False
        return len(self.get_all_legal_moves()) == 0

    def is_stalemate(self):
        if self.is_in_check(self.turn):
            return False
        return len(self.get_all_legal_moves()) == 0

    def is_threefold_repetition(self):
        white_score, black_score = self.get_material_value()
        material_adv = abs(white_score - black_score)
        eval_adv = abs(self.evaluate_board())
        if material_adv > 100 or eval_adv > 100:
            return False
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

    def is_draw(self, advantage_tolerance=100):
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

    def evaluate_board_quick(self):
        score = 0
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.':
                    score += PIECE_VALUES[piece]
        return score

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

    def evaluate_tactical_complexity(self):
        white_val, black_val = self.get_material_value()
        if abs(white_val - black_val) > 800:
            return 0
        board_hash = self.get_board_hash()
        if board_hash in self.tactical_cache:
            return self.tactical_cache[board_hash]
        score = 0
        current_color = self.turn
        threats = self.calculate_tactical_threats(current_color)
        forks = self.calculate_forks(current_color)
        traps = self.calculate_piece_traps(current_color)
        score += threats
        score += forks
        score += traps
        opponent_color = 'black' if current_color == 'white' else 'white'
        opponent_threats = self.calculate_tactical_threats(opponent_color)
        opponent_forks = self.calculate_forks(opponent_color)
        opponent_traps = self.calculate_piece_traps(opponent_color)
        score -= opponent_threats * 0.7
        score -= opponent_forks * 0.8
        score -= opponent_traps * 0.6
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == current_color:
                    if piece.lower() != 'k':
                        is_defended = False
                        for r2 in range(8):
                            for c2 in range(8):
                                defender = self.board[r2][c2]
                                if defender != '.' and self.get_piece_color(defender) == current_color:
                                    if (r2, c2) != (row, col):
                                        if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                            is_defended = True
                                            break
                                    if is_defended:
                                        break
                        if not is_defended:
                            piece_value = abs(PIECE_VALUES.get(piece, 0))
                            score -= piece_value * 0.15
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == opponent_color:
                    if piece.lower() != 'k':
                        is_defended = False
                        for r2 in range(8):
                            for c2 in range(8):
                                defender = self.board[r2][c2]
                                if defender != '.' and self.get_piece_color(defender) == opponent_color:
                                    if (r2, c2) != (row, col):
                                        if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                            is_defended = True
                                            break
                                    if is_defended:
                                        break
                        if not is_defended:
                            piece_value = abs(PIECE_VALUES.get(piece, 0))
                            score += piece_value * 0.15
        self.tactical_cache[board_hash] = score
        return score

    def calculate_tactical_threats(self, color):
        threats = 0
        opponent_color = 'black' if color == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == color:
                    piece_value = abs(PIECE_VALUES.get(piece, 0))
                    moves = self.get_piece_moves(row, col)
                    attacked_pieces = []
                    defended_pieces = []
                    for move in moves:
                        target = self.board[move[0]][move[1]]
                        if target != '.' and self.get_piece_color(target) == opponent_color:
                            target_value = abs(PIECE_VALUES.get(target, 0))
                            is_defended = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    defender = self.board[r2][c2]
                                    if defender != '.' and self.get_piece_color(defender) == opponent_color:
                                        if self.can_piece_attack_on_board(r2, c2, move[0], move[1], self.board):
                                            is_defended = True
                                            break
                                    if is_defended:
                                        break
                            if is_defended:
                                defended_pieces.append((target_value, target, move))
                            else:
                                attacked_pieces.append((target_value, target, move))
                    for target_value, target, move in attacked_pieces:
                        if piece_value <= target_value:
                            threats += target_value - piece_value + 50
                        else:
                            threats += 30
                    for target_value, target, move in defended_pieces:
                        if piece_value < target_value:
                            has_protection = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    protector = self.board[r2][c2]
                                    if protector != '.' and self.get_piece_color(protector) == color:
                                        if (r2, c2) != (row, col):
                                            if self.can_piece_attack_on_board(r2, c2, move[0], move[1], self.board):
                                                protector_value = abs(PIECE_VALUES.get(protector, 0))
                                                if protector_value <= target_value:
                                                    has_protection = True
                                                    break
                                    if has_protection:
                                        break
                            if not has_protection:
                                threats -= (target_value - piece_value) * 2
        return threats

    def calculate_forks(self, color):
        forks = 0
        opponent_color = 'black' if color == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == color:
                    piece_type = piece.lower()
                    if piece_type == 'n':
                        knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                       (1, -2), (1, 2), (2, -1), (2, 1)]
                        attacked_targets = []
                        for dr, dc in knight_moves:
                            new_r, new_c = row + dr, col + dc
                            if 0 <= new_r < 8 and 0 <= new_c < 8:
                                target = self.board[new_r][new_c]
                                if target != '.' and self.get_piece_color(target) == opponent_color:
                                    target_value = abs(PIECE_VALUES.get(target, 0))
                                    attacked_targets.append(target_value)
                        if len(attacked_targets) >= 2:
                            is_knight_defended = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    defender = self.board[r2][c2]
                                    if defender != '.' and self.get_piece_color(defender) == color:
                                        if (r2, c2) != (row, col):
                                            if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                                is_knight_defended = True
                                                break
                                if is_knight_defended:
                                    break
                            fork_value = sum(sorted(attacked_targets, reverse=True)[:2])
                            if is_knight_defended:
                                forks += fork_value * 2
                            else:
                                forks += fork_value * 0.5
                    elif piece_type == 'p':
                        direction = -1 if color == 'white' else 1
                        attacked_targets = []
                        for dc in [-1, 1]:
                            new_r, new_c = row + direction, col + dc
                            if 0 <= new_r < 8 and 0 <= new_c < 8:
                                target = self.board[new_r][new_c]
                                if target != '.' and self.get_piece_color(target) == opponent_color:
                                    target_value = abs(PIECE_VALUES.get(target, 0))
                                    attacked_targets.append(target_value)
                        if len(attacked_targets) >= 2:
                            is_pawn_defended = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    defender = self.board[r2][c2]
                                    if defender != '.' and self.get_piece_color(defender) == color:
                                        if defender.lower() == 'p' and abs(r2 - row) == 1 and abs(c2 - col) == 1:
                                            is_pawn_defended = True
                                            break
                                        elif (r2, c2) != (row, col):
                                            if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                                is_pawn_defended = True
                                                break
                                if is_pawn_defended:
                                    break
                            if is_pawn_defended:
                                forks += 150
                            else:
                                forks += 75
                        elif len(attacked_targets) == 1 and attacked_targets[0] >= 500:
                            is_pawn_defended = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    defender = self.board[r2][c2]
                                    if defender != '.' and self.get_piece_color(defender) == color:
                                        if defender.lower() == 'p' and abs(r2 - row) == 1 and abs(c2 - col) == 1:
                                            is_pawn_defended = True
                                            break
                                        elif (r2, c2) != (row, col):
                                            if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                                is_pawn_defended = True
                                                break
                                if is_pawn_defended:
                                    break
                            if is_pawn_defended:
                                forks += 80
                            else:
                                forks += 40
                    elif piece_type in ['q', 'r', 'b']:
                        directions = []
                        if piece_type == 'b':
                            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
                        elif piece_type == 'r':
                            directions = [(-1, 0), (1, 0), (0, -1), (0, 1)]
                        else:
                            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1),
                                         (-1, 0), (1, 0), (0, -1), (0, 1)]
                        attacked_positions = []
                        for dr, dc in directions:
                            for step in range(1, 8):
                                new_r, new_c = row + dr * step, col + dc * step
                                if not (0 <= new_r < 8 and 0 <= new_c < 8):
                                    break
                                target = self.board[new_r][new_c]
                                if target != '.':
                                    if self.get_piece_color(target) == opponent_color:
                                        target_value = abs(PIECE_VALUES.get(target, 0))
                                        attacked_positions.append((target_value, (new_r, new_c)))
                                    break
                                else:
                                    attacked_positions.append((0, (new_r, new_c)))
                        valuable_targets = [v for v, pos in attacked_positions if v >= 300]
                        if len(valuable_targets) >= 2:
                            forks += sum(valuable_targets[:2]) * 1.5
                        elif len(valuable_targets) == 1:
                            forks += valuable_targets[0] * 0.5
        return forks

    def calculate_piece_traps(self, color):
        traps = 0
        opponent_color = 'black' if color == 'white' else 'white'
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece != '.' and self.get_piece_color(piece) == opponent_color:
                    piece_type = piece.lower()
                    piece_value = abs(PIECE_VALUES.get(piece, 0))
                    if piece_type in ['q', 'r', 'n', 'b']:
                        escape_squares = []
                        moves = self.get_piece_moves(row, col)
                        for move in moves:
                            new_r, new_c = move
                            is_attacked = False
                            for r2 in range(8):
                                for c2 in range(8):
                                    attacker = self.board[r2][c2]
                                    if attacker != '.' and self.get_piece_color(attacker) == color:
                                        if self.can_piece_attack_on_board(r2, c2, new_r, new_c, self.board):
                                            is_attacked = True
                                            break
                                if is_attacked:
                                    break
                            if not is_attacked:
                                escape_squares.append(move)
                        if len(escape_squares) == 0:
                            traps += piece_value * 0.8
                        elif len(escape_squares) == 1:
                            traps += piece_value * 0.3
                        attackers_count = 0
                        for r2 in range(8):
                            for c2 in range(8):
                                attacker = self.board[r2][c2]
                                if attacker != '.' and self.get_piece_color(attacker) == color:
                                    if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                        attackers_count += 1
                        defenders_count = 0
                        for r2 in range(8):
                            for c2 in range(8):
                                defender = self.board[r2][c2]
                                if defender != '.' and self.get_piece_color(defender) == opponent_color:
                                    if defender.lower() != 'k':
                                        if self.can_piece_attack_on_board(r2, c2, row, col, self.board):
                                            defenders_count += 1
                        if attackers_count > defenders_count:
                            traps += (attackers_count - defenders_count) * piece_value * 0.5
        return traps

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
                        pos_score = -PAWN_ENDGAME_TABLE[7 - row][col]
                    else:
                        pos_score = -PAWN_TABLE[7 - row][col]
                elif piece == 'N':
                    pos_score = KNIGHT_TABLE[row][col]
                elif piece == 'n':
                    pos_score = -KNIGHT_TABLE[7 - row][col]
                elif piece == 'B':
                    pos_score = BISHOP_TABLE[row][col]
                elif piece == 'b':
                    pos_score = -BISHOP_TABLE[7 - row][col]
                elif piece == 'R':
                    pos_score = ROOK_TABLE[row][col]
                elif piece == 'r':
                    pos_score = -ROOK_TABLE[7 - row][col]
                elif piece == 'Q':
                    pos_score = QUEEN_TABLE[row][col]
                elif piece == 'q':
                    pos_score = -QUEEN_TABLE[7 - row][col]
                elif piece == 'K':
                    pos_score = KING_TABLE_END[row][col] if is_endgame else KING_TABLE_MIDDLE[row][col]
                    if is_endgame:
                        pos_score += KING_ACTIVITY_TABLE[row][col]
                elif piece == 'k':
                    pos_score = -KING_TABLE_END[7 - row][col] if is_endgame else -KING_TABLE_MIDDLE[7 - row][col]
                    if is_endgame:
                        pos_score -= KING_ACTIVITY_TABLE[7 - row][col]
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
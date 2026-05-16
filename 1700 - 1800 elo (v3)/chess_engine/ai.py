import math
import random
import time
from .constants import PIECE_VALUES, transposition_table
from .board import ChessEngine
from opening_book import find_book_moves


class ChessAI:
    def __init__(self, engine, depth=4):
        self.engine = engine
        self.depth = depth
        self.nodes_searched = 0
        self.killer_moves = [[None, None] for _ in range(64)]
        self.history_table = {}
        self.max_mate_depth = 10
        self.rep_penalty = 10000
        self.time_limit = None
        self.start_time = None
        self.hard_limit = None

    def is_time_up(self):
        if self.time_limit is None:
            return False
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) > self.time_limit

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

    def quiescence_search(self, alpha, beta, maximizing, depth_remaining=4, in_check=False):
        if self.is_time_up():
            return self.engine.evaluate_board(), None
        if depth_remaining < -8:
            return self.engine.evaluate_board(), None
        stand_pat = self.engine.evaluate_board()
        if depth_remaining <= 0 and not in_check:
            return stand_pat, None
        if in_check:
            all_moves = self.engine.get_all_legal_moves()
            if not all_moves:
                if self.engine.is_in_check(self.engine.turn):
                    return -100000 - depth_remaining if maximizing else 100000 + depth_remaining, None
                return 0, None

            def move_priority(move):
                start, end = move
                score = 0
                target = self.engine.board[end[0]][end[1]]
                if target != '.':
                    victim_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900}
                    score += victim_values.get(target.lower(), 0) * 10
                if self.engine.is_move_check(start, end):
                    score += 5000
                piece = self.engine.board[start[0]][start[1]]
                if piece.lower() == 'n':
                    for r in range(8):
                        for c in range(8):
                            target_piece = self.engine.board[r][c]
                            if target_piece != '.' and self.engine.get_piece_color(target_piece) != self.engine.get_piece_color(piece):
                                if self.engine.can_piece_attack_on_board(start[0], start[1], r, c, self.engine.board):
                                    score += 300
                move_key = (start, end)
                if move_key in self.history_table:
                    score += min(self.history_table[move_key], 500)
                return score

            all_moves.sort(key=move_priority, reverse=True)
            if maximizing:
                for move in all_moves[:20]:
                    if self.is_time_up():
                        break
                    if not self.engine.is_move_legal(move[0], move[1]):
                        continue
                    state = self.engine.get_state()
                    self.engine.make_move(move[0], move[1], record_history=False)
                    is_still_check = self.engine.is_in_check(self.engine.turn)
                    score, _ = self.quiescence_search(alpha, beta, not maximizing,
                                                      depth_remaining - 1, is_still_check)
                    self.engine.set_state(state)
                    if score >= beta:
                        return beta, None
                    if score > alpha:
                        alpha = score
                return alpha, None
            else:
                for move in all_moves[:20]:
                    if self.is_time_up():
                        break
                    if not self.engine.is_move_legal(move[0], move[1]):
                        continue
                    state = self.engine.get_state()
                    self.engine.make_move(move[0], move[1], record_history=False)
                    is_still_check = self.engine.is_in_check(self.engine.turn)
                    score, _ = self.quiescence_search(alpha, beta, not maximizing,
                                                      depth_remaining - 1, is_still_check)
                    self.engine.set_state(state)
                    if score <= alpha:
                        return alpha, None
                    if score < beta:
                        beta = score
                return beta, None
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
        tactical_moves = []
        for row in range(8):
            for col in range(8):
                piece = self.engine.board[row][col]
                if piece != '.' and self.engine.get_piece_color(piece) == self.engine.turn:
                    moves = self.engine.get_piece_moves(row, col)
                    for move in moves:
                        target = self.engine.board[move[0]][move[1]]
                        if target != '.' and self.engine.get_piece_color(target) != self.engine.turn:
                            tactical_moves.append(((row, col), move, 'capture'))
                        elif self.engine.is_move_check((row, col), move):
                            tactical_moves.append(((row, col), move, 'check'))
                        elif piece.lower() == 'n':
                            fork_potential = 0
                            knight_moves = [(-2, -1), (-2, 1), (-1, -2), (-1, 2),
                                           (1, -2), (1, 2), (2, -1), (2, 1)]
                            for dr, dc in knight_moves:
                                new_r, new_c = move[0] + dr, move[1] + dc
                                if 0 <= new_r < 8 and 0 <= new_c < 8:
                                    target_piece = self.engine.board[new_r][new_c]
                                    if target_piece != '.' and self.engine.get_piece_color(target_piece) != self.engine.get_piece_color(piece):
                                        target_value = abs(PIECE_VALUES.get(target_piece, 0))
                                        if target_value >= 300:
                                            fork_potential += target_value
                            if fork_potential >= 600:
                                tactical_moves.append(((row, col), move, 'fork'))
        if not tactical_moves:
            return stand_pat, None

        def move_priority(tactical_move):
            start, end, move_type = tactical_move
            score = 0
            if move_type == 'capture':
                victim = self.engine.board[end[0]][end[1]].lower()
                attacker = self.engine.board[start[0]][start[1]].lower()
                victim_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900}
                attacker_values = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900}
                score = victim_values.get(victim, 0) - attacker_values.get(attacker, 0) // 10
            elif move_type == 'check':
                score = 500
            elif move_type == 'fork':
                score = 800
            move_key = (start, end)
            if move_key in self.history_table:
                score += min(self.history_table[move_key], 500)
            return score

        tactical_moves.sort(key=move_priority, reverse=True)
        if depth_remaining <= 2:
            tactical_moves = tactical_moves[:8]
        elif depth_remaining <= 3:
            tactical_moves = tactical_moves[:12]
        else:
            tactical_moves = tactical_moves[:15]
        for start, end, move_type in tactical_moves:
            if self.is_time_up():
                break
            if not self.engine.is_move_legal(start, end):
                continue
            state = self.engine.get_state()
            self.engine.make_move(start, end, record_history=False)
            is_check = self.engine.is_in_check(self.engine.turn)
            score, _ = self.quiescence_search(alpha, beta, not maximizing,
                                              depth_remaining - 1, is_check)
            self.engine.set_state(state)
            if maximizing:
                if score >= beta:
                    return beta, None
                if score > alpha:
                    alpha = score
            else:
                if score <= alpha:
                    return alpha, None
                if score < beta:
                    beta = score
        return alpha if maximizing else beta, None

    def minimax(self, depth, alpha, beta, maximizing):
        if self.is_time_up():
            return (0, None) if maximizing else (0, None)
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
            in_check = self.engine.is_in_check(self.engine.turn)
            if self.depth >= 5:
                qs_depth = 4
            elif self.depth >= 3:
                qs_depth = 3
            else:
                qs_depth = 4
            q_score, _ = self.quiescence_search(alpha, beta, maximizing, depth_remaining=qs_depth, in_check=in_check)
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
        
        REPETITION_PENALTY_THRESHOLD = 50
        if maximizing:
            max_eval = -math.inf
            for i, move in enumerate(moves):
                if self.is_time_up():
                    break
                state = self.engine.get_state()
                self.engine.make_move(move[0], move[1], record_history=True)
                eval_penalty = 0
                if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 1:
                    if current_advantage >= REPETITION_PENALTY_THRESHOLD:
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
                if self.is_time_up():
                    break
                state = self.engine.get_state()
                self.engine.make_move(move[0], move[1], record_history=True)
                eval_penalty = 0
                if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 1:
                    if current_advantage >= REPETITION_PENALTY_THRESHOLD:
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
                if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 1:
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
                    if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 1:
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
        TIME_LIMIT = self.time_limit if self.time_limit is not None else 5.0
        best_moves_same_score = []
        search_depth = self.depth
        best_minimax_move = None
        best_minimax_score = -math.inf if our_color == 'white' else math.inf
        for depth in range(1, search_depth + 1):
            if self.is_time_up():
                break
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
                    if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 1:
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
                    if self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 1:
                        score += 200
                    self.engine.set_state(state)
                    if score < best_score:
                        best_moves_same_score = [move]
                        best_score = score
                    elif abs(score - best_score) < 15:
                        best_moves_same_score.append(move)
                    best_move = move
                    best_minimax_score = score
            if self.is_time_up():
                break
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
            temp_state = self.engine.get_state()
            self.engine.make_move(best_move[0], best_move[1], record_history=True)
            leads_to_repetition = self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2
            self.engine.set_state(temp_state)
            SHOULD_AVOID_REPETITION_THRESHOLD = 200
            if leads_to_repetition and current_advantage >= SHOULD_AVOID_REPETITION_THRESHOLD:
                found_alternative = False
                if len(best_moves_same_score) > 1:
                    for move in best_moves_same_score:
                        if move == best_move:
                            continue
                        self.engine.set_state(temp_state)
                        self.engine.make_move(move[0], move[1], record_history=True)
                        is_rep = self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2
                        self.engine.set_state(temp_state)
                        if not is_rep and self.is_move_safe(move):
                            best_move = move
                            found_alternative = True
                            break
                if not found_alternative:
                    for move in all_legal_moves:
                        if move == best_move:
                            continue
                        self.engine.set_state(temp_state)
                        self.engine.make_move(move[0], move[1], record_history=True)
                        is_rep = self.engine.position_history.get(self.engine.get_board_hash(), 0) >= 2
                        self.engine.set_state(temp_state)
                        if not is_rep and self.is_move_safe(move):
                            self.engine.set_state(temp_state)
                            self.engine.make_move(move[0], move[1], record_history=False)
                            approx_score = self.engine.evaluate_board_quick()
                            self.engine.set_state(temp_state)
                            if (self.engine.turn == 'white' and approx_score >= current_advantage - 150) or \
                               (self.engine.turn == 'black' and approx_score <= current_advantage + 150):
                                best_move = move
                                found_alternative = True
                                break
            move_key = (best_move[0], best_move[1])
            self.history_table[move_key] = self.history_table.get(move_key, 0) + self.depth ** 2
        self.time_limit = None
        self.start_time = None
        return best_move
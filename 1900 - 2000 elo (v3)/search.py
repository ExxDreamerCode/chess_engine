import sys
import time
from board import Board
from evaluation import Evaluation
from transposition import TranspositionTable, TT_EXACT, TT_ALPHA, TT_BETA, compute_zobrist_key

MAX_PLY = 128
MATE_SCORE = 100000
INFINITY = 1000000
ASPIRATION = 50
DEFAULT_TIME_LIMIT = 5.0

REP_DRAW_SCORE = 0
REP_PENALTY = 80000


class Search:
    def __init__(self, board: Board):
        self.board = board
        self.eval = Evaluation(board)
        self.tt = TranspositionTable(64)

        self.nodes = 0
        self.start_time = 0.0
        self.time_limit = DEFAULT_TIME_LIMIT
        self.stopped = False

        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = {}
        self.pv_table = [[None] * MAX_PLY for _ in range(MAX_PLY)]
        self.pv_length = [0] * MAX_PLY

    def set_position(self, board: Board):
        self.board = board
        self.eval.board = board

    def _position_hash_after_move(self, move):
        state = self.board.get_state()
        self.board.make_move(move[0], move[1], record_history=False)
        h = self.board.get_board_hash()
        self.board.set_state(state)
        return h

    def _move_leads_to_repetition(self, move):
        h = self._position_hash_after_move(move)
        return self.board.position_history.get(h, 0) >= 2

    def get_best_move(self, time_limit=DEFAULT_TIME_LIMIT, depth_limit=64):
        self.nodes = 0
        self.start_time = time.time()
        self.time_limit = time_limit
        self.stopped = False
        self.killers = [[None, None] for _ in range(MAX_PLY)]
        self.history = {}
        self.tt.new_write = False

        moves = self.board.get_all_legal_moves()
        if not moves:
            return None

        non_rep_moves = [m for m in moves if not self._move_leads_to_repetition(m)]
        rep_moves = [m for m in moves if self._move_leads_to_repetition(m)]

        candidate_moves = non_rep_moves if non_rep_moves else moves

        best_move = candidate_moves[0]
        best_score = -INFINITY

        tt_key = compute_zobrist_key(
            self.board.board, self.board.turn,
            self.board.en_passant_target, self.board.castling_rights
        )
        tt_entry = self.tt.get(tt_key)
        if tt_entry and tt_entry.get('best_move') in candidate_moves:
            best_move = tt_entry['best_move']

        alpha = -INFINITY
        beta = INFINITY

        for depth in range(1, depth_limit + 1):
            if time.time() - self.start_time > self.time_limit * 0.75:
                break

            self.nodes = 0
            self.pv_length = [0] * MAX_PLY

            if depth >= 4 and best_score != -INFINITY:
                window = ASPIRATION * depth
                alpha = best_score - window
                beta = best_score + window
            else:
                alpha = -INFINITY
                beta = INFINITY

            score = self.negamax(depth, 0, alpha, beta)

            if self.stopped:
                break

            if score <= alpha or score >= beta:
                alpha = -INFINITY
                beta = INFINITY
                score = self.negamax(depth, 0, alpha, beta)
                if self.stopped:
                    break

            pv_move = self.pv_table[0][0]
            if pv_move and pv_move in moves:
                if non_rep_moves:
                    if pv_move in non_rep_moves:
                        best_move = pv_move
                        best_score = score
                else:
                    best_move = pv_move
                    best_score = score

            self._print_uci_info(depth, score, pv_move)

            if time.time() - self.start_time > self.time_limit * 0.95:
                break

            if abs(score) > MATE_SCORE - 100:
                break

        if best_move not in moves:
            return moves[0]
        return best_move

    def negamax(self, depth, ply, alpha, beta):
        if self.nodes % 1024 == 0:
            if time.time() - self.start_time > self.time_limit:
                self.stopped = True
                return 0
        self.nodes += 1

        if self.board.is_threefold_repetition():
            return REP_DRAW_SCORE

        in_check = self.board.is_in_check()
        if in_check:
            depth += 1

        if depth <= 0:
            return self.quiescence(alpha, beta, 4)

        if alpha < -MATE_SCORE + ply:
            alpha = -MATE_SCORE + ply
        if beta > MATE_SCORE - ply - 1:
            beta = MATE_SCORE - ply - 1
        if alpha >= beta:
            return alpha

        tt_key = compute_zobrist_key(
            self.board.board, self.board.turn,
            self.board.en_passant_target, self.board.castling_rights
        )
        tt_entry = self.tt.get(tt_key)
        tt_move = None
        if tt_entry:
            tt_move = tt_entry.get('best_move')
            if tt_entry['depth'] >= depth:
                tt_best = tt_entry.get('best_move')
                tt_leads_to_rep = False
                if tt_best is not None:
                    after_hash = self._position_hash_after_move(tt_best)
                    if self.board.position_history.get(after_hash, 0) >= 2:
                        tt_leads_to_rep = True

                if not tt_leads_to_rep:
                    if tt_entry['flag'] == TT_EXACT:
                        return tt_entry['score']
                    elif tt_entry['flag'] == TT_ALPHA and tt_entry['score'] <= alpha:
                        return alpha
                    elif tt_entry['flag'] == TT_BETA and tt_entry['score'] >= beta:
                        return beta

        if (not in_check and ply > 0 and depth >= 3
                and self._has_non_pawn_material()):
            self.board.turn = 'black' if self.board.turn == 'white' else 'white'
            old_ep = self.board.en_passant_target
            self.board.en_passant_target = None
            score = -self.negamax(depth - 3, ply + 1, -beta, -beta + 1)
            self.board.turn = 'black' if self.board.turn == 'white' else 'white'
            self.board.en_passant_target = old_ep
            if self.stopped:
                return 0
            if score >= beta:
                return beta

        moves = self.board.get_all_legal_moves()
        if not moves:
            if in_check:
                return -MATE_SCORE + ply
            return 0

        moves = self._order_moves(moves, depth, ply, tt_move)

        original_alpha = alpha
        best_move = moves[0]
        moves_searched = 0

        for i, move in enumerate(moves):
            after_hash = self._position_hash_after_move(move)
            is_repetition_move = self.board.position_history.get(after_hash, 0) >= 2

            state = self.board.get_state()
            self.board.make_move(move[0], move[1], record_history=False)

            if is_repetition_move:
                score = REP_DRAW_SCORE
            elif moves_searched == 0:
                score = -self.negamax(depth - 1, ply + 1, -beta, -alpha)
            else:
                if i >= 4 and depth >= 3 and not in_check:
                    reduction = 1
                    score = -self.negamax(depth - 1 - reduction, ply + 1, -alpha - 1, -alpha)
                    if score > alpha:
                        score = -self.negamax(depth - 1, ply + 1, -beta, -alpha)
                else:
                    score = -self.negamax(depth - 1, ply + 1, -beta, -alpha)

            self.board.set_state(state)
            moves_searched += 1

            if self.stopped:
                return 0

            if score > alpha:
                alpha = score
                best_move = move

                self.pv_table[ply][ply] = move
                for j in range(ply + 1, ply + 1 + self.pv_length[ply + 1]):
                    self.pv_table[ply][j] = self.pv_table[ply + 1][j]
                self.pv_length[ply] = 1 + self.pv_length[ply + 1]

                if self.board.board[move[1][0]][move[1][1]] == '.':
                    self.history[(move[0], move[1])] = self.history.get((move[0], move[1]), 0) + depth * depth

                if alpha >= beta:
                    if self.board.board[move[1][0]][move[1][1]] == '.':
                        if self.killers[ply][0] != move:
                            self.killers[ply][1] = self.killers[ply][0]
                            self.killers[ply][0] = move
                    break

        if best_move:
            flag = TT_EXACT
            if alpha <= original_alpha:
                flag = TT_ALPHA
            elif alpha >= beta:
                flag = TT_BETA
            self.tt.store(tt_key, depth, alpha, flag, best_move)

        return alpha

    def quiescence(self, alpha, beta, depth_remaining=4):
        self.nodes += 1

        if self.nodes % 2048 == 0:
            if time.time() - self.start_time > self.time_limit:
                self.stopped = True
                return 0

        stand_pat = self.eval.evaluate()

        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        if depth_remaining <= 0:
            return stand_pat

        if depth_remaining <= 1:
            if stand_pat + 600 < alpha:
                return alpha

        in_check = self.board.is_in_check()

        v = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}
        captures = []
        for row in range(8):
            for col in range(8):
                piece = self.board.board[row][col]
                if piece != '.' and self.board.get_piece_color(piece) == self.board.turn:
                    moves = self.board.get_piece_moves(row, col)
                    for m in moves:
                        target = self.board.board[m[0]][m[1]]
                        if target != '.' and self.board.get_piece_color(target) != self.board.turn:
                            captures.append(((row, col), m))
                        elif piece.lower() == 'p' and (m[0] == 0 or m[0] == 7):
                            captures.append(((row, col), m))
                        elif in_check:
                            captures.append(((row, col), m))

        if not captures:
            return alpha

        if in_check:
            passes = []
            checks = []
            for mv in captures:
                t = self.board.board[mv[1][0]][mv[1][1]]
                if t != '.' and self.board.get_piece_color(t) != self.board.turn:
                    checks.append(mv)
                else:
                    passes.append(mv)
            checks.sort(key=lambda mv: v.get(self.board.board[mv[1][0]][mv[1][1]].lower(), 0)
                                  - v.get(self.board.board[mv[0][0]][mv[0][1]].lower(), 0),
                        reverse=True)
            captures = checks + passes
        else:
            captures.sort(key=lambda mv: v.get(self.board.board[mv[1][0]][mv[1][1]].lower(), 0)
                                   - v.get(self.board.board[mv[0][0]][mv[0][1]].lower(), 0),
                          reverse=True)

        if depth_remaining <= 2 and len(captures) > 30:
            captures = captures[:30]

        for move in captures:
            if not self.board.is_move_legal(move[0], move[1]):
                continue

            state = self.board.get_state()
            self.board.make_move(move[0], move[1], record_history=False)
            score = -self.quiescence(-beta, -alpha, depth_remaining - 1)
            self.board.set_state(state)

            if self.stopped:
                return 0

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _order_moves(self, moves, depth, ply, tt_move=None):
        rep_info = {}
        for move in moves:
            h = self._position_hash_after_move(move)
            rep_info[move] = self.board.position_history.get(h, 0)

        vals = {'p': 100, 'n': 320, 'b': 330, 'r': 500, 'q': 900, 'k': 20000}

        def move_score(move):
            start, end = move
            val = 0

            if tt_move and move == tt_move:
                val += 1000000

            target = self.board.board[end[0]][end[1]]
            if target != '.':
                attacker = self.board.board[start[0]][start[1]].lower()
                victim = target.lower()
                val += 10000 + vals.get(victim, 0) - vals.get(attacker, 0)

            if self.killers[ply][0] == move:
                val = max(val, 9000)
            elif self.killers[ply][1] == move:
                val = max(val, 8000)

            hist_val = self.history.get((start, end), 0)
            if hist_val:
                val = max(val, min(hist_val, 7000))

            piece = self.board.board[start[0]][start[1]].lower()
            if piece == 'p' and (end[0] == 0 or end[0] == 7):
                val += 8000

            seen = rep_info.get(move, 0)
            if seen >= 2:
                val -= 500000
            elif seen >= 1:
                val -= 50000

            return val

        return sorted(moves, key=move_score, reverse=True)

    def _has_non_pawn_material(self):
        for row in range(8):
            for col in range(8):
                piece = self.board.board[row][col]
                if piece != '.' and self.board.get_piece_color(piece) == self.board.turn:
                    if piece.lower() not in ('p', 'k'):
                        return True
        return False

    def _print_uci_info(self, depth, score, pv_move):
        elapsed = time.time() - self.start_time
        if elapsed <= 0:
            elapsed = 0.001
        nps = int(self.nodes / elapsed)

        if abs(score) > MATE_SCORE - 100:
            mate_in = (MATE_SCORE - abs(score) + 1) // 2
            if score > 0:
                score_str = f"mate {mate_in}"
            else:
                score_str = f"mate -{mate_in}"
        else:
            score_str = f"cp {score}"

        pv_parts = []
        if pv_move:
            start_sq = self.board.coord_to_square(pv_move[0][0], pv_move[0][1])
            end_sq = self.board.coord_to_square(pv_move[1][0], pv_move[1][1])
            pv_parts.append(f"{start_sq}{end_sq}")
        for i in range(self.pv_length[0]):
            if i == 0:
                continue
            move = self.pv_table[0][i]
            if move:
                start_sq = self.board.coord_to_square(move[0][0], move[0][1])
                end_sq = self.board.coord_to_square(move[1][0], move[1][1])
                pv_parts.append(f"{start_sq}{end_sq}")

        pv_str = ' '.join(pv_parts)
        msg = f"info depth {depth} score {score_str} nodes {self.nodes} nps {nps}"
        if pv_str:
            msg += f" pv {pv_str}"
        sys.stdout.write(f"{msg}\n")
        sys.stdout.flush()
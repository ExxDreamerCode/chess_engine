import sys
import time
from board import Board
from evaluation import Evaluation
from search import Search, DEFAULT_TIME_LIMIT
from opening_book import find_book_moves


class ChessEngine:

    def __init__(self):
        self.board = Board()
        self.search = Search(self.board)
        self.eval = Evaluation(self.board)

    def reset(self):
        self.board = Board()
        self.search = Search(self.board)
        self.eval = Evaluation(self.board)

    def set_fen(self, fen):
        self.reset()
        parts = fen.split(' ')
        board_part = parts[0]

        rows = board_part.split('/')
        for r_idx, row_str in enumerate(rows):
            c_idx = 0
            for ch in row_str:
                if ch.isdigit():
                    c_idx += int(ch)
                else:
                    self.board.board[r_idx][c_idx] = ch
                    c_idx += 1

        if len(parts) > 1:
            self.board.turn = 'white' if parts[1] == 'w' else 'black'

        if len(parts) > 2:
            rights = parts[2]
            self.board.castling_rights = {
                'white_kingside': 'K' in rights,
                'white_queenside': 'Q' in rights,
                'black_kingside': 'k' in rights,
                'black_queenside': 'q' in rights
            }

        if len(parts) > 3:
            ep = parts[3]
            if ep != '-':
                self.board.en_passant_target = ep
            else:
                self.board.en_passant_target = None

        if len(parts) > 4:
            self.board.halfmove_clock = int(parts[4])

        if len(parts) > 5:
            self.board.fullmove_number = int(parts[5])

    def get_fen(self):
        pieces = {'K': 'K', 'Q': 'Q', 'R': 'R', 'B': 'B', 'N': 'N', 'P': 'P',
                  'k': 'k', 'q': 'q', 'r': 'r', 'b': 'b', 'n': 'n', 'p': 'p'}

        board_str = ''
        for row in self.board.board:
            empty_count = 0
            for piece in row:
                if piece == '.':
                    empty_count += 1
                else:
                    if empty_count > 0:
                        board_str += str(empty_count)
                        empty_count = 0
                    board_str += pieces.get(piece, piece)
            if empty_count > 0:
                board_str += str(empty_count)
            board_str += '/'
        board_str = board_str.rstrip('/')

        turn_str = 'w' if self.board.turn == 'white' else 'b'

        castling = ''
        if self.board.castling_rights['white_kingside']:
            castling += 'K'
        if self.board.castling_rights['white_queenside']:
            castling += 'Q'
        if self.board.castling_rights['black_kingside']:
            castling += 'k'
        if self.board.castling_rights['black_queenside']:
            castling += 'q'
        if not castling:
            castling = '-'

        ep = self.board.en_passant_target if self.board.en_passant_target else '-'

        return f"{board_str} {turn_str} {castling} {ep} {self.board.halfmove_clock} {self.board.fullmove_number}"

    def make_move(self, start, end, promotion='q'):
        self.board.make_move(start, end, promotion)

    def get_legal_moves(self):
        return self.board.get_all_legal_moves()

    def is_game_over(self):
        if self.board.is_checkmate():
            return True, 'checkmate'
        if self.board.is_stalemate():
            return True, 'stalemate'
        if self.board.is_fifty_move_rule():
            return True, 'fiftymoves'
        if self.board.is_insufficient_material():
            return True, 'insufficient_material'
        if self.board.is_threefold_repetition():
            return True, 'repetition'
        return False, None

    def find_best_move(self, time_limit=DEFAULT_TIME_LIMIT, depth_limit=64):
        if len(self.board.move_history) < 12:
            book_moves = find_book_moves(self.board)
            if book_moves:
                legal = self.board.get_all_legal_moves()
                legal_book = [m for m in book_moves if m in legal]
                if legal_book:
                    best_book_move = legal_book[0]
                    best_book_score = -99999
                    for bm in legal_book:
                        state = self.board.get_state()
                        self.board.make_move(bm[0], bm[1], record_history=False)
                        score = -self.eval.evaluate()
                        if score > best_book_score:
                            best_book_score = score
                            best_book_move = bm
                        self.board.set_state(state)

                    sys.stdout.write(f"info depth 0 score cp {best_book_score} nodes 0 time 0 pv book move\n")
                    sys.stdout.flush()
                    return best_book_move

        return self.search.get_best_move(time_limit=time_limit, depth_limit=depth_limit)
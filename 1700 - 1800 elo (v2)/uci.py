#!/usr/bin/env python3

import sys
import math
import time
from chess_engine import ChessEngine, ChessAI


class UCIEngine:
    def __init__(self):
        self.engine = ChessEngine()
        self.ai = ChessAI(self.engine, depth=4)
        self.searching = False
        self.stop_search = False
        self.start_time = 0
        self.max_time = 0
        
    def run(self):
        self.send_id()
        
        while True:
            try:
                line = sys.stdin.readline().strip()
                if not line:
                    continue
                
                if line == "quit":
                    break
                elif line == "uci":
                    self.send_id()
                elif line == "isready":
                    print("readyok")
                    sys.stdout.flush()
                elif line == "ucinewgame":
                    self.engine = ChessEngine()
                    self.ai = ChessAI(self.engine, depth=4)
                elif line.startswith("position"):
                    self.set_position(line)
                elif line.startswith("go"):
                    self.go(line)
                elif line == "stop":
                    self.stop_search = True
                elif line == "d":
                    self.print_board()
                    
            except Exception as e:
                print(f"info string error: {e}", file=sys.stderr)
                sys.stderr.flush()
                
    def send_id(self):
        print(f"id name DreamerExx_ChessEngine v1.4")
        print(f"id author Dreamer_Exx (14 years old)")
        print("uciok")
        sys.stdout.flush()
        
    def set_position(self, cmd):
        parts = cmd.split()
        
        if parts[1] == "startpos":
            self.engine = ChessEngine()
            self.ai = ChessAI(self.engine, depth=4)
            
            if len(parts) > 2 and parts[2] == "moves":
                for move_str in parts[3:]:
                    self.apply_uci_move(move_str)
                    
    def apply_uci_move(self, move_str):
        from_col = ord(move_str[0]) - ord('a')
        from_row = 8 - int(move_str[1])
        to_col = ord(move_str[2]) - ord('a')
        to_row = 8 - int(move_str[3])
        
        promotion = None
        if len(move_str) == 5:
            promotion = move_str[4]
        
        start = (from_row, from_col)
        end = (to_row, to_col)
        
        if promotion:
            self.engine.make_move(start, end, promotion)
        else:
            self.engine.make_move(start, end)
    
    def get_my_evaluation_cp(self):
        score = self.engine.evaluate_board()
        
        if self.engine.turn == 'white':
            return int(score)
        else:
            return int(-score)
    
    def is_move_mate(self, move):
        start, end = move
        piece = self.engine.board[start[0]][start[1]]
        
        state = self.engine.get_state()
        
        promotion = None
        if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
            promotion = 'q'
        
        if promotion:
            self.engine.make_move(start, end, promotion)
        else:
            self.engine.make_move(start, end)
        
        is_mate = self.engine.is_checkmate()
        
        self.engine.set_state(state)
        
        return is_mate
    
    def get_mate_distance(self, move):
        if self.is_move_mate(move):
            return 1
        return None
    
    def send_my_evaluation(self, depth=None, search_time=None, best_move=None):
        if best_move:
            mate_distance = self.get_mate_distance(best_move)
            if mate_distance:
                info_parts = [f"info score mate {mate_distance}"]
                if depth is not None:
                    info_parts.append(f"depth {depth}")
                if search_time is not None:
                    info_parts.append(f"time {search_time}")
                print(" ".join(info_parts))
                print(f"info string DreamerExx_mate: {mate_distance}")
                sys.stdout.flush()
                return
        
        score_cp = self.get_my_evaluation_cp()
        
        info_parts = [f"info score cp {score_cp}"]
        
        if depth is not None:
            info_parts.append(f"depth {depth}")
        
        if search_time is not None:
            info_parts.append(f"time {search_time}")
        
        print(" ".join(info_parts))
        print(f"info string DreamerExx_eval: {score_cp/100:.2f} pawns")
        sys.stdout.flush()
    
    def go(self, cmd):
        parts = cmd.split()
        
        depth = 4
        for i in range(len(parts)):
            if parts[i] == "depth" and i + 1 < len(parts):
                depth = int(parts[i + 1])
                break
        
        self.ai.depth = min(depth, 5)
        
        print(f"info string DreamerExx analyzing position...")
        
        start_time = time.time()
        
        best_move = self.ai.get_best_move()
        
        elapsed_ms = int((time.time() - start_time) * 1000)
        
        self.send_my_evaluation(depth=self.ai.depth, search_time=elapsed_ms, best_move=best_move)
        
        if best_move:
            move_str = self.move_to_uci(best_move)
            print(f"bestmove {move_str}")
        else:
            moves = self.engine.get_all_legal_moves()
            if moves:
                move_str = self.move_to_uci(moves[0])
                print(f"bestmove {move_str}")
                print(f"info string warning: no bestmove found, using first legal move")
            else:
                print("bestmove (none)")
        
        sys.stdout.flush()
    
    def move_to_uci(self, move):
        start, end = move
        from_square = f"{chr(start[1] + ord('a'))}{8 - start[0]}"
        to_square = f"{chr(end[1] + ord('a'))}{8 - end[0]}"
        
        piece = self.engine.board[start[0]][start[1]]
        if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
            promotion = 'q'
            if hasattr(self.engine, 'move_history') and self.engine.move_history:
                last_move = self.engine.move_history[-1]
                if last_move.get('promotion'):
                    promotion = last_move['promotion'].lower()
            
            return from_square + to_square + promotion
        
        return from_square + to_square
        
    def print_board(self):
        for row in self.engine.board:
            print(' '.join(row))
        sys.stdout.flush()


if __name__ == "__main__":
    engine = UCIEngine()
    engine.run()
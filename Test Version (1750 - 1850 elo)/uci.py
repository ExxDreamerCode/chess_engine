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
        
        self.max_depth_limit = 6
        self.min_depth_limit = 2
        self.move_time_limit = 5.0
        self.max_mate_depth = 10
        
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
                    global transposition_table
                    transposition_table.clear()
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
        print(f"id name DreamerExx_ChessEngine v1.5")
        print(f"id author Dreamer_Exx")
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
    
    def calculate_adaptive_depth(self, remaining_time, moves_to_go=0, move_number=0):
        if remaining_time <= 0:
            return self.min_depth_limit
        
        if remaining_time < 1.0:
            return self.min_depth_limit
        
        if moves_to_go > 0:
            estimated_moves_left = moves_to_go
        else:
            estimated_moves_left = max(10, 40 - move_number)
        
        time_per_move = remaining_time / estimated_moves_left * 0.8
        
        time_per_move = min(time_per_move, self.move_time_limit)
        
        if time_per_move >= 5.0:
            base_depth = self.max_depth_limit
        elif time_per_move >= 3.0:
            base_depth = self.max_depth_limit - 1
        elif time_per_move >= 2.0:
            base_depth = min(self.max_depth_limit - 2, 6)
        elif time_per_move >= 1.0:
            base_depth = min(self.max_depth_limit - 3, 5)
        elif time_per_move >= 0.5:
            base_depth = min(self.max_depth_limit - 4, 4)
        else:
            base_depth = self.min_depth_limit
        
        white_score, black_score = self.engine.get_material_value()
        total_material = white_score + black_score
        
        if total_material < 20:
            base_depth += 1
        
        if total_material < 30:
            moves_count = len(self.engine.get_all_legal_moves())
            if moves_count < 20:
                base_depth += 1
        
        if remaining_time < 5.0:
            base_depth = min(base_depth, self.min_depth_limit + 2)
        
        final_depth = max(self.min_depth_limit, min(base_depth, self.max_depth_limit))
        
        print(f"info string Adaptive depth: {final_depth} (time_per_move={time_per_move:.2f}s, remaining={remaining_time:.1f}s)")
        return final_depth
    
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
        
        wtime = None
        btime = None
        winc = None
        binc = None
        movetime = None
        movestogo = None
        depth_param = None
        
        for i in range(len(parts)):
            if parts[i] == "wtime" and i + 1 < len(parts):
                wtime = int(parts[i + 1])
            elif parts[i] == "btime" and i + 1 < len(parts):
                btime = int(parts[i + 1])
            elif parts[i] == "winc" and i + 1 < len(parts):
                winc = int(parts[i + 1])
            elif parts[i] == "binc" and i + 1 < len(parts):
                binc = int(parts[i + 1])
            elif parts[i] == "movetime" and i + 1 < len(parts):
                movetime = int(parts[i + 1])
            elif parts[i] == "movestogo" and i + 1 < len(parts):
                movestogo = int(parts[i + 1])
            elif parts[i] == "depth" and i + 1 < len(parts):
                depth_param = int(parts[i + 1])
        
        MAX_TIME_PER_MOVE = 10.0
        
        remaining_time = None
        if self.engine.turn == 'white' and wtime is not None:
            remaining_time = wtime / 1000.0
        elif self.engine.turn == 'black' and btime is not None:
            remaining_time = btime / 1000.0
        
        if movetime is not None:
            time_limit = min(movetime / 1000.0, MAX_TIME_PER_MOVE)
        else:
            if remaining_time is not None and remaining_time > 0:
                if movestogo and movestogo > 0:
                    estimated_moves = movestogo
                else:
                    moves_played = len(self.engine.move_history) // 2
                    estimated_moves = max(10, 40 - moves_played)
                
                time_per_move = remaining_time / estimated_moves
                
                if self.engine.turn == 'white' and winc:
                    time_per_move += winc / 1000.0
                elif self.engine.turn == 'black' and binc:
                    time_per_move += binc / 1000.0
                
                time_limit = min(time_per_move, MAX_TIME_PER_MOVE)
                
                if remaining_time < 3.0:
                    time_limit = min(time_limit, 2.0)
                elif remaining_time < 1.0:
                    time_limit = min(time_limit, 0.5)
            else:
                time_limit = MAX_TIME_PER_MOVE / 2
        
        if depth_param is not None:
            adaptive_depth = min(depth_param, 8)
        else:
            if time_limit >= 8.0:
                adaptive_depth = 5
            elif time_limit >= 5.0:
                adaptive_depth = 4
            elif time_limit >= 3.0:
                adaptive_depth = 4
            elif time_limit >= 1.5:
                adaptive_depth = 3
            elif time_limit >= 0.5:
                adaptive_depth = 2
            else:
                adaptive_depth = 1
        
        self.ai.depth = adaptive_depth
        self.max_time = time_limit
        self.start_time = time.time()
        self.stop_search = False
        
        print(f"info string time_limit={time_limit:.2f}s, depth={adaptive_depth}, remaining_time={remaining_time if remaining_time else 'unknown'}s")
        
        all_moves = self.engine.get_all_legal_moves()
        mate_in_one = None
        
        for move in all_moves:
            state = self.engine.get_state()
            
            start, end = move
            piece = self.engine.board[start[0]][start[1]]
            promotion = None
            if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
                promotion = 'q'
            
            if promotion:
                self.engine.make_move(start, end, promotion, record_history=False)
            else:
                self.engine.make_move(start, end, record_history=False)
            
            if self.engine.is_checkmate():
                mate_in_one = move
                self.engine.set_state(state)
                break
            
            self.engine.set_state(state)
        
        if mate_in_one:
            move_str = self.move_to_uci(mate_in_one)
            print(f"info string Checkmate in 1 found!")
            print(f"bestmove {move_str}")
            sys.stdout.flush()
            return
        
        best_move = None
        start_search = time.time()
        
        try:
            self.ai.depth = min(2, adaptive_depth)
            print(f"info string Quick search depth {self.ai.depth}...")
            quick_move = self.ai.get_best_move()
            
            if quick_move and (time.time() - start_search) < time_limit * 0.3:
                best_move = quick_move
                print(f"info string Quick search found: {self.move_to_uci(best_move)}")
            
            if (time.time() - start_search) < time_limit * 0.6:
                self.ai.depth = adaptive_depth
                print(f"info string Full search depth {self.ai.depth}...")
                deep_move = self.ai.get_best_move()
                
                if deep_move:
                    best_move = deep_move
                    print(f"info string Deep search found: {self.move_to_uci(best_move)}")
        
        except Exception as e:
            print(f"info string Search error: {e}", file=sys.stderr)
        
        elapsed = time.time() - start_search
        if elapsed > time_limit:
            print(f"info string Time exceeded! elapsed={elapsed:.2f}s > limit={time_limit:.2f}s")
        
        if not best_move and all_moves:
            for move in all_moves:
                start, end = move
                piece = self.engine.board[start[0]][start[1]]
                
                if piece.upper() in ['N', 'B', 'Q']:
                    if 2 <= end[0] <= 5 and 2 <= end[1] <= 5:
                        best_move = move
                        break
            
            if not best_move:
                best_move = all_moves[0]
        
        elapsed_ms = int((time.time() - start_search) * 1000)
        
        self.send_my_evaluation(depth=self.ai.depth, search_time=elapsed_ms, best_move=best_move)
        
        if best_move:
            move_str = self.move_to_uci(best_move)
            print(f"bestmove {move_str}")
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
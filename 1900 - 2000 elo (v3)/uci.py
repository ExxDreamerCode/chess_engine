import sys
import time
from engine import ChessEngine


class UCI:

    def __init__(self):
        self.engine = ChessEngine()
        self.thinking_time = {}
        self.movetime = 0
        self.time_left = {}
        self.inc = {}
        self.moves_to_go = 40
        self.have_time_control = False

    def run(self):
        engine_name = "DreamerExx V3"
        engine_author = "DreamerExx"

        print(f"id name {engine_name}")
        print(f"id author {engine_author}")
        print("uciok")
        sys.stdout.flush()

        while True:
            try:
                line = sys.stdin.readline()
            except KeyboardInterrupt:
                break

            if not line:
                break

            line = line.strip()
            if not line:
                continue

            tokens = line.split()

            if tokens[0] == 'quit':
                break

            elif tokens[0] == 'uci':
                print("id name " + engine_name)
                print("id author " + engine_author)
                print("uciok")
                sys.stdout.flush()

            elif tokens[0] == 'isready':
                print("readyok")
                sys.stdout.flush()

            elif tokens[0] == 'ucinewgame':
                self.engine.reset()
                self.thinking_time = {}
                self.time_left = {}
                self.inc = {}
                self.movetime = 0
                self.have_time_control = False
                self.moves_to_go = 40

            elif tokens[0] == 'position':
                self._handle_position(tokens[1:])

            elif tokens[0] == 'go':
                self._handle_go(tokens[1:])

            elif tokens[0] == 'stop':
                self.engine.search.stopped = True

            elif tokens[0] == 'setoption':
                pass

    def _handle_position(self, tokens):
        if not tokens:
            return

        idx = 0

        if tokens[idx] == 'startpos':
            self.engine.reset()
            idx += 1
        elif tokens[idx] == 'fen':
            fen_parts = []
            idx += 1
            while idx < len(tokens) and tokens[idx] != 'moves':
                fen_parts.append(tokens[idx])
                idx += 1
            if fen_parts:
                self.engine.set_fen(' '.join(fen_parts))
        else:
            return

        if idx < len(tokens) and tokens[idx] == 'moves':
            idx += 1
            while idx < len(tokens):
                move_str = tokens[idx]
                start, end, promotion = self._parse_uci_move(move_str)
                if start:
                    self.engine.make_move(start, end, promotion or 'q')
                idx += 1

    def _handle_go(self, tokens):
        idx = 0
        depth_limit = 64

        self.movetime = 0
        self.have_time_control = False

        while idx < len(tokens):
            if tokens[idx] == 'wtime' and idx + 1 < len(tokens):
                self.time_left['white'] = int(tokens[idx + 1])
                self.have_time_control = True
                idx += 2
            elif tokens[idx] == 'btime' and idx + 1 < len(tokens):
                self.time_left['black'] = int(tokens[idx + 1])
                self.have_time_control = True
                idx += 2
            elif tokens[idx] == 'winc' and idx + 1 < len(tokens):
                self.inc['white'] = int(tokens[idx + 1])
                idx += 2
            elif tokens[idx] == 'binc' and idx + 1 < len(tokens):
                self.inc['black'] = int(tokens[idx + 1])
                idx += 2
            elif tokens[idx] == 'movestogo' and idx + 1 < len(tokens):
                self.moves_to_go = int(tokens[idx + 1])
                idx += 2
            elif tokens[idx] == 'movetime' and idx + 1 < len(tokens):
                self.movetime = int(tokens[idx + 1])
                self.have_time_control = False
                idx += 2
            elif tokens[idx] == 'depth' and idx + 1 < len(tokens):
                depth_limit = int(tokens[idx + 1])
                idx += 2
            elif tokens[idx] == 'infinite':
                self.movetime = 99999000
                idx += 1
            else:
                idx += 1

        time_limit = self._calculate_time()

        best_move = self.engine.find_best_move(time_limit=time_limit, depth_limit=depth_limit)

        if best_move:
            move_str = self._format_uci_move(best_move)
            print(f"bestmove {move_str}")
        else:
            print("bestmove 0000")
        sys.stdout.flush()

    def _calculate_time(self):
        if self.movetime > 0:
            return max(0.01, self.movetime / 1000.0)

        if self.have_time_control:
            color = self.engine.board.turn
            time_left_ms = self.time_left.get(color, 60000)
            inc_ms = self.inc.get(color, 0)
            moves_to_go = max(1, self.moves_to_go)

            if time_left_ms <= 30000:
                percent = 0.06 if inc_ms == 0 else 0.1
                allocated_time = int(time_left_ms * percent) + inc_ms
                allocated_time = max(50, min(allocated_time, int(time_left_ms * 0.3)))
            elif time_left_ms <= 120000:
                allocated_time = time_left_ms // moves_to_go + inc_ms // 2
                allocated_time = min(allocated_time, int(time_left_ms * 0.4))
            else:
                allocated_time = time_left_ms // moves_to_go + inc_ms // 2
                allocated_time = min(allocated_time, int(time_left_ms * 0.3))

            allocated_time = min(allocated_time, int(time_left_ms * 0.8))
            return max(0.05, allocated_time / 1000.0)

        return 0.1

    def _parse_uci_move(self, move_str):
        if len(move_str) < 4:
            return None, None, None

        start = self.engine.board.square_to_coord(move_str[:2])
        end = self.engine.board.square_to_coord(move_str[2:4])
        promotion = None
        if len(move_str) > 4:
            promotion = move_str[4]

        return start, end, promotion

    def _format_uci_move(self, move):
        start, end = move
        start_sq = self.engine.board.coord_to_square(start[0], start[1])
        end_sq = self.engine.board.coord_to_square(end[0], end[1])
        piece = self.engine.board.board[start[0]][start[1]]
        if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
            if self.engine.board.move_history:
                last = self.engine.board.move_history[-1]
                if last.get('promotion'):
                    return f"{start_sq}{end_sq}{last['promotion']}"
            return f"{start_sq}{end_sq}q"
        return f"{start_sq}{end_sq}"


if __name__ == "__main__":
    uci = UCI()
    uci.run()
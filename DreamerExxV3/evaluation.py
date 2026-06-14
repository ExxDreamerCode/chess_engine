from board import Board, PIECE_VALUES
from board import (PAWN_TABLE, KNIGHT_TABLE, BISHOP_TABLE, ROOK_TABLE, QUEEN_TABLE,
                   KING_MIDDLE_TABLE, KING_ENDGAME_TABLE, PAWN_ENDGAME_TABLE)

MIDGAME_VALUES = {'K':0,'Q':1025,'R':477,'B':365,'N':337,'P':82}
TOTAL_PHASE = (MIDGAME_VALUES['Q']*2 + MIDGAME_VALUES['R']*4 +
               MIDGAME_VALUES['B']*4 + MIDGAME_VALUES['N']*4)

PST_SCALE = 10
DOUBLED_PEN = 12
ISOLATED_PEN = 20
PASSED_BONUS = [5, 10, 20, 30, 50, 75, 100, 150]
BISHOP_PAIR = 30

MOBILITY_BONUS = {
    'p': 1, 'n': 3, 'b': 3, 'r': 2, 'q': 2, 'k': 1
}

ROOK_OPEN_FILE_BONUS = 10
CENTER_CONTROL_BONUS = 4
DEVELOPMENT_BONUS = 6

_KNIGHT_MOBILITY = [[0]*8 for _ in range(8)]
_BISHOP_MOBILITY = [[0]*8 for _ in range(8)]
_ROOK_MOBILITY = [[0]*8 for _ in range(8)]
_QUEEN_MOBILITY = [[0]*8 for _ in range(8)]
_KING_MOBILITY = [[0]*8 for _ in range(8)]
_PAWN_W_MOBILITY = [[0]*8 for _ in range(8)]
_PAWN_B_MOBILITY = [[0]*8 for _ in range(8)]

KNIGHT_DELTAS = [(-2,-1),(-2,1),(-1,-2),(-1,2),(1,-2),(1,2),(2,-1),(2,1)]
KING_DELTAS = [(-1,-1),(-1,0),(-1,1),(0,-1),(0,1),(1,-1),(1,0),(1,1)]

for r in range(8):
    for c in range(8):
        cnt = 0
        for dr, dc in KNIGHT_DELTAS:
            if 0 <= r + dr < 8 and 0 <= c + dc < 8:
                cnt += 1
        _KNIGHT_MOBILITY[r][c] = cnt

        cnt = 0
        for dr, dc in KING_DELTAS:
            if 0 <= r + dr < 8 and 0 <= c + dc < 8:
                cnt += 1
        _KING_MOBILITY[r][c] = cnt

        _BISHOP_MOBILITY[r][c] = min(r, c) + min(r, 7-c) + min(7-r, c) + min(7-r, 7-c)
        _ROOK_MOBILITY[r][c] = r + (7-r) + c + (7-c)
        _QUEEN_MOBILITY[r][c] = _BISHOP_MOBILITY[r][c] + _ROOK_MOBILITY[r][c]

        wm = 0
        if r > 0:
            wm += 1
            if r == 6:
                wm += 1
        if r > 0:
            if c > 0: wm += 1
            if c < 7: wm += 1
        _PAWN_W_MOBILITY[r][c] = wm

        bm = 0
        if r < 7:
            bm += 1
            if r == 1:
                bm += 1
        if r < 7:
            if c > 0: bm += 1
            if c < 7: bm += 1
        _PAWN_B_MOBILITY[r][c] = bm

CENTER_SQUARES = [(3, 3), (3, 4), (4, 3), (4, 4)]


class Evaluation:
    def __init__(self, board: Board):
        self.board = board

    def evaluate(self):
        b = self.board.board
        turn = self.board.turn

        phase = 0
        for r in range(8):
            for c in range(8):
                p = b[r][c]
                if p != '.' and p.lower() != 'k' and p.upper() != 'P':
                    phase += MIDGAME_VALUES.get(p.upper(), 0)
        phase = max(0, min(TOTAL_PHASE, phase))
        eg_weight = max(0, min(256, (TOTAL_PHASE - phase) * 256 // TOTAL_PHASE))
        mg_weight = 256 - eg_weight

        raw = 0
        wp, bp = [], []
        white_mobility_total = 0
        black_mobility_total = 0
        white_developed = 0
        black_developed = 0
        move_number = len(self.board.move_history)

        for r in range(8):
            for c in range(8):
                p = b[r][c]
                if p == '.':
                    continue

                is_white = p.isupper()
                piece_type = p.lower()

                material_value = PIECE_VALUES.get(p.upper(), 0)
                raw += material_value if is_white else -material_value

                row_pst = 7 - r if is_white else r

                if piece_type == 'p':
                    mg = PAWN_TABLE[row_pst][c]
                    eg = PAWN_ENDGAME_TABLE[row_pst][c]
                    if is_white:
                        wp.append((r, c))
                        mob_count = _PAWN_W_MOBILITY[r][c]
                    else:
                        bp.append((r, c))
                        mob_count = _PAWN_B_MOBILITY[r][c]
                elif piece_type == 'n':
                    mg = eg = KNIGHT_TABLE[row_pst][c]
                    mob_count = _KNIGHT_MOBILITY[r][c]
                    if move_number < 20 and ((is_white and r == 7) or (not is_white and r == 0)):
                        if is_white:
                            white_developed += 1
                        else:
                            black_developed += 1
                elif piece_type == 'b':
                    mg = eg = BISHOP_TABLE[row_pst][c]
                    mob_count = _BISHOP_MOBILITY[r][c]
                    if move_number < 20 and ((is_white and r == 7) or (not is_white and r == 0)):
                        if is_white:
                            white_developed += 1
                        else:
                            black_developed += 1
                elif piece_type == 'r':
                    mg = eg = ROOK_TABLE[row_pst][c]
                    mob_count = _ROOK_MOBILITY[r][c]
                    if self._is_file_open(c):
                        raw += ROOK_OPEN_FILE_BONUS if is_white else -ROOK_OPEN_FILE_BONUS
                elif piece_type == 'q':
                    mg = eg = QUEEN_TABLE[row_pst][c]
                    mob_count = _QUEEN_MOBILITY[r][c]
                elif piece_type == 'k':
                    mg = KING_MIDDLE_TABLE[row_pst][c]
                    eg = KING_ENDGAME_TABLE[row_pst][c]
                    mob_count = _KING_MOBILITY[r][c]
                else:
                    continue

                pst = (mg * mg_weight + eg * eg_weight) // 256 // PST_SCALE
                raw += pst if is_white else -pst

                mobility_value = mob_count * MOBILITY_BONUS.get(piece_type, 0)
                if is_white:
                    white_mobility_total += mobility_value
                else:
                    black_mobility_total += mobility_value

        raw += (white_mobility_total - black_mobility_total) // 2
        dev_bonus = (white_developed - black_developed) * DEVELOPMENT_BONUS
        raw += dev_bonus
        pawn_score = self._pawn_structure_score(wp, bp, eg_weight)
        raw += pawn_score

        wb = sum(1 for r in range(8) for c in range(8) if b[r][c] == 'B')
        bb = sum(1 for r in range(8) for c in range(8) if b[r][c] == 'b')
        if wb >= 2:
            raw += BISHOP_PAIR
        if bb >= 2:
            raw -= BISHOP_PAIR

        if mg_weight > 128:
            raw += self._center_control_score()

        return raw if turn == 'white' else -raw

    def _is_file_open(self, col):
        b = self.board.board
        has_white = any(b[r][col] == 'P' for r in range(8))
        has_black = any(b[r][col] == 'p' for r in range(8))
        return not has_white and not has_black

    def _pawn_structure_score(self, wp, bp, eg_weight):
        b = self.board.board
        score = 0

        wfc = [0] * 8
        bfc = [0] * 8
        for _, c in wp:
            wfc[c] += 1
        for _, c in bp:
            bfc[c] += 1

        wd = sum(max(0, c - 1) for c in wfc)
        bd = sum(max(0, c - 1) for c in bfc)
        score -= (wd - bd) * DOUBLED_PEN

        wcols = {c for _, c in wp}
        for col in wcols:
            has_neighbor = (col > 0 and wfc[col - 1] > 0) or (col < 7 and wfc[col + 1] > 0)
            if not has_neighbor:
                score -= ISOLATED_PEN

        bcols = {c for _, c in bp}
        for col in bcols:
            has_neighbor = (col > 0 and bfc[col - 1] > 0) or (col < 7 and bfc[col + 1] > 0)
            if not has_neighbor:
                score += ISOLATED_PEN

        if eg_weight > 64:
            for r, c in wp:
                blocked = any(b[r2][c2] == 'p'
                             for r2 in range(r)
                             for c2 in [c-1, c, c+1] if 0 <= c2 < 8)
                if not blocked:
                    rank = 7 - r
                    if rank < len(PASSED_BONUS):
                        score += PASSED_BONUS[rank] * eg_weight // 256

            for r, c in bp:
                blocked = any(b[r2][c2] == 'P'
                             for r2 in range(r+1, 8)
                             for c2 in [c-1, c, c+1] if 0 <= c2 < 8)
                if not blocked:
                    rank = r
                    if rank < len(PASSED_BONUS):
                        score -= PASSED_BONUS[rank] * eg_weight // 256

        return score

    def _center_control_score(self):
        b = self.board.board
        control = 0

        for cr, cc in CENTER_SQUARES:
            if cr + 1 < 8:
                if cc > 0 and b[cr+1][cc-1] == 'P':
                    control += CENTER_CONTROL_BONUS
                if cc < 7 and b[cr+1][cc+1] == 'P':
                    control += CENTER_CONTROL_BONUS
            if cr - 1 >= 0:
                if cc > 0 and b[cr-1][cc-1] == 'p':
                    control -= CENTER_CONTROL_BONUS
                if cc < 7 and b[cr-1][cc+1] == 'p':
                    control -= CENTER_CONTROL_BONUS

            for dr, dc in KNIGHT_DELTAS:
                nr, nc = cr + dr, cc + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    p = b[nr][nc]
                    if p == 'N':
                        control += CENTER_CONTROL_BONUS
                    elif p == 'n':
                        control -= CENTER_CONTROL_BONUS

        return control
import hashlib

TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2

ZOBRIST_KEYS = {}
ZOBRIST_SIDE = 0

def _init_zobrist():
    import random
    random.seed(12345678)
    pieces = ['P','N','B','R','Q','K','p','n','b','r','q','k']
    for piece in pieces:
        ZOBRIST_KEYS[piece] = [[random.getrandbits(64) for _ in range(8)] for _ in range(8)]
    global ZOBRIST_SIDE
    ZOBRIST_SIDE = random.getrandbits(64)

_init_zobrist()

def compute_zobrist_key(board, turn, en_passant, castling):
    key = 0
    for r in range(8):
        for c in range(8):
            p = board[r][c]
            if p != '.':
                key ^= ZOBRIST_KEYS[p][r][c]
    if turn == 'black':
        key ^= ZOBRIST_SIDE
    if en_passant:
        h = hashlib.md5(en_passant.encode()).digest()
        key ^= int.from_bytes(h[:8], 'big')
    cr_str = ''.join(str(v) for v in castling.values())
    h = hashlib.md5(cr_str.encode()).digest()
    key ^= int.from_bytes(h[:8], 'big')
    return key

class TranspositionTable:
    def __init__(self, mb_size=64):
        self.size = mb_size * 1024 * 1024 // 32
        self.table = {}
        self.new_write = False

    def store(self, key, depth, score, flag, best_move):
        self.table[key] = {
            'depth': depth,
            'score': score,
            'flag': flag,
            'best_move': best_move
        }

    def get(self, key):
        return self.table.get(key)

    def clear(self):
        self.table.clear()
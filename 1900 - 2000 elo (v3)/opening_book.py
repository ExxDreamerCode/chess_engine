from board import Board

OPENING_LINES = [
    [
        (6, 4, 4, 4),
        (1, 3, 3, 3),
        (4, 4, 3, 3),
    ],
    [
        (6, 4, 4, 4),
        (1, 4, 3, 4),
        (7, 5, 5, 5),
        (0, 1, 2, 1),
        (7, 2, 5, 3),
        (0, 6, 2, 6),
    ],
    [
        (6, 4, 4, 4),
        (1, 4, 3, 4),
        (7, 5, 5, 5),
        (0, 1, 2, 1),
        (7, 2, 5, 6),
    ],
    [
        (6, 3, 4, 3),
        (1, 4, 3, 4),
        (6, 1, 4, 1),
    ],
    [
        (6, 4, 4, 4),
        (1, 1, 3, 1),
        (7, 5, 5, 5),
    ],
]

def find_book_moves(board: Board):
    move_count = len(board.move_history)
    
    for line in OPENING_LINES:
        if move_count < len(line):
            match = True
            for i in range(move_count):
                hist = board.move_history[i]
                expected = line[i]
                if (hist['start'][0] != expected[0] or 
                    hist['start'][1] != expected[1] or
                    hist['end'][0] != expected[2] or 
                    hist['end'][1] != expected[3]):
                    match = False
                    break
            
            if match:
                expected = line[move_count]
                return [((expected[0], expected[1]), (expected[2], expected[3]))]
    
    if move_count == 0:
        return [
            ((6, 4), (4, 4)),
            ((6, 3), (4, 3)),
            ((6, 2), (4, 2)),
            ((7, 5), (5, 5)),
        ]
    
    return []
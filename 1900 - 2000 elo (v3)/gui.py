import pygame
import sys
import os
import urllib.request
from engine import ChessEngine

pygame.init()

BOARD_SIZE = 560
SQUARE_SIZE = BOARD_SIZE // 8
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (240, 217, 181)
DARK_BROWN = (181, 136, 99)
HIGHLIGHT = (255, 255, 0)
LAST_MOVE_COLOR = (170, 255, 170)
CHECK_COLOR = (255, 100, 100)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (100, 100, 255)
GRAY = (128, 128, 128)

PNG_URLS = {
    'K': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wk.png',
    'Q': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wq.png',
    'R': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wr.png',
    'B': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wb.png',
    'N': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wn.png',
    'P': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/wp.png',
    'k': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bk.png',
    'q': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bq.png',
    'r': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/br.png',
    'b': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bb.png',
    'n': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bn.png',
    'p': 'https://images.chesscomfiles.com/chess-themes/pieces/neo/150/bp.png'
}


class ChessGUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((BOARD_SIZE, BOARD_SIZE + 190))
        pygame.display.set_caption("DreamerExx V3 Chess Engine")

        try:
            pygame.scrap.init()
            self.scrap_available = True
        except:
            self.scrap_available = False

        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 28)
        self.big_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 20)

        self.engine = ChessEngine()
        self.selected_piece = None
        self.valid_moves = []
        self.running = True
        self.ai_thinking = False
        self.game_over = False
        self.winner = None
        self.player_color = None
        self.piece_images = {}
        self.flipped = False
        self.buttons = {}
        self.pgn_copied = False
        self.pgn_copy_timer = 0

        if not os.path.exists('pieces'):
            os.makedirs('pieces')

        self.load_piece_images()

    def load_piece_images(self):
        pieces = ['K', 'Q', 'R', 'B', 'N', 'P', 'k', 'q', 'r', 'b', 'n', 'p']
        for piece in pieces:
            self.download_piece_image(piece)

    def download_piece_image(self, piece):
        prefix = 'w_' if piece.isupper() else 'b_'
        image_path = f'pieces/{prefix}{piece}.png'

        if os.path.exists(image_path):
            try:
                img = pygame.image.load(image_path)
                self.piece_images[piece] = pygame.transform.scale(img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                return
            except:
                pass

        if piece in PNG_URLS:
            url = PNG_URLS[piece]
            try:
                req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
                with urllib.request.urlopen(req, timeout=10) as response:
                    image_data = response.read()

                with open(image_path, 'wb') as f:
                    f.write(image_data)

                img = pygame.image.load(image_path)
                self.piece_images[piece] = pygame.transform.scale(img, (SQUARE_SIZE - 10, SQUARE_SIZE - 10))
                return
            except:
                pass

        self.create_fallback_image(piece, image_path)

    def create_fallback_image(self, piece, filename=None):
        size = SQUARE_SIZE - 10
        img = pygame.Surface((size, size), pygame.SRCALPHA)

        if piece.isupper():
            main_color = (255, 248, 220)
            dark_color = (200, 180, 140)
            outline_color = (80, 80, 80)
        else:
            main_color = (40, 40, 40)
            dark_color = (20, 20, 20)
            outline_color = (180, 180, 180)

        center = (size // 2, size // 2)
        radius = size // 3

        pygame.draw.circle(img, main_color, center, radius)
        pygame.draw.circle(img, outline_color, center, radius, 2)

        symbol = piece
        text = self.small_font.render(symbol, True, outline_color)
        text_rect = text.get_rect(center=center)
        img.blit(text, text_rect)

        self.piece_images[piece] = img

        if filename:
            try:
                pygame.image.save(img, filename)
            except:
                pass

    def choose_color(self):
        waiting = True
        while waiting:
            self.screen.fill(LIGHT_BROWN)

            title = self.big_font.render("Choose Your Color", True, BLACK)
            title_rect = title.get_rect(center=(BOARD_SIZE // 2, 200))
            self.screen.blit(title, title_rect)

            white_btn = pygame.Rect(BOARD_SIZE // 2 - 100, 300, 200, 50)
            pygame.draw.rect(self.screen, WHITE, white_btn)
            pygame.draw.rect(self.screen, BLACK, white_btn, 3)
            white_text = self.font.render("Play as White", True, BLACK)
            white_rect = white_text.get_rect(center=white_btn.center)
            self.screen.blit(white_text, white_rect)

            black_btn = pygame.Rect(BOARD_SIZE // 2 - 100, 380, 200, 50)
            pygame.draw.rect(self.screen, BLACK, black_btn)
            pygame.draw.rect(self.screen, WHITE, black_btn, 3)
            black_text = self.font.render("Play as Black", True, WHITE)
            black_rect = black_text.get_rect(center=black_btn.center)
            self.screen.blit(black_text, black_rect)

            pygame.display.flip()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if white_btn.collidepoint(event.pos):
                        self.player_color = 'white'
                        self.flipped = False
                        waiting = False
                    elif black_btn.collidepoint(event.pos):
                        self.player_color = 'black'
                        self.flipped = True
                        waiting = False

        if self.player_color == 'black':
            self.ai_thinking = True

        return True

    def draw_board(self):
        for row in range(8):
            for col in range(8):
                display_row = 7 - row if self.flipped else row
                display_col = 7 - col if self.flipped else col
                color = LIGHT_BROWN if (display_row + display_col) % 2 == 0 else DARK_BROWN
                pygame.draw.rect(self.screen, color,
                               (col * SQUARE_SIZE, row * SQUARE_SIZE, SQUARE_SIZE, SQUARE_SIZE))

        for i in range(8):
            display_i = 7 - i if self.flipped else i
            letter = chr(ord('a') + display_i)
            text = self.small_font.render(letter, True, BLACK)
            self.screen.blit(text, (i * SQUARE_SIZE + 5, BOARD_SIZE - 20))

            display_number = i + 1 if self.flipped else 8 - i
            number = str(display_number)
            text = self.small_font.render(number, True, BLACK)
            self.screen.blit(text, (5, i * SQUARE_SIZE + 5))

        if self.engine.board.last_move:
            for pos in self.engine.board.last_move:
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                s.set_alpha(100)
                s.fill(LAST_MOVE_COLOR)
                row, col = pos
                display_row = 7 - row if self.flipped else row
                display_col = 7 - col if self.flipped else col
                self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

        if self.selected_piece:
            row, col = self.selected_piece
            display_row = 7 - row if self.flipped else row
            display_col = 7 - col if self.flipped else col
            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(100)
            s.fill(HIGHLIGHT)
            self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

        for move in self.valid_moves:
            row, col = move
            display_row = 7 - row if self.flipped else row
            display_col = 7 - col if self.flipped else col
            center = (display_col * SQUARE_SIZE + SQUARE_SIZE // 2,
                     display_row * SQUARE_SIZE + SQUARE_SIZE // 2)
            pygame.draw.circle(self.screen, GREEN, center, SQUARE_SIZE // 6)

        if self.engine.board.is_in_check(self.engine.board.turn):
            king_pos = self.engine.board.find_king(self.engine.board.board, self.engine.board.turn)
            if king_pos:
                row, col = king_pos
                display_row = 7 - row if self.flipped else row
                display_col = 7 - col if self.flipped else col
                s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
                s.set_alpha(150)
                s.fill(CHECK_COLOR)
                self.screen.blit(s, (display_col * SQUARE_SIZE, display_row * SQUARE_SIZE))

        for row in range(8):
            for col in range(8):
                piece = self.engine.board.board[row][col]
                if piece != '.' and piece in self.piece_images:
                    img = self.piece_images[piece]
                    display_row = 7 - row if self.flipped else row
                    display_col = 7 - col if self.flipped else col
                    x = display_col * SQUARE_SIZE + (SQUARE_SIZE - img.get_width()) // 2
                    y = display_row * SQUARE_SIZE + (SQUARE_SIZE - img.get_height()) // 2
                    self.screen.blit(img, (x, y))

        y_offset = BOARD_SIZE + 10

        if not self.game_over:
            turn_text = f"Turn: {'White' if self.engine.board.turn == 'white' else 'Black'}"
            turn_color = WHITE if self.engine.board.turn == 'white' else BLACK

            turn_surface = self.big_font.render(turn_text, True, turn_color)
            turn_rect = turn_surface.get_rect(topleft=(20, y_offset + 5))
            bg_rect = turn_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, DARK_BROWN, bg_rect)
            pygame.draw.rect(self.screen, turn_color, bg_rect, 2)
            self.screen.blit(turn_surface, (20, y_offset + 5))
        else:
            if self.winner == 'white':
                win_text = "White wins!"
                win_color = WHITE
            elif self.winner == 'black':
                win_text = "Black wins!"
                win_color = BLACK
            else:
                win_text = "Draw!"
                win_color = GRAY

            win_surface = self.big_font.render(win_text, True, win_color)
            win_rect = win_surface.get_rect(topleft=(20, y_offset + 5))
            bg_rect = win_rect.inflate(20, 10)
            pygame.draw.rect(self.screen, DARK_BROWN, bg_rect)
            pygame.draw.rect(self.screen, win_color, bg_rect, 2)
            self.screen.blit(win_surface, (20, y_offset + 5))

        if self.ai_thinking:
            thinking_text = self.small_font.render("AI thinking...", True, BLUE)
            thinking_rect = thinking_text.get_rect(topleft=(20, y_offset + 40))
            think_bg = thinking_rect.inflate(10, 5)
            pygame.draw.rect(self.screen, DARK_BROWN, think_bg)
            self.screen.blit(thinking_text, (20, y_offset + 40))

        flip_btn = pygame.Rect(BOARD_SIZE - 250, y_offset + 5, 70, 35)
        pygame.draw.rect(self.screen, BLUE, flip_btn)
        pygame.draw.rect(self.screen, BLACK, flip_btn, 2)
        flip_text = self.small_font.render("Flip", True, WHITE)
        flip_rect = flip_text.get_rect(center=flip_btn.center)
        self.screen.blit(flip_text, flip_rect)

        restart_btn = pygame.Rect(BOARD_SIZE - 170, y_offset + 5, 70, 35)
        pygame.draw.rect(self.screen, DARK_BROWN, restart_btn)
        pygame.draw.rect(self.screen, BLACK, restart_btn, 2)
        restart_text = self.small_font.render("Restart", True, WHITE)
        restart_rect = restart_text.get_rect(center=restart_btn.center)
        self.screen.blit(restart_text, restart_rect)

        resign_btn = pygame.Rect(BOARD_SIZE - 90, y_offset + 5, 70, 35)
        pygame.draw.rect(self.screen, RED, resign_btn)
        pygame.draw.rect(self.screen, BLACK, resign_btn, 2)
        resign_text = self.small_font.render("Resign", True, WHITE)
        resign_rect = resign_text.get_rect(center=resign_btn.center)
        self.screen.blit(resign_text, resign_rect)

        white_mat, black_mat = self.engine.board.get_material_count()
        panel_rect = pygame.Rect(10, y_offset + 55, BOARD_SIZE - 20, 35)
        pygame.draw.rect(self.screen, GRAY, panel_rect)
        pygame.draw.rect(self.screen, BLACK, panel_rect, 2)

        diff = white_mat - black_mat
        if diff > 0:
            material_text = f"White: {white_mat}  Black: {black_mat} (+{diff})"
            diff_color = WHITE
        elif diff < 0:
            material_text = f"White: {white_mat}  Black: {black_mat} ({diff})"
            diff_color = BLACK
        else:
            material_text = f"White: {white_mat}  Black: {black_mat} (=)"
            diff_color = (200, 200, 0)

        material_surface = self.small_font.render(material_text, True, diff_color)
        material_rect = material_surface.get_rect(center=(BOARD_SIZE // 2, y_offset + 72))
        self.screen.blit(material_surface, material_rect)

        self.buttons['flip'] = flip_btn
        self.buttons['restart'] = restart_btn
        self.buttons['resign'] = resign_btn

    def show_promotion_menu(self):
        menu_rect = pygame.Rect(BOARD_SIZE // 2 - 100, BOARD_SIZE // 2 - 100, 200, 200)
        pygame.draw.rect(self.screen, LIGHT_BROWN, menu_rect)
        pygame.draw.rect(self.screen, BLACK, menu_rect, 3)

        pieces = [('q', 'Queen'), ('r', 'Rook'), ('n', 'Knight'), ('b', 'Bishop')]
        buttons = []

        for i, (piece, name) in enumerate(pieces):
            btn = pygame.Rect(menu_rect.x + 10, menu_rect.y + 10 + i * 45, 180, 40)
            pygame.draw.rect(self.screen, DARK_BROWN, btn)

            piece_key = piece.upper() if self.engine.board.turn == 'white' else piece
            if piece_key in self.piece_images:
                img = pygame.transform.scale(self.piece_images[piece_key], (30, 30))
                self.screen.blit(img, (btn.x + 10, btn.y + 5))

            text = self.font.render(name, True, WHITE)
            self.screen.blit(text, (btn.x + 50, btn.y + 10))
            buttons.append((btn, piece))

        pygame.display.flip()

        while True:
            for event in pygame.event.get():
                if event.type == pygame.MOUSEBUTTONDOWN:
                    for btn, piece in buttons:
                        if btn.collidepoint(event.pos):
                            return piece
                elif event.type == pygame.QUIT:
                    return 'q'

    def handle_click(self, pos):
        if self.game_over or self.engine.board.turn != self.player_color or self.ai_thinking:
            return True

        col = pos[0] // SQUARE_SIZE
        row = pos[1] // SQUARE_SIZE

        if not (0 <= row < 8 and 0 <= col < 8):
            return True

        actual_row = 7 - row if self.flipped else row
        actual_col = 7 - col if self.flipped else col

        if self.selected_piece is None:
            piece = self.engine.board.board[actual_row][actual_col]
            if piece != '.' and self.engine.board.get_piece_color(piece) == self.engine.board.turn:
                self.selected_piece = (actual_row, actual_col)
                moves = self.engine.board.get_piece_moves(actual_row, actual_col)
                self.valid_moves = [move for move in moves
                                   if self.engine.board.is_move_legal((actual_row, actual_col), move)]
        else:
            if (actual_row, actual_col) in self.valid_moves:
                start = self.selected_piece
                end = (actual_row, actual_col)
                piece = self.engine.board.board[start[0]][start[1]]

                if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
                    promotion = self.show_promotion_menu()
                    self.engine.make_move(start, end, promotion)
                else:
                    self.engine.make_move(start, end)

                self.selected_piece = None
                self.valid_moves = []

                if self.engine.board.is_checkmate():
                    self.game_over = True
                    self.winner = 'black' if self.engine.board.turn == 'white' else 'white'
                else:
                    is_draw, draw_reason = self.engine.board.is_draw()
                    if is_draw:
                        self.game_over = True
                        self.winner = None
                    else:
                        self.ai_thinking = True
            else:
                piece = self.engine.board.board[actual_row][actual_col]
                if piece != '.' and self.engine.board.get_piece_color(piece) == self.engine.board.turn:
                    self.selected_piece = (actual_row, actual_col)
                    moves = self.engine.board.get_piece_moves(actual_row, actual_col)
                    self.valid_moves = [move for move in moves
                                       if self.engine.board.is_move_legal((actual_row, actual_col), move)]
                else:
                    self.selected_piece = None
                    self.valid_moves = []

        return True

    def resign(self):
        if not self.game_over:
            self.game_over = True
            if self.player_color == 'white':
                self.winner = 'black'
            else:
                self.winner = 'white'
            self.ai_thinking = False

    def ai_move(self):
        if self.game_over or self.engine.board.turn == self.player_color:
            self.ai_thinking = False
            return

        self.ai_thinking = True

        self.draw_board()
        pygame.display.flip()

        move = self.engine.find_best_move(time_limit=2.0)

        if move:
            start, end = move
            piece = self.engine.board.board[start[0]][start[1]]
            promotion = 'q'
            if piece.lower() == 'p' and (end[0] == 0 or end[0] == 7):
                promotion = 'q'

            self.engine.make_move(start, end, promotion)

            if self.engine.board.is_checkmate():
                self.game_over = True
                self.winner = 'black' if self.engine.board.turn == 'white' else 'white'
            else:
                is_draw, draw_reason = self.engine.board.is_draw()
                if is_draw:
                    self.game_over = True
                    self.winner = None

        self.ai_thinking = False

    def restart_game(self):
        self.engine = ChessEngine()
        self.selected_piece = None
        self.valid_moves = []
        self.game_over = False
        self.winner = None
        self.ai_thinking = False
        self.player_color = None
        self.flipped = False
        self.pgn_copied = False

        if not self.choose_color():
            pygame.quit()
            sys.exit()

    def run(self):
        if not self.choose_color():
            return

        running = True

        while running:
            if self.pgn_copied:
                self.pgn_copy_timer += 1
                if self.pgn_copy_timer > 60:
                    self.pgn_copied = False
                    self.pgn_copy_timer = 0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.buttons:
                        if self.buttons.get('copy_pgn') and self.buttons['copy_pgn'].collidepoint(event.pos):
                            pgn = self.generate_pgn()
                            if self.scrap_available:
                                try:
                                    pygame.scrap.put(pygame.SCRAP_TEXT, pgn.encode())
                                except:
                                    pass
                            self.pgn_copied = True
                            self.pgn_copy_timer = 0
                        elif self.buttons['flip'].collidepoint(event.pos):
                            self.flipped = not self.flipped
                        elif self.buttons['restart'].collidepoint(event.pos):
                            self.restart_game()
                        elif self.buttons['resign'].collidepoint(event.pos):
                            self.resign()
                        elif event.pos[1] < BOARD_SIZE:
                            self.handle_click(event.pos)

            if not self.game_over and self.ai_thinking:
                self.ai_move()

            self.draw_board()
            pygame.display.flip()
            self.clock.tick(FPS)

        pygame.quit()
        sys.exit()

    def generate_pgn(self):
        if not self.engine.board.move_history:
            return ""

        pgn = ""
        move_number = 1
        for i in range(0, len(self.engine.board.move_history), 2):
            pgn += f"{move_number}. "
            white_record = self.engine.board.move_history[i]
            notation = self._move_to_algebraic(white_record)
            pgn += notation + " "

            if i + 1 < len(self.engine.board.move_history):
                black_record = self.engine.board.move_history[i + 1]
                notation = self._move_to_algebraic(black_record)
                pgn += notation + " "

            move_number += 1
            if move_number % 8 == 0:
                pgn += "\n"

        if self.game_over:
            if self.winner == 'white':
                pgn += " 1-0"
            elif self.winner == 'black':
                pgn += " 0-1"
            else:
                pgn += " 1/2-1/2"

        return pgn.strip()

    def _move_to_algebraic(self, move_record):
        piece = move_record['piece']
        start = move_record['start']
        end = move_record['end']
        captured = move_record['captured']
        promotion = move_record['promotion']

        if piece.lower() == 'k' and abs(start[1] - end[1]) == 2:
            return "O-O" if end[1] > start[1] else "O-O-O"

        piece_map = {
            'K': 'K', 'Q': 'Q', 'R': 'R', 'B': 'B', 'N': 'N', 'P': '',
            'k': 'K', 'q': 'Q', 'r': 'R', 'b': 'B', 'n': 'N', 'p': ''
        }
        piece_symbol = piece_map.get(piece, '')

        start_sq = self.engine.board.coord_to_square(start[0], start[1])
        end_sq = self.engine.board.coord_to_square(end[0], end[1])

        if captured != '.':
            notation = (start_sq[0] if piece.lower() == 'p' else piece_symbol) + 'x' + end_sq
        else:
            notation = piece_symbol + end_sq

        if promotion:
            notation += '=' + promotion.upper()

        return notation


if __name__ == "__main__":
    game = ChessGUI()
    game.run()
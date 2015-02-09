import re

"""
The Board class contains the state of a game, which is constituted by the positions of all pieces.
"""
class Board(object):
   WHITE = 'white'
   BLACK = 'black'
   _move_pattern = re.compile('([RNBQK]?)([1-h1-8]?)(x?)([a-h][1-8])(=[NBRQ])?(\+)?')
   
   """
   Create a new Board instance with no pieces.  See Board.initialize() to set up the initial position.
   """
   def __init__(self):
      # We have to keep the pieces doubly indexed.  The pieces array is so that we can find pieces by where
      # they are on the board.  The by_piece dict is so that we can find pieces by type.
      self.en_passant_target = None
      self.check = None
      self.pieces = [None] * 64
      self.to_play = Board.WHITE
      self.by_piece = {
         'N': {Board.WHITE: [], Board.BLACK: []},
         'B': {Board.WHITE: [], Board.BLACK: []},
         'R': {Board.WHITE: [], Board.BLACK: []},
         'Q': {Board.WHITE: [], Board.BLACK: []},
         'P': {Board.WHITE: [], Board.BLACK: []}, #DF: changed name of pawn from ' ' to 'P'
         'K': {Board.WHITE: None, Board.BLACK: None},
      }
      self.callback = None
   
   """
   Populate a board with the initial position.  There is no check to make sure the board in empty, so it
   is recommended that you only call initialize() on a Board instance you've just created.
   """
   def initialize(self):
      for i in range(0, 8):
         Pawn(self, 1, i, Board.WHITE, i)
         Pawn(self, 6, i, Board.BLACK, i)
      
      Rook(self, 0, 0, Board.WHITE, 0)
      Rook(self, 0, 7, Board.WHITE, 1)
      Rook(self, 7, 0, Board.BLACK, 0)
      Rook(self, 7, 7, Board.BLACK, 1)
      Knight(self, 0, 1, Board.WHITE, 0)
      Knight(self, 0, 6, Board.WHITE, 1)
      Knight(self, 7, 1, Board.BLACK, 0)
      Knight(self, 7, 6, Board.BLACK, 1)
      Bishop(self, 0, 2, Board.WHITE, 0)
      Bishop(self, 0, 5, Board.WHITE, 1)
      Bishop(self, 7, 2, Board.BLACK, 0)
      Bishop(self, 7, 5, Board.BLACK, 1)
      Queen(self, 0, 3, Board.WHITE, 0)
      Queen(self, 7, 3, Board.BLACK, 0)
      King(self, 0, 4, Board.WHITE, 0)
      King(self, 7, 4, Board.BLACK, 0)
   
   """
   Register a callback for move events
   """
   def add_move_listener(self, callback):
       self.callback = callback
   
   """
   Get the piece at a given position.  The position can either be a tuple of (rank, file) or text, e.g. "d4".
   """
   def get(self, position):
      rank, file = self._arg_to_rf(position)
      
      return self.pieces[self._rf_to_index(rank, file)]
   
   """
   Get the king of the given color.
   """
   def get_king(self, color):
      return self.by_piece['K'][color]
      
   """
   Place a piece at the given position.  The position can either be a tuple of (rank, file) or text, e.g. "d4".
   """
   def put(self, piece, position):
      rank, file = self._arg_to_rf(position)
      
      self.pieces[self._rf_to_index(rank, file)] = piece
      piece.move(rank, file)
      
      if isinstance(piece, King):
         if self.by_piece[piece.name][piece.color] != None:
            raise ValueError("Attempt to add second %s king" % (piece.color))
         
         self.by_piece[piece.name][piece.color] = piece
      else:
         self.by_piece[piece.name][piece.color].append(piece)
      
   """
   Remove the pieces at a given position.  The position can either be a tuple of (rank, file) or text, e.g. "d4".
   The removed piece is returned.
   """
   def take(self, position):
      rank, file = self._arg_to_rf(position)
      
      i = self._rf_to_index(rank, file)
      piece = self.pieces[i]
      self.pieces[i] = None
      piece.take()
      
      if isinstance(piece, King):
         raise ValueError("Attempt to remove %s king" % (piece.color))
      else:
         self.by_piece[piece.name][piece.color].remove(piece)
      
      return piece
   
   """
   Move the piece at a given position to a given position.   The positions can each be either a tuple of
   (rank, file) or text, e.g. "d4".
   """
   def move(self, src, dest):
      rank1, file1 = self._arg_to_rf(src)
      i1 = self._rf_to_index(rank1, file1)

      if self.pieces[i1] == None:
         raise ValueError('Source square is empty')

      rank2, file2 = self._arg_to_rf(dest)
      i2 = self._rf_to_index(rank2, file2)

      piece = self.pieces[i2]
      self.pieces[i2] = self.pieces[i1]
      self.pieces[i1] = None
      self.pieces[i2].move(rank2, file2)
      
      if self.callback:
          self.callback(self.pieces[i2], src, dest)
      
      return piece
   
   """
   Move a piece by a PGN code, e.g. "d4" or "Nxf6+".
   """
   def movePGN(self, move):
      m = self._move_pattern.match(move)
      
      if m:
         src = m.group(1)
         rf = m.group(2)
         capture = m.group(3)
         dest = m.group(4)
         promotion = m.group(5)
         check = m.group(6)
         
         # DF: Pawns expect their names to be 'P'
         if not src:
            src = 'P'
         
         rank, file = self._position_to_rf(dest)
         
         # Track the capture rank separately in case of en passant
         capture_rank = rank
         
         # Check to see if this is an en passant #DF: changed ' ' for 'P'
         if capture != '' and self.pieces[self._rf_to_index(rank, file)] == None and src == 'P' and \
            self.en_passant_target != None and rank == self.en_passant_target[0] and \
            file == self.en_passant_target[1]:
            capture_rank = self.en_passant_target[2]
         elif capture != '' and self.pieces[self._rf_to_index(rank, file)] == None:
            raise ValueError('Capture is not possible: %s' % move)
            
         # Find the piece of the given type that can make the given move.
         piece = self._find_piece(src, (rank, file), rf, capture != '')
         
         if not piece:
            raise ValueError('Move is not possible: %s' % move)
         
         # If it's a capture, remove the captured piece
         if capture != '':
            self.take((capture_rank, file))
            
         if type(piece) == Pawn and piece.file == file and abs(piece.rank - rank) == 2:
            # Store the square that could be attacked en passant
            self.en_passant_target = (rank + (piece.rank - rank) / 2, file, rank)
         else:
            self.en_passant_target = None
            
         if not promotion:
            # Move the given piece to the given destination
            self.move((piece.rank, piece.file), (rank, file))
         else:
            if self.callback:
                self.callback(piece, (piece.rank, piece.file), (rank, file))

            # Swap out the pawn for the promoted piece
            self.take((piece.rank, piece.file))
            
            if promotion == '=N':
               Knight(self, rank, file, self.to_play, len(self.by_piece['N'][piece.color])) #DF: added ids
            elif promotion == '=B':
               Bishop(self, rank, file, self.to_play, len(self.by_piece['B'][piece.color]))
            elif promotion == '=R':
               Rook(self, rank, file, self.to_play, len(self.by_piece['R'][piece.color]))
            elif promotion == '=Q':
               Queen(self, rank, file, self.to_play, len(self.by_piece['Q'][piece.color]))
            else:
               raise ValueError("Promotion is not valid: %s" % move)
         # Toggle who's turn it is
         if self.to_play == Board.WHITE:
            self.to_play = Board.BLACK
         else:
            self.to_play = Board.WHITE

         # If the player was in check, make sure he isn't still
         if self.check:
            king = self.by_piece['K'][self.check]
            
            for piece_type in self.by_piece.keys():
               if piece_type != 'K':
                  for piece in self.by_piece[piece_type][self.to_play]:
                     if piece.reach((king.rank, king.file), True):
                        print piece
                        raise ValueError('Check not resolved by %s' % move)
                     
         # Record who's in check, even though we don't do anything with it yet
         if check != '':
            self.check = self.to_play
         else:
            self.check = None
         
      # Queen-side castle
      elif move.startswith('O-O-O'):
         if self.to_play == Board.WHITE and type(self.pieces[self._rf_to_index(0, 4)]) == King and \
            type(self.pieces[self._rf_to_index(0, 0)]) == Rook and \
            self.pieces[self._rf_to_index(0, 1)] == None and \
            self.pieces[self._rf_to_index(0, 2)] == None and \
            self.pieces[self._rf_to_index(0, 3)] == None:
            self.move((0, 0), (0, 3))
            self.move((0, 4), (0, 2))
         elif self.to_play == Board.BLACK and type(self.pieces[self._rf_to_index(7, 4)]) == King and \
            type(self.pieces[self._rf_to_index(7, 0)]) == Rook and \
            self.pieces[self._rf_to_index(7, 1)] == None and \
            self.pieces[self._rf_to_index(7, 2)] == None and \
            self.pieces[self._rf_to_index(7, 3)] == None:
            self.move((7, 0), (7, 3))
            self.move((7, 4), (7, 2))
         else:
            raise ValueError('Castle is not possible')
         
         # Toggle who's turn it is
         if self.to_play == Board.WHITE:
            self.to_play = Board.BLACK
         else:
            self.to_play = Board.WHITE
         pass
      
         if move[-1] == '+':
            self.check = self.to_play
         else:
            self.check = None
      # King-side castle
      elif move.startswith('O-O'):
         if self.to_play == Board.WHITE and type(self.pieces[self._rf_to_index(0, 4)]) == King and \
            type(self.pieces[self._rf_to_index(0, 7)]) == Rook and \
            self.pieces[self._rf_to_index(0, 5)] == None and \
            self.pieces[self._rf_to_index(0, 6)] == None:
            self.move((0, 7), (0, 5))
            self.move((0, 4), (0, 6))
         elif self.to_play == Board.BLACK and type(self.pieces[self._rf_to_index(7, 4)]) == King and \
            type(self.pieces[self._rf_to_index(7, 7)]) == Rook and \
            self.pieces[self._rf_to_index(7, 5)] == None and \
            self.pieces[self._rf_to_index(7, 6)] == None:
            self.move((7, 7), (7, 5))
            self.move((7, 4), (7, 6))
         else:
            raise ValueError('Castle is not possible')
         
         # Toggle who's turn it is
         if self.to_play == Board.WHITE:
            self.to_play = Board.BLACK
         else:
            self.to_play = Board.WHITE
      
         if move[-1] == '+':
            self.check = self.to_play
         else:
            self.check = None
      else:
         raise ValueError('Bad move definition: %s' % move)
      
   """
   Set which color is to play next.
   """
   def set_to_play(self, color):
      self.to_play = color
   
   """
   Return a string that uniquely represents this board position.
   """
   def encode(self):
      encoding = ''
      
      for piece in self.pieces:
         if piece == None:
            encoding += 'x'
         elif type(piece) == Rook and piece.color == Board.WHITE:
            encoding += 'R'
         elif type(piece) == Rook and piece.color == Board.BLACK:
            encoding += 'r'
         elif type(piece) == Knight and piece.color == Board.WHITE:
            encoding += 'N'
         elif type(piece) == Knight and piece.color == Board.BLACK:
            encoding += 'n'
         elif type(piece) == Bishop and piece.color == Board.WHITE:
            encoding += 'B'
         elif type(piece) == Bishop and piece.color == Board.BLACK:
            encoding += 'b'
         elif type(piece) == Queen and piece.color == Board.WHITE:
            encoding += 'Q'
         elif type(piece) == Queen and piece.color == Board.BLACK:
            encoding += 'q'
         elif type(piece) == King and piece.color == Board.WHITE:
            encoding += 'K'
         elif type(piece) == King and piece.color == Board.BLACK:
            encoding += 'k'
         elif type(piece) == Pawn and piece.color == Board.WHITE:
            encoding += 'P'
         elif type(piece) == Pawn and piece.color == Board.BLACK:
            encoding += 'p'
         else:
            raise Error('Unknown piece type: %s' % type(piece))
      
      return encoding
   
   #DF: SHANNON's evaluation function
   def evaluate(self):
      
      kings={}
      queens={}
      rooks={}
      bishops={}
      knights={}
      pawns={}
      
      kings[Board.WHITE] = 1 if type(self.by_piece['K'][Board.WHITE])!=list else len(self.by_piece['K'][Board.WHITE]) 
      queens[Board.WHITE] = 1 if type(self.by_piece['Q'][Board.WHITE])!=list else len(self.by_piece['Q'][Board.WHITE])
      rooks[Board.WHITE] = 1 if type(self.by_piece['R'][Board.WHITE])!=list else len(self.by_piece['R'][Board.WHITE])
      bishops[Board.WHITE] = 1 if type(self.by_piece['B'][Board.WHITE])!=list else len(self.by_piece['B'][Board.WHITE])
      knights[Board.WHITE] = 1 if type(self.by_piece['N'][Board.WHITE])!=list else len(self.by_piece['N'][Board.WHITE])
      pawns[Board.WHITE] = 1 if type(self.by_piece['P'][Board.WHITE])!=list else len(self.by_piece['P'][Board.WHITE])

      kings[Board.BLACK] = 1 if type(self.by_piece['K'][Board.BLACK])!=list else len(self.by_piece['K'][Board.BLACK])
      queens[Board.BLACK] = 1 if type(self.by_piece['Q'][Board.BLACK])!=list else len(self.by_piece['Q'][Board.BLACK])
      rooks[Board.BLACK] = 1 if type(self.by_piece['R'][Board.BLACK])!=list else len(self.by_piece['R'][Board.BLACK])
      bishops[Board.BLACK] = 1 if type(self.by_piece['B'][Board.BLACK])!=list else len(self.by_piece['B'][Board.BLACK])
      knights[Board.BLACK] = 1 if type(self.by_piece['N'][Board.BLACK])!=list else len(self.by_piece['N'][Board.BLACK])
      pawns[Board.BLACK] = 1 if type(self.by_piece['P'][Board.BLACK])!=list else len(self.by_piece['P'][Board.BLACK])
      
      isolated_pawns = {}
      isolated_pawns[Board.BLACK]=0
      isolated_pawns[Board.WHITE]=0
      doubled_pawns = {}
      doubled_pawns[Board.BLACK]=0
      doubled_pawns[Board.WHITE]=0
      backward_pawns = {}
      backward_pawns[Board.BLACK]=0
      backward_pawns[Board.WHITE]=0
      
      mobility = {}
      mobility[Board.BLACK]=0
      mobility[Board.WHITE]=0
      
      for r in range(8):
         for f in range(8):
            piece = self.get((r,f))
            
            if piece!=None:
               mobility[piece.color] += self.mobility(piece)
               
               if type(piece) == Pawn:
                  is_isolated = True
                  is_doubled = False
                  is_backward = False
                  
                  #check one side
                  if piece.file>0:
                     i=0
                     while i<8 and is_isolated:
                        neighbor = self.get((i, piece.file-1))
                        i+=1
                        if type(neighbor)==Pawn and neighbor.color==piece.color:
                           is_isolated = not is_isolated
                     
                     if piece.rank<6 and piece.color==Board.WHITE:      
                        piece1 = self.get((piece.rank+1, piece.file-1))
                        piece2 = self.get((piece.rank+2, piece.file-1))
                        if not is_backward and piece.color==Board.WHITE and type(piece1)==Pawn and piece1.color==Board.WHITE and type(piece2)==Pawn and piece2.color==Board.BLACK:
                           is_backward = not is_backward
                     if piece.rank>1 and piece.color==Board.BLACK:      
                        piece1 = self.get((piece.rank-1, piece.file-1))
                        piece2 = self.get((piece.rank-2, piece.file-1))
                        if not is_backward and piece.color==Board.WHITE and type(piece1)==Pawn and piece1.color==Board.WHITE and type(piece2)==Pawn and piece2.color==Board.BLACK:
                           is_backward = not is_backward
                  
                  #check the other side 
                  if piece.file<7:
                     i=0
                     while i<8 and is_isolated:
                        neighbor = self.get((i, piece.file+1))
                        i+=1
                        if type(neighbor)==Pawn and neighbor.color==piece.color:
                           is_isolated = not is_isolated
                     
                     if piece.rank<6 and piece.color==Board.WHITE:      
                        piece1 = self.get((piece.rank+1, piece.file+1))
                        piece2 = self.get((piece.rank+2, piece.file+1))
                        if not is_backward and piece.color==Board.WHITE and type(piece1)==Pawn and piece1.color==Board.WHITE and type(piece2)==Pawn and piece2.color==Board.BLACK:
                           is_backward = not is_backward
                     if piece.rank>1 and piece.color==Board.BLACK:      
                        piece1 = self.get((piece.rank-1, piece.file+1))
                        piece2 = self.get((piece.rank-2, piece.file+1))
                        if not is_backward and piece.color==Board.WHITE and type(piece1)==Pawn and piece1.color==Board.WHITE and type(piece2)==Pawn and piece2.color==Board.BLACK:
                           is_backward = not is_backward 
                  #check same file 
                  i=0
                  while i<8 and not is_doubled:
                     neighbor = self.get(self._rf_to_position(i, piece.file))
                     i+=1
                     if type(neighbor)==Pawn and neighbor.color==piece.color and neighbor!=piece:
                        is_doubled = not is_doubled
                                          
                  isolated_pawns[piece.color]+=1*is_isolated
                  doubled_pawns[piece.color]+=1*is_doubled
                  backward_pawns[piece.color]+=1*is_backward
               
      eval_f = {}
      eval_f[Board.WHITE] = 200*(kings[Board.WHITE]-kings[Board.BLACK]) + 9*(queens[Board.WHITE]-queens[Board.BLACK]) + \
                     5*(rooks[Board.WHITE]-rooks[Board.BLACK]) + 3*(bishops[Board.WHITE]-bishops[Board.BLACK]+ \
                     knights[Board.WHITE]-knights[Board.BLACK])+ (pawns[Board.WHITE]-pawns[Board.BLACK]) - \
                     0.5*(doubled_pawns[Board.WHITE]-doubled_pawns[Board.BLACK]+backward_pawns[Board.WHITE]-backward_pawns[Board.BLACK]+isolated_pawns[Board.WHITE]-isolated_pawns[Board.BLACK]) + \
                     0.1*(mobility[Board.WHITE]-mobility[Board.BLACK])
      
      eval_f[Board.BLACK] = -eval_f[Board.WHITE] 
      return eval_f
   
   def mobility(self, piece):
      #DF: I have to add the special case for pawns
      mobility = 0
      for r in range(8):
         for f in range(8):
            if r!=piece.rank and f!=piece.file:
               mobility += 1*piece.reach((r, f))
      return mobility
            
   
   """
   Search for the piece of a given type that can make a specified move.  The src is the name of the piece type, e.g.
   'K'.  The dest is either a tuple of (rank, file) or text, e.g. "d4".  The modifier is a rank of file name used
   to disambiguate which piece is intended.  The capture field is whether the move is a capture.  The capture field
   is really only relevant to pawns.
   """
   def _find_piece(self, src, dest, modifier='', capture=False):
      list = self.by_piece[src][self.to_play]
      rank = None
      file = None
      
      # If there's a disambiguating modifier, as in Nfxd4, then parse it.
      if modifier:
         try:
            rank = int(modifier) - 1
         except ValueError:
            file = ord(modifier) - 97
            
      if (rank and (rank < 0 or rank > 7)) or (file and (file < 0 or file > 7)):
         raise ValueError("Bad piece identifier: %s" % dest)
      
      ret = None
      pinned = []
      
      # King's work differently, so handle everything else separately.
      if src != 'K':
         # Get the list of pieces that can't move.
         pinned = self._get_pinned(dest)

         # If there's a modifier that disambiguates by rank, find a piece on the given rank that's not pinned
         # that can reach the destination.
         if rank != None:
            for piece in list:
               if piece.rank == rank and piece.reach(dest, capture) and piece not in pinned:
                  ret = piece
                  break
         # If there's a modifier that disambiguates by file, find a piece on the given file that's not pinned
         # that can reach the destination.
         elif file != None:
            for piece in list:
               if piece.file == file and piece.reach(dest, capture) and piece not in pinned:
                  ret = piece
                  break
         # Otherwise, just find a piece that can reach the destination and isn't pinned.
         else:
            for piece in list:
               if piece.reach(dest, capture) and piece not in pinned:
                  ret = piece
                  break
      # Kings are easy: if they can reach the destination, they're the piece we want.
      elif self.by_piece[src][self.to_play].reach(self._arg_to_rf(dest), capture):
         ret = self.by_piece[src][self.to_play]
               
      return ret
   
   """
   Get the list of pieces that are unable to move because they are pinned.  Most of the time this list will be empty.
   Rarely will it have more than one entry.  The rf argument is the piece to be excluded from the search, most
   likely because it's the piece being captured.
   """
   def _get_pinned(self, rf=None):
      pinned = set()
      rank, file = rf
      other_color = Board.WHITE
      
      if self.to_play == Board.WHITE:
         other_color = Board.BLACK
         
      king = self.by_piece['K'][self.to_play]
      
      # Look at all of the opponent's rooks, bishops, and queens, and determine if any of them have any
      # pieces pinned.
      for piece in self.by_piece['R'][other_color]:
         pinnee = piece.pinned()
         
         # Once we have the pinned piece, we check to see if it's moving along the line of the pin.
         # If it is, then we don't declare it pinned because for this move, it effectively isn't.
         if pinnee and ((piece.rank == king.rank and rank != king.rank) or \
            (piece.file == king.file and file != king.file)):
            # A piece can only be pin and be pinned once
            pinned.add(pinnee)

      for piece in self.by_piece['B'][other_color]:
         pinnee = piece.pinned()
         
         # Once we have the pinned piece, we check to see if it's moving along the line of the pin.
         # If it is, then we don't declare it pinned because for this move, it effectively isn't.
         # The logic here is pretty complicated.  The idea is that the line of the pin can be represented as the
         # slope of the line between the pinning piece and the king.  If the slope of the line between the move
         # destination and the king isn't the same, then it's not along the line of the pin.  The one place where
         # this fails is if the pinned piece jumps to the other side of the pinning piece or king, which thankfully
         # is against the rules.  Only the knight can jump other pieces, but a knight couldn't stay on the pin line.
         #
         # Let me also explain the logic of how I'm testing that.  To avoid divide by zero errors, we don't calculate
         # the slope directly.  First, we make sure the destination is on the pin line.  If it is, we can reduce the
         # slope to either 1 or -1, which let's us arrange the math differently.  The max() in the comparison is to
         # avoid divide by zero.  When the value in the denominator would otherwise be 0, the value in the
         # numerator is also zero, which means we don't care what's in the denominator.
         if pinnee and not (rank == piece.rank and file == piece.file) and (abs(rank - king.rank) != abs(file - king.file) or \
            ((rank - king.rank) / max(1, abs(rank - king.rank)) != (piece.rank - rank) / max(1, abs(piece.rank - rank))) or \
            ((file - king.file) / max(1, abs(file - king.file)) != (piece.file - file) / max(1, abs(piece.file - file)))):
            # A piece can only be pin and be pinned once
            pinned.add(pinnee)

      for piece in self.by_piece['Q'][other_color]:
         pinnee = piece.pinned()
         
         # Once we have the pinned piece, we check to see if it's moving along the line of the pin.
         # If it is, then we don't declare it pinned because for this move, it effectively isn't.
         # See the comment for the bishop above.
         if pinnee and not (rank == piece.rank and file == piece.file) and ((piece.rank == king.rank and rank != king.rank) or \
            (piece.file == king.file and file != king.file) or \
            ((piece.rank != king.rank and piece.file != king.file) and \
            (abs(rank - king.rank) != abs(file - king.file) or \
            ((rank - king.rank) / max(1, abs(rank - king.rank)) != (piece.rank - rank) / max(1, abs(piece.rank - rank))) or \
            ((file - king.file) / max(1, abs(file - king.file)) != (piece.file - file) / max(1, abs(piece.file - file)))))):
            # A piece can only be pin and be pinned once
            pinned.add(pinnee)

      return pinned
   
   """
   Return the Board and all pieces as a printable string.
   """
   def __str__(self):
      s = ''
      
      for r in range(7, -1, -1):
         s += '+---' * 8 + '+\n'
         
         for f in range(0, 8):
            s += '|'
            
            i = self._rf_to_index(r, f)
            
            if self.pieces[i] == None:
               s += '   '
            elif self.pieces[i].color == Board.WHITE:
               s += str(self.pieces[i])
            else:
               s += str(self.pieces[i]).lower()

         s += '|\n'
      
      s += '+---' * 8 + '+'
      
      return s
   
   """
   Create a board from an encoding string.
   """
   @staticmethod
   def decode(encoding):
      b = Board()
      
      for i, c in enumerate(encoding):
         rank, file = Board._index_to_rf(i)
         
         if c == 'R':
            Rook(b, rank, file, Board.WHITE)
         elif c == 'r':
            Rook(b, rank, file, Board.BLACK)
         elif c == 'N':
            Knight(b, rank, file, Board.WHITE)
         elif c == 'n':
            Knight(b, rank, file, Board.BLACK)
         elif c == 'B':
            Bishop(b, rank, file, Board.WHITE)
         elif c == 'b':
            Bishop(b, rank, file, Board.BLACK)
         elif c == 'Q':
            Queen(b, rank, file, Board.WHITE)
         elif c == 'q':
            Queen(b, rank, file, Board.BLACK)
         elif c == 'K':
            King(b, rank, file, Board.WHITE)
         elif c == 'k':
            King(b, rank, file, Board.BLACK)
         elif c == 'P':
            Pawn(b, rank, file, Board.WHITE)
         elif c == 'p':
            Pawn(b, rank, file, Board.BLACK)
            
      return b

   """
   Test that the rank and file values are valid
   """
   @staticmethod
   def _test_rank_file(rank, file):
      if file < 0 or file > 7 or rank < 0 or rank > 8:
         raise ValueError('Rank or file out of range')
      
   """
   Translate a position string into a rank and file.
   """
   @staticmethod
   def _position_to_rf(position):
      if len(position) != 2:
         raise ValueError()
      
      rank = int(position[1]) - 1
      file = ord(position[0]) - 97

      return (rank, file)

   """
   Translate a rank and file into a position string.
   """
   @staticmethod
   def _rf_to_position(rank, file):
      return chr(file + 97) + str(rank + 1)
      
   """
   Translate a position argument (either a (rank, file) tuple or position string) into a (rank, file) tuple.
   """
   @staticmethod
   def _arg_to_rf(position):
      p = position
      
      if type(position) == str:
         p = Board._position_to_rf(position)
      
      return p
      
   """
   Translate a rank and file into an array index for the Board.pieces array.
   """
   @staticmethod
   def _rf_to_index(rank, file):
      Board._test_rank_file(rank, file)

      return file * 8 + rank
      
   """
   Translate an array index for the Board.pieces array into a rank and file.
   """
   @staticmethod
   def _index_to_rf(index):
      if index < 0 or index > 63:
         raise ValueError('Bad index: %d', index)

      return (index % 8, index / 8)

      
"""
Piece is the base class for all piece types.
"""
class Piece(object):
   board = None
   name = None
   rank = None
   file = None
   color = None
   id = None
   
   def __init__(self, b, r, f, c, n, id): #DF: added id
      self.board = b
      self.rank = r
      self.file = f
      self.name = n
      self.color = c
      self.id = id
      
      self.board.put(self, (r, f))
      
   def move(self, r, f):
      self.rank = r
      self.file = f
      
   def take(self):
      self.rank = None
      self.file = None
      
   def nodename(self):
      return str(self.color)[0] + self.name + str(self.id)
      
   """
   Return whether this piece can reach the given destination in a single move.  The destination is given as the
   rf tuple of (rank, file).  The capture argument indicates whether the move is a capture, which is really only
   relevant to pawns.
   """
   def reach(self, rf, capture=False):
      return False
   
   """
   Return the piece pinned by this piece, if any.  This method only applies to Rooks, Bishops, and Queens.
   """
   def pinned(self):
      return []

   """
   Return the squares covered by this piece.
   """
   def covers(self):
      return []
    
   """
   Return the squares that could be reached by this pieces.
   """
   def reaches(self):
      return [(r,f) for r,f in self.covers()
               if self.board.get((r,f)) == None or self.board.get((r,f)).color != self.color]
   
   def __str__(self):
      return self.name + chr(self.file + 97) + str(self.rank + 1)
   
class Pawn(Piece):
   def __init__(self, b, r, f, c, id): #DF: added id
      super(Pawn, self).__init__(b, r, f, c, 'P', id)
   
   def reach(self, rf, capture=False):
      r, f = rf
      
      # Pawn's are wonky.  They depend on their colors, whether they've moved before, and whether they're capturing.
      # And then there's the en passant, which is handled by the Board class because it requires knowledge of the
      # previous move.
      return (self.color == Board.WHITE and \
            ((not capture and self.file == f and \
               (self.rank == r - 1 or (self.rank == 1 and r == 3 and self.board.get((2, f)) == None))) or \
             (capture and abs(self.file - f) == 1 and r - self.rank == 1))) or \
         (self.color == Board.BLACK and \
            ((not capture and self.file == f and \
               (self.rank == r + 1 or (self.rank == 6 and r == 4 and self.board.get((5, f)) == None))) or \
             (capture and abs(self.file - f) == 1 and self.rank - r == 1)))
   
   def covers(self):
      ret = []
      
      if self.color == Board.WHITE and self.rank < 7:
         if self.file > 0:
            ret.append((self.rank + 1, self.file - 1))
         if self.file < 7:
            ret.append((self.rank + 1, self.file + 1))
      elif self.color == Board.BLACK and self.rank > 0:
         if self.file > 0:
            ret.append((self.rank - 1, self.file - 1))
         if self.file < 7:
            ret.append((self.rank - 1, self.file + 1))
            
      return ret
   
   def reaches(self):
      ret = []
      
      if self.color == Board.WHITE and self.rank < 7:
         if self.board.get((self.rank + 1, self.file)) == None:
            ret.append((self.rank + 1, self.file))

            if self.rank == 1 and self.board.get((3, self.file)) == None:
               ret.append((3, self.file))
               
         if self.file > 0 and self.board.get((self.rank + 1, self.file - 1)) != None and \
               self.board.get((self.rank + 1, self.file - 1)).color != self.color:
            ret.append((self.rank + 1, self.file - 1))
            
         if self.file < 7 and self.board.get((self.rank + 1, self.file + 1)) != None and \
               self.board.get((self.rank + 1, self.file + 1)).color != self.color:
            ret.append((self.rank + 1, self.file + 1))
      elif self.color == Board.BLACK and self.rank > 0:
         if self.board.get((self.rank - 1, self.file)) == None:
            ret.append((self.rank - 1, self.file))

            if self.rank == 6 and self.board.get((4, self.file)) == None:
               ret.append((4, self.file))
         
         if self.file > 0 and self.board.get((self.rank - 1, self.file - 1)) != None and \
               self.board.get((self.rank - 1, self.file - 1)).color != self.color:
            ret.append((self.rank - 1, self.file - 1))
         
         if self.file < 7 and self.board.get((self.rank - 1, self.file + 1)) != None and \
               self.board.get((self.rank - 1, self.file + 1)).color != self.color:
            ret.append((self.rank - 1, self.file + 1))
            
      return ret
   
class Rook(Piece):
   def __init__(self, b, r, f, c, id): #DF: added id
      super(Rook, self).__init__(b, r, f, c, 'R', id)
   
   def reach(self, rf, capture=False):
      r, f = rf
      ret = False

      # If we're on the same file, check if the rank is blocked
      if self.file == f:
         step = (r - self.rank) / abs(r - self.rank)
         ret = True
         
         for i in range(self.rank + step, r, step):
            if self.board.get((i, f)) != None:
               ret = False
               break
      # If we're on the same rank, check if the file is blocked
      elif self.rank == r:
         step = (f - self.file) / abs(f - self.file)
         ret = True
               
         for i in range(self.file + step, f, step):
            if self.board.get((r, i)) != None:
               ret = False
               break
      
      return ret
   
   def pinned(self):
      pinned = None
      other_color = Board.WHITE
      
      if (self.color == Board.WHITE):
         other_color = Board.BLACK
         
      king = self.board.by_piece['K'][other_color]

      # If we're on the same file as the king, check if there is exactly one piece between us and the king.
      if self.file == king.file:
         step = (king.rank - self.rank) / abs(king.rank - self.rank)
         
         for i in range(self.rank + step, king.rank, step):
            blocker = self.board.get((i, king.file))

            # Found the first piece between us and the king
            if blocker != None and not pinned:
               pinned = blocker
            # Oops. Found a second piece between us and the king
            elif blocker != None:
               pinned = None
               break
      # If we're on the same rank as the king, check if there is exactly one piece between us and the king.             
      elif self.rank == king.rank:
         step = (king.file - self.file) / abs(king.file - self.file)
               
         for i in range(self.file + step, king.file, step):
            blocker = self.board.get((king.rank, i))

            # Found the first piece between us and the king
            if blocker != None and not pinned:
               pinned = blocker
            # Oops. Found a second piece between us and the king
            elif blocker != None:
               pinned = None
               break
      
      return pinned

   def covers(self):
      ret = []
      
      for r in range(self.rank - 1, -1, -1):
         ret.append((r, self.file))
         
         if self.board.pieces[Board._rf_to_index(r, self.file)]:
            break
      
      for r in range(self.rank + 1, 8):
         ret.append((r, self.file))
         
         if self.board.pieces[Board._rf_to_index(r, self.file)]:
            break
      
      for f in range(self.file - 1, -1, -1):
         ret.append((self.rank, f))
         
         if self.board.pieces[Board._rf_to_index(self.rank, f)]:
            break
      
      for f in range(self.file + 1, 8):
         ret.append((self.rank, f))
         
         if self.board.pieces[Board._rf_to_index(self.rank, f)]:
            break
      
      return ret

class Bishop(Piece):
   def __init__(self, b, r, f, c, id): #DF: added id
      super(Bishop, self).__init__(b, r, f, c, 'B', id)
   
   def reach(self, rf, capture=False):
      r, f = rf
      ret = False
      
      # If we're on the same diagonal, check if there's a piece between us
      if abs(self.rank - r) == abs(self.file - f):
         ret = True
         
         # Figure out which direction to the target
         r_fact = (r - self.rank) / max(1, abs(r - self.rank))
         f_fact = (f - self.file) / max(1, abs(f - self.file))
         
         for i in range(1, abs(r - self.rank)):
            if self.board.get((self.rank + i * r_fact, self.file + i * f_fact)) != None:
               ret = False
               break
               
      return ret
   
   def pinned(self):
      pinned = None
      other_color = Board.WHITE
      
      if (self.color == Board.WHITE):
         other_color = Board.BLACK
         
      king = self.board.by_piece['K'][other_color]

      # If we're on the same diagonal as the king, check if there's exactly one piece between us
      if abs(self.rank - king.rank) == abs(self.file - king.file):
         # Figure out which direction to the king
         r_fact = (king.rank - self.rank) / max(1, abs(king.rank - self.rank))
         f_fact = (king.file - self.file) / max(1, abs(king.file - self.file))
         
         for i in range(1, abs(king.rank - self.rank)):
            blocker = self.board.get((self.rank + i * r_fact, self.file + i * f_fact))
            
            # We found the first piece between us and the king.
            if blocker != None and not pinned:
               pinned = blocker
            # Oops.  We found a second piece between us and the king.
            elif blocker != None:
               pinned = None
               break
         
      return pinned
   
   def covers(self):
      ret = []
      
      for m in range(1, min(7 - self.rank, 7 - self.file) + 1):
         ret.append((self.rank + m, self.file + m))
         
         if self.board.pieces[Board._rf_to_index(self.rank + m, self.file + m)]:
            break
      
      for m in range(1, min(self.rank, 7 - self.file) + 1):
         ret.append((self.rank - m, self.file + m))
         
         if self.board.pieces[Board._rf_to_index(self.rank - m, self.file + m)]:
            break
      
      for m in range(1, min(self.rank, self.file) + 1):
         ret.append((self.rank - m, self.file - m))
         
         if self.board.pieces[Board._rf_to_index(self.rank - m, self.file - m)]:
            break
      
      for m in range(1, min(7 - self.rank, self.file) + 1):
         ret.append((self.rank + m, self.file - m))
         
         if self.board.pieces[Board._rf_to_index(self.rank + m, self.file - m)]:
            break
      
      return ret
   
class Knight(Piece):
   def __init__(self, b, r, f, c, id): #DF: added id
      super(Knight, self).__init__(b, r, f, c, 'N', id)
      
   def reach(self, rf, capture=False):
      r, f = rf
      ret = False
      
      if (abs(self.rank - r) == 2 and abs(self.file - f) == 1) or \
         (abs(self.rank - r) == 1 and abs(self.file - f) == 2):
         ret = True
      
      return ret
   
   def covers(self):
      return [(r,f) for r,f in
                  [(self.rank + r, self.file + f) for r in [-2, -1, 1, 2]
                  for f in [-2, -1, 1, 2]
                  if abs(r) != abs(f)]
               if r >= 0 and r <= 7 and f >= 0 and f <= 7]
   
class King(Piece):
   def __init__(self, b, r, f, c, id): #DF: added id
      super(King, self).__init__(b, r, f, c, 'K', id)
      
   def reach(self, rf, capture=False):
      r, f = rf
      ret = False
      
      if abs(self.rank - r) <= 1 and abs(self.file - f) <= 1:
         ret = True
      
      return ret
   
   def covers(self):
      return [(r, f) for r in range(max(0, self.rank - 1), min(8, self.rank + 2))
                     for f in range(max(0, self.file - 1), min(8, self.file + 2))
                     if r != self.rank or f != self.file]
   
class Queen(Piece):
   def __init__(self, b, r, f, c, id): #DF: added id
      super(Queen, self).__init__(b, r, f, c, 'Q', id)
   
   def reach(self, rf, capture=False):
      r, f = rf
      ret = False
      
      # If we're on the same file, check if the rank is blocked
      if self.file == f:
         step = (r - self.rank) / abs(r - self.rank)
         ret = True
         
         for i in range(self.rank + step, r, step):
            if self.board.get((i, f)) != None:
               ret = False
               break
      # If we're on the same rank, check if the file is blocked
      elif self.rank == r:
         step = (f - self.file) / abs(f - self.file)
         ret = True
               
         for i in range(self.file + step, f, step):
            if self.board.get((r, i)) != None:
               ret = False
               break
      # If we're on the same diagonal, check if there's a piece between us
      elif abs(self.rank - r) == abs(self.file - f):
         ret = True
         
         # Figure out which direction to the target
         r_fact = (r - self.rank) / max(1, abs(r - self.rank))
         f_fact = (f - self.file) / max(1, abs(f - self.file))
         
         for i in range(1, abs(r - self.rank)):
            if self.board.get((self.rank + i * r_fact, self.file + i * f_fact)) != None:
               ret = False
               break
      
      return ret

   def pinned(self):
      pinned = None
      other_color = Board.WHITE
      
      if (self.color == Board.WHITE):
         other_color = Board.BLACK
         
      king = self.board.by_piece['K'][other_color]

      # If we're on the same file as the king, check if there is exactly one piece between us and the king.
      if self.file == king.file:
         step = (king.rank - self.rank) / abs(king.rank - self.rank)
         
         for i in range(self.rank + step, king.rank, step):
            blocker = self.board.get((i, king.file))
            
            # We found the first piece between us and the king.
            if blocker != None and not pinned:
               pinned = blocker
            # Oops.  We found a second piece between us and the king.
            elif blocker != None:
               pinned = None
               break
      # If we're on the same rank as the king, check if there is exactly one piece between us and the king.
      elif self.rank == king.rank:
         step = (king.file - self.file) / abs(king.file - self.file)
               
         for i in range(self.file + step, king.file, step):
            blocker = self.board.get((king.rank, i))
            
            # We found the first piece between us and the king.
            if blocker != None and not pinned:
               pinned = blocker
            # Oops.  We found a second piece between us and the king.
            elif blocker != None:
               pinned = None
               break
      # If we're on the same diagonal as the king, check if there's exactly one piece between us
      elif abs(self.rank - king.rank) == abs(self.file - king.file):
         # Figure out which direction to the king
         r_fact = (king.rank - self.rank) / max(1, abs(king.rank - self.rank))
         f_fact = (king.file - self.file) / max(1, abs(king.file - self.file))
         
         for i in range(1, abs(king.rank - self.rank)):
            blocker = self.board.get((self.rank + i * r_fact, self.file + i * f_fact))

            # We found the first piece between us and the king.
            if blocker != None and not pinned:
               pinned = blocker
            # Oops.  We found a second piece between us and the king.
            elif blocker != None:
               pinned = None
               break
      
      return pinned

   def covers(self):
      ret = []
      
      for r in range(self.rank - 1, -1, -1):
         ret.append((r, self.file))
         
         if self.board.pieces[Board._rf_to_index(r, self.file)]:
            break
      
      for r in range(self.rank + 1, 8):
         ret.append((r, self.file))
         
         if self.board.pieces[Board._rf_to_index(r, self.file)]:
            break
      
      for f in range(self.file - 1, -1, -1):
         ret.append((self.rank, f))
         
         if self.board.pieces[Board._rf_to_index(self.rank, f)]:
            break
      
      for f in range(self.file + 1, 8):
         ret.append((self.rank, f))
         
         if self.board.pieces[Board._rf_to_index(self.rank, f)]:
            break
      
      for m in range(1, min(7 - self.rank, 7 - self.file) + 1):
         ret.append((self.rank + m, self.file + m))
         
         if self.board.pieces[Board._rf_to_index(self.rank + m, self.file + m)]:
            break
      
      for m in range(1, min(self.rank, 7 - self.file) + 1):
         ret.append((self.rank - m, self.file + m))
         
         if self.board.pieces[Board._rf_to_index(self.rank - m, self.file + m)]:
            break
      
      for m in range(1, min(self.rank, self.file) + 1):
         ret.append((self.rank - m, self.file - m))
         
         if self.board.pieces[Board._rf_to_index(self.rank - m, self.file - m)]:
            break
      
      for m in range(1, min(7 - self.rank, self.file) + 1):
         ret.append((self.rank + m, self.file - m))
         
         if self.board.pieces[Board._rf_to_index(self.rank + m, self.file - m)]:
            break

      return ret

def test_init_and_move():
   b = Board()
   b.initialize()
   b.movePGN('d4')
   b.movePGN('d5')
   b.movePGN('Nf3')
   b.movePGN('Nc6')
   b.movePGN('e4')
   b.movePGN('Nxd4')
   b.movePGN('Nxd4')
   
def test_rook_capture():
   b = Board()
   Rook(b, 0, 0, Board.WHITE)
   Rook(b, 0, 7, Board.WHITE)
   Rook(b, 0, 3, Board.BLACK)
   King(b, 7, 0, Board.WHITE)
   King(b, 7, 7, Board.BLACK)
   b.movePGN('Rhxd1')
   
def test_rook_pin():
   b = Board()
   King(b, 3, 0, Board.WHITE)
   Rook(b, 7, 2, Board.WHITE)
   Rook(b, 3, 2, Board.WHITE)
   King(b, 0, 7, Board.BLACK)
   Rook(b, 3, 7, Board.BLACK)
   Pawn(b, 5, 2, Board.BLACK)
   b.movePGN('Rxc6')
   
def test_bishop_capture():
   b = Board()
   Bishop(b, 3, 3, Board.BLACK)
   Bishop(b, 0, 0, Board.WHITE)
   Bishop(b, 6, 0, Board.WHITE)
   King(b, 7, 0, Board.WHITE)
   King(b, 7, 7, Board.BLACK)
   b.movePGN('B1xd4')
   
def test_bishop_pin():
   b = Board()
   King(b, 0, 0, Board.WHITE)
   Bishop(b, 1, 1, Board.WHITE)
   Bishop(b, 3, 1, Board.WHITE)
   King(b, 0, 7, Board.BLACK)
   Bishop(b, 7, 7, Board.BLACK)
   Pawn(b, 2, 0, Board.BLACK)
   b.movePGN('Bxa3')
   
def test_knight_capture():
   b = Board()
   Knight(b, 2, 1, Board.BLACK)
   Knight(b, 0, 0, Board.WHITE)
   Knight(b, 4, 0, Board.WHITE)
   King(b, 7, 0, Board.WHITE)
   King(b, 7, 7, Board.BLACK)
   b.movePGN('N1xb3')
   
def test_queen_capture():
   b = Board()
   Queen(b, 0, 0, Board.BLACK)
   Queen(b, 3, 7, Board.WHITE)
   Pawn(b, 3, 3, Board.WHITE)
   King(b, 7, 0, Board.WHITE)
   King(b, 7, 7, Board.BLACK)
   b.movePGN('Qxd4')
   
def test_queen_pin():
   b = Board()
   King(b, 0, 0, Board.WHITE)
   Bishop(b, 1, 1, Board.WHITE)
   Bishop(b, 3, 1, Board.WHITE)
   King(b, 0, 7, Board.BLACK)
   Queen(b, 7, 7, Board.BLACK)
   Pawn(b, 2, 0, Board.BLACK)
   b.movePGN('Bxa3')
   
def test_pawn_capture():
   b = Board()
   Pawn(b, 4, 2, Board.BLACK)
   Pawn(b, 2, 4, Board.WHITE)
   Pawn(b, 3, 3, Board.WHITE)
   King(b, 7, 0, Board.WHITE)
   King(b, 7, 7, Board.BLACK)
   b.movePGN('xd4')
   
def test_en_passant():
   b = Board()
   Pawn(b, 3, 1, Board.BLACK)
   Pawn(b, 1, 0, Board.WHITE)
   Pawn(b, 3, 4, Board.BLACK)
   Pawn(b, 1, 3, Board.WHITE)
   King(b, 7, 0, Board.WHITE)
   King(b, 7, 7, Board.BLACK)
   b.movePGN('d4')
   b.movePGN('xd3')
   b.movePGN('a4')
   b.movePGN('Kh7')
   b.movePGN('Ka7')
   
   try:
      b.movePGN('xa3')
      raise Exception('FAIL')
   except ValueError:
      pass
   
def test_king_capture():
   b = Board()
   Pawn(b, 4, 1, Board.BLACK)
   King(b, 4, 0, Board.WHITE)
   King(b, 4, 2, Board.BLACK)
   b.movePGN('Kxb5')
   
def test_castle():
   b = Board()
   King(b, 0, 4, Board.WHITE)
   Rook(b, 0, 7, Board.WHITE)
   King(b, 7, 4, Board.BLACK)
   Rook(b, 7, 0, Board.BLACK)
   b.movePGN('O-O')
   b.movePGN('O-O-O')
   
def main():
   test_init_and_move()
   test_rook_capture()
   test_bishop_capture()
   test_knight_capture()
   test_queen_capture()
   test_pawn_capture()
   test_king_capture()
   test_rook_pin()
   test_bishop_pin()
   test_queen_pin()
   test_en_passant()
   test_castle()

if __name__ == '__main__':
   main()
 

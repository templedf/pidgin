# pidgin
Pidgin is a Python tool that reads PGN files and translates them into a Board object.

Create a new Board instance, initialize it, and then call move() or
movePGN() to move pieces.  move() blindly moves the piece at the given
square to the destination square.  movePGN() takes a move in PGN notation,
parses it, tests it for validity, and then makes the move.

For example:

    import board

    b = board.Board()
    b.initialize()

    with open('pgn.txt', 'r') as f:
        for line in f:
            for move in line.strip().split():
                # Drop the leading . if there is one
                code = move.split('.')[-1]

                if code:
                    b.movePGN(code)

Parsing PGN notation is actually much harder than it looks because of all
of the odd corner cases.  For example, there may be two pieces that could be
referenced, but one of them is pinned, making only one of them a valid play,
and thereby leaving no need to disambiguate the move.  As such Pidgin has
to keep track of every aspect of the game so that it can understand the
notation.

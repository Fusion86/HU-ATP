# Board size is 16*8 WxH, so 128 tiles in total.
#
# Y
# |
# |
# |
# |
# |
# |
# |
# | _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ _ X
#
# See https://en.wikipedia.org/wiki/Conway%27s_Game_of_Life

static var board: array[128];
static var board_next: array[128];

func main() {
    var speed = 1000; # Lower is faster
    # If you set the speed value to a large value the CLI tool will think the Arduino timed out and exit.
    # This can be bypassed by using PlatformIO monitor, or by fixing the CLI tool.

    println_str("Welcome to Conway's Game of Life");

    # Change this number here to create other boards.
    init_board(1);

    var step = 0;
    while (step < 16) {
        println_str("================");
        print_board();
        simulate_board();
        delay(speed);
        step = step + 1;
    }

    println_str("The end.")
}

# Init board
# Types:
# 0 - Empty board
# 1 - Block and blinker
# 2 - Beehive and toad
# 3 - Light-weight spaceship
func init_board(type: number) {
    // Set the board to zero
    // Not really needed on the first run, but doesn't hurt either.
    var i = 0;
    while (i < 128) {
        board[i] = 0;
        i = i + 1;
    }

    if (type == 1) {
        // Block
        board[51] = 1;
        board[52] = 1;
        board[67] = 1;
        board[68] = 1;

        // Blinker
        board[41] = 1;
        board[57] = 1;
        board[73] = 1;
        return 0;
    }

    if (type == 2) {
        // Beehive
        board[18] = 1;
        board[19] = 1;
        board[33] = 1;
        board[36] = 1;
        board[50] = 1;
        board[51] = 1;

        // Toad
        board[42] = 1;
        board[56] = 1;
        board[59] = 1;
        board[72] = 1;
        board[75] = 1;
        board[89] = 1;
    }

    if (type == 3) {
        // Light-weight spaceship
        board[17] = 1;
        board[20] = 1;
        board[37] = 1;
        board[49] = 1;
        board[53] = 1;
        board[66] = 1;
        board[67] = 1;
        board[68] = 1;
        board[69] = 1;
    }
}

func print_board() {
    var i = 0;
    var x = 0;
    while (i < 128) {
        var cell = board[i];

        if (cell == 1) {
            print_str("X");
        } else {
            print_str(" ");
        }

        i = i + 1;

        # Shitty alternative to the module operator.
        # Though this is probably more performance friendly than implementing modulo ourselves.
        x = x + 1;
        if (x == 16) {
            x = 0;
            println_str("");
        }
        # P.S. we now have a modulo operator in the language, but we didn't have it when I was writing this part of the code.
        # Though maybe the performance still is better with this code?
    }
}

# Simulate one full 'step' of the game of life.
# Create new state in the `board_next` array, and write this array to the `board` array when
# all tiles have been updated.
func simulate_board() {
    # A live cell dies unless it has exactly 2 or 3 live neighbors.
    # A dead cell remains dead unless it has exactly 3 live neighbors.

    var i = 0;
    while (i < 128) {
        # Figure out if the current cell is dead or alive.
        var cell = board[i];
        var alive_neighbor_count = count_live_neighbors(i);

        # If cell is alive
        if (cell == 1) {
            if (alive_neighbor_count != 2) {
                if (alive_neighbor_count != 3) {
                    cell = 0;
                }
            }
        } else {
            if (alive_neighbor_count == 3) {
                cell = 1;
            }
        }

        board_next[i] = cell;

        i = i + 1;
    }

    # Copy values from `board_next` to `board`
    i = 0;
    while (i < 128) {
        var tmp = board_next[i];
        board[i] = tmp;
        i = i + 1;
    }
}

func count_live_neighbors(i: number) {
    var tmp = 0;
    var count = 0;

    # Wrapping around is not supported, because it is a PITA to implement.
    tmp = is_edge(i);
    if (tmp == 0) {
        # Return count, aka zero.
        return count;
    }

    # Top left
    tmp = i - 17; # Calculate neigbor index
    tmp = board[tmp]; # Check if neighbor is alive
    count = count + tmp; # Count += 1 if neighbor is alive

    # Top middle
    tmp = i - 16;
    tmp = board[tmp];
    count = count + tmp;

    # Top right
    tmp = i - 15;
    tmp = board[tmp];
    count = count + tmp;

    # Middle left
    tmp = i - 1;
    tmp = board[tmp];
    count = count + tmp;

    # Middle right
    tmp = i + 1;
    tmp = board[tmp];
    count = count + tmp;

    # Bottom left
    tmp = i + 15;
    tmp = board[tmp];
    count = count + tmp;

    # Bottom left
    tmp = i + 16;
    tmp = board[tmp];
    count = count + tmp;

    # Bottom left
    tmp = i + 17;
    tmp = board[tmp];
    count = count + tmp;

    return count;
}

func is_edge(n) {
    # Top row and leftmost item on the second row
    if (n < 17) { return 1; }

    # Left edge
    if (n == 32) { return 1; }
    if (n == 48) { return 1; }
    if (n == 64) { return 1; }
    if (n == 80) { return 1; }
    if (n == 96) { return 1; }

    # Right edge
    if (n == 31) { return 1; }
    if (n == 46) { return 1; }
    if (n == 63) { return 1; }
    if (n == 79) { return 1; }
    if (n == 95) { return 1; }

    # Bottom row and rightmost item on the second-last row
    if (n > 110) { return 1; }
}

/*
 * Bot Mourad AmazingGame - version optimisée cours + compétition
 *
 * Compile Windows :
 * gcc -O2 -Wall -o sample_player_client.exe sample_player_client.c -lws2_32 -lm
 *
 * Run :
 * .\sample_player_client.exe 127.0.0.1 16210 MouradBot
 */

#define _WIN32_WINNT 0x0601

#ifdef _WIN32
#ifndef WIN32_LEAN_AND_MEAN
#define WIN32_LEAN_AND_MEAN
#endif
#include <winsock2.h>
#include <ws2tcpip.h>
typedef SOCKET sock_t;
#define INVALID_SOCK INVALID_SOCKET
#define sock_close closesocket
#else
#include <netdb.h>
#include <sys/socket.h>
#include <unistd.h>
typedef int sock_t;
#define INVALID_SOCK (-1)
#define sock_close close
#endif

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#ifndef M_PI
#define M_PI 3.14159265358979323846
#endif

#define GRID 15
#define GOAL_X 14
#define GOAL_Y 14

#define EAST 0
#define NORTH 1
#define WEST 2
#define SOUTH 3

static int dxs[4] = {1, 0, -1, 0};
static int dys[4] = {0, -1, 0, 1};

/* Tableaux : accès O(1), adaptés à une grille fixe 15x15 */
static int visited[GRID][GRID];
static int blocked[GRID][GRID][4];
static int known[GRID][GRID][4];

/* Anti-blocage / virage verrouillé */
static int turn_mode = 0;
static int turn_steps = 0;
static int last_turn = 0;
static int lock_turn = 0;

static int last_x = -1;
static int last_y = -1;
static int stuck_counter = 0;

static int last_visit_x = -1;
static int last_visit_y = -1;

static int send_line(sock_t fd, const char* msg)
{
    char buf[256];
    snprintf(buf, sizeof(buf), "%s\n", msg);
    return send(fd, buf, (int)strlen(buf), 0) > 0 ? 0 : -1;
}

static int read_line(sock_t fd, char* buf, size_t size)
{
    size_t pos = 0;

    while (pos < size - 1) {
        char c;
        int n = (int)recv(fd, &c, 1, 0);

        if (n <= 0) return -1;
        if (c == '\n') break;
        if (c != '\r') buf[pos++] = c;
    }

    buf[pos] = '\0';
    return (int)pos;
}

static int in_grid(int x, int y)
{
    return x >= 0 && x < GRID && y >= 0 && y < GRID;
}

static int opposite_dir(int d)
{
    return (d + 2) % 4;
}

static void set_edge(int x, int y, int d, int is_blocked)
{
    int nx = x + dxs[d];
    int ny = y + dys[d];

    if (!in_grid(x, y) || !in_grid(nx, ny)) return;

    known[x][y][d] = 1;
    known[nx][ny][opposite_dir(d)] = 1;

    blocked[x][y][d] = is_blocked;
    blocked[nx][ny][opposite_dir(d)] = is_blocked;
}

static int dir_from_orientation(double ori)
{
    ori = fmod(ori + 360.0, 360.0);

    if (ori < 45 || ori >= 315) return EAST;
    if (ori >= 45 && ori < 135) return NORTH;
    if (ori >= 135 && ori < 225) return WEST;

    return SOUTH;
}

static int right_dir(int d)
{
    return (d + 3) % 4;
}

static int left_dir(int d)
{
    return (d + 1) % 4;
}

static double normalize_angle(double a)
{
    while (a < 0) a += 360.0;
    while (a >= 360.0) a -= 360.0;
    return a;
}

static double angle_diff(double target, double current)
{
    double diff = normalize_angle(target - current);
    if (diff > 180.0) diff -= 360.0;
    return diff;
}

static double angle_to_cell(double x, double y, int tx, int ty)
{
    double cx = tx + 0.5;
    double cy = ty + 0.5;
    return normalize_angle(-atan2(cy - y, cx - x) * 180.0 / M_PI);
}

static void update_map(
    double x,
    double y,
    double orientation,
    double front,
    double right,
    double rear,
    double left
)
{
    int cx = (int)floor(x);
    int cy = (int)floor(y);

    if (!in_grid(cx, cy)) return;

    int fd = dir_from_orientation(orientation);
    int rd = right_dir(fd);
    int ld = left_dir(fd);
    int bd = opposite_dir(fd);

    set_edge(cx, cy, fd, front < 0.50);
    set_edge(cx, cy, rd, right < 0.50);
    set_edge(cx, cy, ld, left < 0.50);
    set_edge(cx, cy, bd, rear < 0.50);
}

static int can_move_known(int x, int y, int d)
{
    int nx = x + dxs[d];
    int ny = y + dys[d];

    if (!in_grid(nx, ny)) return 0;
    if (!known[x][y][d]) return 0;
    if (blocked[x][y][d]) return 0;

    return 1;
}

/*
 * BFS avec FIFO par tableaux qx/qy.
 * Complexité : O(V+E), très efficace sur 15x15.
 */
static int bfs(int sx, int sy, int gx, int gy, int* next_x, int* next_y)
{
    int qx[GRID * GRID];
    int qy[GRID * GRID];
    int px[GRID][GRID];
    int py[GRID][GRID];
    int seen[GRID][GRID];

    memset(seen, 0, sizeof(seen));

    for (int x = 0; x < GRID; x++) {
        for (int y = 0; y < GRID; y++) {
            px[x][y] = -1;
            py[x][y] = -1;
        }
    }

    int head = 0;
    int tail = 0;

    qx[tail] = sx;
    qy[tail] = sy;
    tail++;
    seen[sx][sy] = 1;

    while (head < tail) {
        int x = qx[head];
        int y = qy[head];
        head++;

        if (x == gx && y == gy) {
            int cx = gx;
            int cy = gy;

            while (!(px[cx][cy] == sx && py[cx][cy] == sy)) {
                int tx = px[cx][cy];
                int ty = py[cx][cy];

                if (tx < 0 || ty < 0) break;

                cx = tx;
                cy = ty;
            }

            *next_x = cx;
            *next_y = cy;
            return 1;
        }

        for (int d = 0; d < 4; d++) {
            if (!can_move_known(x, y, d)) continue;

            int nx = x + dxs[d];
            int ny = y + dys[d];

            if (!seen[nx][ny]) {
                seen[nx][ny] = 1;
                px[nx][ny] = x;
                py[nx][ny] = y;
                qx[tail] = nx;
                qy[tail] = ny;
                tail++;
            }
        }
    }

    return 0;
}

/*
 * Exploration intelligente :
 * BFS vers la cellule non visitée connue la plus proche.
 */
static int bfs_nearest_unvisited(int sx, int sy, int* next_x, int* next_y)
{
    int qx[GRID * GRID];
    int qy[GRID * GRID];
    int px[GRID][GRID];
    int py[GRID][GRID];
    int seen[GRID][GRID];

    memset(seen, 0, sizeof(seen));

    for (int x = 0; x < GRID; x++) {
        for (int y = 0; y < GRID; y++) {
            px[x][y] = -1;
            py[x][y] = -1;
        }
    }

    int head = 0;
    int tail = 0;

    qx[tail] = sx;
    qy[tail] = sy;
    tail++;
    seen[sx][sy] = 1;

    while (head < tail) {
        int x = qx[head];
        int y = qy[head];
        head++;

        if (!(x == sx && y == sy) && visited[x][y] == 0) {
            int cx = x;
            int cy = y;

            while (!(px[cx][cy] == sx && py[cx][cy] == sy)) {
                int tx = px[cx][cy];
                int ty = py[cx][cy];

                if (tx < 0 || ty < 0) break;

                cx = tx;
                cy = ty;
            }

            *next_x = cx;
            *next_y = cy;
            return 1;
        }

        for (int d = 0; d < 4; d++) {
            if (!can_move_known(x, y, d)) continue;

            int nx = x + dxs[d];
            int ny = y + dys[d];

            if (!seen[nx][ny]) {
                seen[nx][ny] = 1;
                px[nx][ny] = x;
                py[nx][ny] = y;
                qx[tail] = nx;
                qy[tail] = ny;
                tail++;
            }
        }
    }

    return 0;
}

static const char* start_turn(double right, double left)
{
    if (lock_turn > 0) {
        lock_turn--;

        if (last_turn > 0) return "TURN_RIGHT";
        return "TURN_LEFT";
    }

    if (right >= left) {
        turn_mode = 1;
        turn_steps = 9;
        last_turn = 1;
        lock_turn = 7;
        return "TURN_RIGHT";
    }

    turn_mode = -1;
    turn_steps = 9;
    last_turn = -1;
    lock_turn = 7;
    return "TURN_LEFT";
}

static const char* continue_turn(double front)
{
    if (turn_steps <= 0) {
        turn_mode = 0;
        return NULL;
    }

    if (front > 1.25) {
        turn_steps = 0;
        turn_mode = 0;
        lock_turn = 0;
        return "ACCELERATE";
    }

    turn_steps--;

    if (turn_mode > 0) return "TURN_RIGHT";
    if (turn_mode < 0) return "TURN_LEFT";

    return NULL;
}

static const char* drive_to_cell(
    double x,
    double y,
    double orientation,
    double speed,
    double front,
    double right,
    double left,
    int tx,
    int ty,
    double max_speed
)
{
    double target = angle_to_cell(x, y, tx, ty);
    double diff = angle_diff(target, orientation);

    if (front < 0.55 + speed * 1.20) {
        if (speed > 0.08) return "DECELERATE";
        return start_turn(right, left);
    }

    if (fabs(diff) > 14.0) {
        if (speed > 0.20) return "DECELERATE";
        return diff > 0 ? "TURN_LEFT" : "TURN_RIGHT";
    }

    if (front > 1.10 && speed < max_speed) return "ACCELERATE";

    if (speed > max_speed + 0.30) return "DECELERATE";

    return "ACCELERATE";
}

static void mark_visit(int cx, int cy)
{
    if (cx != last_visit_x || cy != last_visit_y) {
        visited[cx][cy]++;
        last_visit_x = cx;
        last_visit_y = cy;
    }
}

static double adaptive_speed(int exploration, double front)
{
    if (exploration) {
        if (front > 3.0) return 1.60;
        if (front > 2.0) return 1.20;
        if (front > 1.2) return 0.85;
        return 0.45;
    }

    if (front > 3.0) return 2.20;
    if (front > 2.0) return 1.60;
    if (front > 1.2) return 1.10;
    return 0.55;
}
static int has_unknown_edge(int x, int y)
{
    if (!in_grid(x, y)) return 0;

    for (int d = 0; d < 4; d++) {
        int nx = x + dxs[d];
        int ny = y + dys[d];

        if (in_grid(nx, ny) && !known[x][y][d]) {
            return 1;
        }
    }

    return 0;
}

static int bfs_nearest_frontier(int sx, int sy, int* next_x, int* next_y)
{
    int qx[GRID * GRID];
    int qy[GRID * GRID];
    int px[GRID][GRID];
    int py[GRID][GRID];
    int seen[GRID][GRID];

    memset(seen, 0, sizeof(seen));

    for (int x = 0; x < GRID; x++) {
        for (int y = 0; y < GRID; y++) {
            px[x][y] = -1;
            py[x][y] = -1;
        }
    }

    int head = 0;
    int tail = 0;

    qx[tail] = sx;
    qy[tail] = sy;
    tail++;
    seen[sx][sy] = 1;

    while (head < tail) {
        int x = qx[head];
        int y = qy[head];
        head++;

        if (!(x == sx && y == sy) && has_unknown_edge(x, y)) {
            int cx = x;
            int cy = y;

            while (!(px[cx][cy] == sx && py[cx][cy] == sy)) {
                int tx = px[cx][cy];
                int ty = py[cx][cy];

                if (tx < 0 || ty < 0) break;

                cx = tx;
                cy = ty;
            }

            *next_x = cx;
            *next_y = cy;
            return 1;
        }

        for (int d = 0; d < 4; d++) {
            if (!can_move_known(x, y, d)) continue;

            int nx = x + dxs[d];
            int ny = y + dys[d];

            if (!seen[nx][ny]) {
                seen[nx][ny] = 1;
                px[nx][ny] = x;
                py[nx][ny] = y;
                qx[tail] = nx;
                qy[tail] = ny;
                tail++;
            }
        }
    }

    return 0;
}

static const char* choose_command(
    int exploration,
    double x,
    double y,
    double orientation,
    double speed,
    double front,
    double right,
    double rear,
    double left
)
{
    int cx = (int)floor(x);
    int cy = (int)floor(y);

    if (!in_grid(cx, cy)) return "DECELERATE";

    mark_visit(cx, cy);

    if (cx == last_x && cy == last_y) {
        stuck_counter++;
    } else {
        stuck_counter = 0;
    }

    last_x = cx;
    last_y = cy;

    double max_speed = adaptive_speed(exploration, front);
    double danger_front = exploration ? 0.55 + speed * 1.40
                                      : 0.50 + speed * 1.20;

    if (front < danger_front) {
        if (speed > 0.05) return "DECELERATE";
        return start_turn(right, left);
    }

    const char* turn_cmd = continue_turn(front);
    if (turn_cmd != NULL) return turn_cmd;

    if (stuck_counter > 26) {
        stuck_counter = 0;

        if (speed > 0.05) return "DECELERATE";
        return start_turn(right, left);
    }

    if (speed > max_speed + 0.30) return "DECELERATE";

    if (exploration == 1) {
    int next_x;
    int next_y;

    /*
     * Priorité 1 : aller vers une frontière,
     * c’est-à-dire une case qui a encore des directions inconnues.
     */
    if (bfs_nearest_frontier(cx, cy, &next_x, &next_y)) {
        return drive_to_cell(
            x,
            y,
            orientation,
            speed,
            front,
            right,
            left,
            next_x,
            next_y,
            max_speed
        );
    }

    /*
     * Priorité 2 : aller vers une cellule jamais visitée.
     */
    if (bfs_nearest_unvisited(cx, cy, &next_x, &next_y)) {
        return drive_to_cell(
            x,
            y,
            orientation,
            speed,
            front,
            right,
            left,
            next_x,
            next_y,
            max_speed
        );
    }

    /*
     * Priorité 3 : comportement local rapide.
     */
    if (front > 1.00) {
        if (speed < max_speed) return "ACCELERATE";
        return "ACCELERATE";
    }

    if (speed > 0.05) return "DECELERATE";

    return start_turn(right, left);
}
    int next_x;
    int next_y;

    if (bfs(cx, cy, GOAL_X, GOAL_Y, &next_x, &next_y)) {
        return drive_to_cell(
            x,
            y,
            orientation,
            speed,
            front,
            right,
            left,
            next_x,
            next_y,
            max_speed
        );
    }

    if (front > 0.90) {
        if (speed < max_speed) return "ACCELERATE";
        return "ACCELERATE";
    }

    if (speed > 0.05) return "DECELERATE";

    return start_turn(right, left);
}

int main(int argc, char* argv[])
{
    const char* host = argc > 1 ? argv[1] : "127.0.0.1";
    const char* port = argc > 2 ? argv[2] : "16210";
    const char* name = argc > 3 ? argv[3] : "MouradBot";

#ifdef _WIN32
    WSADATA wsa;

    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return 1;
    }
#endif

    memset(visited, 0, sizeof(visited));
    memset(blocked, 0, sizeof(blocked));
    memset(known, 0, sizeof(known));

    struct addrinfo hints;
    struct addrinfo* res;
    struct addrinfo* rp;

    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC;
    hints.ai_socktype = SOCK_STREAM;

    if (getaddrinfo(host, port, &hints, &res) != 0) {
        fprintf(stderr, "getaddrinfo failed\n");

#ifdef _WIN32
        WSACleanup();
#endif

        return 1;
    }

    sock_t fd = INVALID_SOCK;

    for (rp = res; rp != NULL; rp = rp->ai_next) {
        fd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);

        if (fd == INVALID_SOCK) continue;

        if (connect(fd, rp->ai_addr, (int)rp->ai_addrlen) == 0) break;

        sock_close(fd);
        fd = INVALID_SOCK;
    }

    freeaddrinfo(res);

    if (fd == INVALID_SOCK) {
        fprintf(stderr, "Could not connect\n");

#ifdef _WIN32
        WSACleanup();
#endif

        return 1;
    }

    printf("Connected to %s:%s\n", host, port);

    char line[256];

    send_line(fd, "0");
    send_line(fd, name);

    if (read_line(fd, line, sizeof(line)) < 0) goto done;

    if (strcmp(line, "OK") != 0) {
        printf("Server rejected: %s\n", line);
        goto done;
    }

    printf("Registered as %s\n", name);

    if (read_line(fd, line, sizeof(line)) < 0) goto done;

    if (strcmp(line, "START") != 0) {
        printf("Expected START, got %s\n", line);
        goto done;
    }

    printf("Game started\n");

    for (;;) {
        if (send_line(fd, "GET_SENSORS") < 0) break;
        if (read_line(fd, line, sizeof(line)) < 0) break;

        if (strcmp(line, "BLOCKED") == 0) {
            printf("BLOCKED\n");
            turn_mode = 0;
            turn_steps = 0;
            lock_turn = 0;
            continue;
        }

        double t, x, y, orientation, speed;
        double front, right, rear, left;
        int exploration;

        int parsed = sscanf(
            line,
            "%lf %d %lf %lf %lf %lf %lf %lf %lf %lf",
            &t,
            &exploration,
            &x,
            &y,
            &orientation,
            &speed,
            &front,
            &right,
            &rear,
            &left
        );

        if (parsed != 10) {
            printf("Bad sensors: %s\n", line);
            continue;
        }

        update_map(x, y, orientation, front, right, rear, left);

        const char* cmd = choose_command(
            exploration,
            x,
            y,
            orientation,
            speed,
            front,
            right,
            rear,
            left
        );

        printf(
            "t=%.2f mode=%s pos=(%.2f,%.2f) ori=%.0f spd=%.2f F=%.2f R=%.2f L=%.2f cmd=%s\n",
            t,
            exploration ? "EXPLORE" : "RACE",
            x,
            y,
            orientation,
            speed,
            front,
            right,
            left,
            cmd
        );

        if (send_line(fd, cmd) < 0) break;
        if (read_line(fd, line, sizeof(line)) < 0) break;

        if (
            strcmp(line, "OK") != 0 &&
            strcmp(line, "KO") != 0 &&
            strcmp(line, "BLOCKED") != 0
        ) {
            printf("Unexpected server response: %s\n", line);
            break;
        }
    }

done:
    sock_close(fd);

#ifdef _WIN32
    WSACleanup();
#endif

    return 0;
}

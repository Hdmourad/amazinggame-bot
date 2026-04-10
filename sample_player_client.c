/*
 * sample_player_client.c
 *
 * A minimal Amazinggame player that connects to the game server and turns forever.
 *
 * Usage:  ./sample_player_client [host [port [name]]]
 *         defaults: host=127.0.0.1  port=16210  name=turner
 *
 * Compile (Linux):   gcc -Wall -o sample_player_client sample_player_client.c
 * Compile (Windows): gcc -Wall -o sample_player_client sample_player_client.c -lws2_32
 */

/* --------------------------------------------------------------------------
 * Platform abstraction
 * -------------------------------------------------------------------------- */
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

/* --------------------------------------------------------------------------
 * Low-level helpers
 * -------------------------------------------------------------------------- */

/*
 * send_line – send <msg> followed by a newline.
 * Returns 0 on success, -1 on error.
 */
static int send_line(sock_t fd, const char* msg)
{
    size_t len = strlen(msg);
    /* Build "msg\n" in a local buffer to avoid two send() calls. */
    char* buf = (char*)malloc(len + 2);
    if (!buf) {
        fprintf(stderr, "send_line: out of memory\n");
        return -1;
    }
    memcpy(buf, msg, len);
    buf[len] = '\n';
    buf[len + 1] = '\0';

    size_t sent = 0;
    while (sent < len + 1) {
        int n = (int)send(fd, buf + sent, (int)(len + 1 - sent), 0);
        if (n <= 0) {
            fprintf(stderr, "send_line: connection lost while sending '%s'\n", msg);
            free(buf);
            return -1;
        }
        sent += (size_t)n;
    }
    free(buf);
    return 0;
}

/*
 * read_line – read bytes one at a time until '\n' (or EOF / error).
 * The newline (and any preceding '\r') is stripped.
 * Returns the number of bytes stored in buf (excluding the null terminator),
 * or -1 on error / disconnection.
 */
static int read_line(sock_t fd, char* buf, size_t size)
{
    size_t pos = 0;
    while (pos < size - 1) {
        char c;
        int n = (int)recv(fd, &c, 1, 0);
        if (n <= 0) {
            fprintf(stderr, "read_line: connection closed by server\n");
            return -1;
        }
        if (c == '\n') {
            break;
        }
        if (c == '\r') {
            continue; /* skip CR in CRLF line endings */
        }
        buf[pos++] = c;
    }
    buf[pos] = '\0';
    return (int)pos;
}

/* --------------------------------------------------------------------------
 * Main
 * -------------------------------------------------------------------------- */

int main(int argc, char* argv[])
{
    const char* host = (argc > 1) ? argv[1] : "127.0.0.1";
    const char* port = (argc > 2) ? argv[2] : "16210";
    const char* name = (argc > 3) ? argv[3] : "turner";

#ifdef _WIN32
    WSADATA wsa;
    if (WSAStartup(MAKEWORD(2, 2), &wsa) != 0) {
        fprintf(stderr, "WSAStartup failed\n");
        return 1;
    }
#endif

    /* ------------------------------------------------------------------ */
    /* Resolve host / port and connect                                     */
    /* ------------------------------------------------------------------ */
    struct addrinfo hints, *res, *rp;
    memset(&hints, 0, sizeof(hints));
    hints.ai_family = AF_UNSPEC; /* IPv4 or IPv6 */
    hints.ai_socktype = SOCK_STREAM; /* TCP */

    int rc = getaddrinfo(host, port, &hints, &res);
    if (rc != 0) {
        fprintf(stderr, "getaddrinfo: %s\n", gai_strerror(rc));
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    sock_t fd = INVALID_SOCK;
    for (rp = res; rp != NULL; rp = rp->ai_next) {
        fd = socket(rp->ai_family, rp->ai_socktype, rp->ai_protocol);
        if (fd == INVALID_SOCK) {
            continue;
        }
        if (connect(fd, rp->ai_addr, (int)rp->ai_addrlen) == 0) {
            break; /* connected */
        }
        sock_close(fd);
        fd = INVALID_SOCK;
    }
    freeaddrinfo(res);

    if (fd == INVALID_SOCK) {
        fprintf(stderr, "Could not connect to %s:%s\n", host, port);
#ifdef _WIN32
        WSACleanup();
#endif
        return 1;
    }

    printf("Connected to %s:%s\n", host, port);

    /* ------------------------------------------------------------------ */
    /* Handshake                                                           */
    /* ------------------------------------------------------------------ */
    char line[256];

    /* Identify as a player (not spectator) */
    if (send_line(fd, "0") < 0)
        goto error;

    /* Send player name */
    if (send_line(fd, name) < 0)
        goto error;

    /* Expect "OK" */
    if (read_line(fd, line, sizeof(line)) < 0)
        goto error;
    if (strcmp(line, "OK") != 0) {
        fprintf(stderr, "Server rejected connection: '%s'\n", line);
        goto error;
    }
    printf("Registered as '%s', waiting for game to start...\n", name);

    /* Expect "START" */
    if (read_line(fd, line, sizeof(line)) < 0)
        goto error;
    if (strcmp(line, "START") != 0) {
        fprintf(stderr, "Expected START, got: '%s'\n", line);
        goto error;
    }
    printf("Game started! Turning forever...\n");

    /* ------------------------------------------------------------------ */
    /* Game loop: turn right indefinitely                                  */
    /* ------------------------------------------------------------------ */
    for (;;) {
        if (send_line(fd, "TURN_RIGHT") < 0)
            goto done;
        if (read_line(fd, line, sizeof(line)) < 0)
            goto done;
        /* KO means we are blocked; keep trying — the server will handle it */
        if (strcmp(line, "OK") != 0 && strcmp(line, "KO") != 0) {
            /* Unexpected response; the game may have ended */
            printf("Server: '%s' — stopping.\n", line);
            break;
        }
    }

done:
    sock_close(fd);
#ifdef _WIN32
    WSACleanup();
#endif
    return 0;

error:
    sock_close(fd);
#ifdef _WIN32
    WSACleanup();
#endif
    return 1;
}

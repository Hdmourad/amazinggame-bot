"""Main entry point for maze-generator."""

from maze_generator import generate_maze


def main() -> None:
    """Run the maze generator application."""
    maze = generate_maze(30, 30)
    paths = maze.paths(0, 0, 29, 29)
    print(maze)  # noqa: T201
    print(f"Number of paths from (0, 0) to (29, 29): {len(paths)}")  # noqa: T201
    if paths:
        print("Example path:", paths[0])  # noqa: T201


if __name__ == "__main__":
    main()

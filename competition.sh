PORT=$(python -c "import random; print(random.randint(50000, 60000))")
echo "La compétition se passe sur 127.0.0.1:$PORT"

uv run python  -m amazinggame.killall
find . -name "*.log" -exec rm \{} \;

uv run python -m amazinggame.game.server -p $PORT --timeout 5 &
uv run python -m amazinggame.viewer -p $PORT &
# https://www.speedscope.app/
# py-spy record -o profile.data --format speedscope -- python -m amazinggame.viewer -p $PORT &
#uv run python -m amazinggame.viewer -p $PORT --small-window &
sleep 2

uv run python /home/vincent/Documents/programmation/amazing_player/sample_player_client.py -p $PORT -u "Flash" --winner &
sleep 1
uv run python /home/vincent/Documents/programmation/amazing_player/sample_player_client.py -p $PORT -u "KITT" &
uv run python /home/vincent/Documents/programmation/amazing_player/sample_player_client.py -p $PORT -u "Optimus Prime" &
uv run python /home/vincent/Documents/programmation/amazing_player/sample_player_client.py -p $PORT -u "Toto" &
uv run python /home/vincent/Documents/programmation/amazing_player/sample_player_client.py -p $PORT -u "Titi" &
uv run python /home/vincent/Documents/programmation/amazing_player/sample_player_client.py -p $PORT -u "Tutu" &

gcc -Wall -o sample_player_client sample_player_client.c
./sample_player_client "localhost" $PORT "SamplePlayer" &

sleep 330
uv run python -m amazinggame.killall

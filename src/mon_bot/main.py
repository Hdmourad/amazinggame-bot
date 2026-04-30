import socket
import time

def main():
    # --- CONFIGURATION ---
    host = "127.0.0.1"
    port = 16210
    bot_name = "MonSuperBot"

    # 1. CONNEXION AU SERVEUR
    print(f"Connexion à {host}:{port}...")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.sendall(f"{bot_name}\n".encode())
        print(f"\033[92m[OK] Connecté en tant que {bot_name}\033[0m")
    except Exception as e:
        print(f"\033[91m[ERREUR] Impossible de se connecter : {e}\033[0m")
        return

    try:
        while True:
            # 2. DEMANDER LES INFOS CAPTEURS
            s.sendall(b"GET_SENSORS\n")
            response = s.recv(1024).decode().strip()

            if not response:
                continue
            
            if response == "BLOCKED":
                print("\033[93m [!] MUR TOUCHÉ : Bloqué pour 10s... \033[0m", end="\r")
                continue

            # 3. ANALYSER LES DONNÉES
            parts = response.split()
            if len(parts) < 10:
                continue

            try:
                infos = {
                    "time": float(parts[0]),
                    "is_exploring": int(parts[1]) == 1,
                    "x": float(parts[2]),
                    "y": float(parts[3]),
                    "angle": float(parts[4]),
                    "speed": float(parts[5]),
                    "dist": {
                        "front": float(parts[6]),
                        "right": float(parts[7]),
                        "rear": float(parts[8]),
                        "left": float(parts[9])
                    }
                }
            except ValueError:
                continue

            # --- AFFICHAGE ---
            phase = "EXPLORATION" if infos["is_exploring"] else "COURSE"
            print(f"[{phase}] 📍({infos['x']:>5.2f}, {infos['y']:>5.2f}) | "
                  f"🏎️ Vit: {infos['speed']:.2f} | "
                  f"📏 F:{infos['dist']['front']:.1f} R:{infos['dist']['right']:.1f} L:{infos['dist']['left']:.1f}", end="\r")

            # --- IA AMÉLIORÉE ---
            # --- IA AMÉLIORÉE ---
            # --- IA COMPÉTITION ---

            front = infos["dist"]["front"]
            right = infos["dist"]["right"]
            left = infos["dist"]["left"]
            speed = infos["speed"]
            exploring = infos["is_exploring"]

            SAFE = 0.9
            DANGER = 0.5

            command = "ACCELERATE\n"

            # 🔥 1. ÉVITER COLLISION (priorité max)
            if front < DANGER:
                if right > left:
                    command = "TURN_RIGHT\n"
                else:
                    command = "TURN_LEFT\n"

            # 🔥 2. SUIVI DE MUR (stratégie labyrinthe)
            elif front < SAFE:
                if right > left:
                    command = "TURN_RIGHT\n"
                else:
                    command = "TURN_LEFT\n"

            # 🔥 3. CORRECTION TRAJECTOIRE (évite zigzag)
            elif left < 0.4:
                command = "TURN_RIGHT\n"

            elif right < 0.4:
                command = "TURN_LEFT\n"

            # 🔥 4. PHASE COURSE = PLUS AGRESSIF
            if not exploring:
                if front > 1.5:
                    command = "ACCELERATE\n"

            # 🔥 ENVOI UNIQUE
            s.sendall(command.encode())

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("\n\033[94mArêt du bot demandé par l'utilisateur.\033[0m")

    except Exception as e:
        print(f"\n\033[91mErreur pendant l'exécution : {e}\033[0m")

    finally:
        s.close()
        print("Connexion fermée.")


if __name__ == "__main__":
    main()
#!/usr/bin/env bash

if [[ "$RETROARCHER_DOCKER" == "True" ]]; then
    PUID=${PUID:-1000}
    PGID=${PGID:-1000}

    groupmod -o -g "$PGID" retroarcher
    usermod -o -u "$PUID" retroarcher

    chown -R retroarcher:retroarcher /config

    echo "Running RetroArcher using user retroarcher (uid=$(id -u retroarcher)) and group retroarcher (gid=$(id -g retroarcher))"
    exec gosu retroarcher "$@"
else
    python_versions=("python3" "python3.8" "python3.7" "python3.6" "python" "python2" "python2.7")
    for cmd in "${python_versions[@]}"; do
        if command -v "$cmd" >/dev/null; then
            echo "Starting RetroArcher with $cmd."
            if [[ "$(uname -s)" == "Darwin" ]]; then
                $cmd RetroArcher.py &> /dev/null &
            else
                $cmd RetroArcher.py --quiet --daemon
            fi
            exit
        fi
    done
    echo "Unable to start RetroArcher. No Python interpreter was found in the following options:" "${python_versions[@]}"
fi

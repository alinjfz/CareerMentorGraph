#!/usr/bin/env bash
set -euo pipefail

docker compose up -d neo4j

printf "\nNeo4j is starting.\n"
printf "Browser: http://localhost:7474\n"
printf "Bolt URI: bolt://localhost:7687\n"
printf "Username: neo4j\n"
printf "Password: CareerGraphPass123\n"

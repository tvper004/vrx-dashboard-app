#!/bin/bash

# Script de comandos para vRx Dashboard App usando su root
# Servidor: 192.168.1.200

APP_DIR="/home/rleon/vrx-dashboard"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_help() {
    echo -e "${BLUE}vRx Dashboard App - Comandos con su root${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start      - Iniciar la aplicación"
    echo "  stop       - Parar la aplicación"
    echo "  restart    - Reiniciar la aplicación"
    echo "  status     - Ver estado de la aplicación"
    echo "  logs       - Ver logs en tiempo real"
    echo "  health     - Verificar health check"
    echo "  shell      - Acceder al contenedor"
    echo "  help       - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 status"
}

case "$1" in
    start)
        echo -e "${GREEN}🚀 Iniciando vRx Dashboard App...${NC}"
        cd $APP_DIR && ./start-with-su.sh
        ;;
    stop)
        echo -e "${YELLOW}🛑 Parando vRx Dashboard App...${NC}"
        su root@192.168.1.200 -c "docker stop vrx-postgres vrx-app"
        ;;
    restart)
        echo -e "${BLUE}🔄 Reiniciando vRx Dashboard App...${NC}"
        su root@192.168.1.200 -c "docker restart vrx-postgres vrx-app"
        ;;
    status)
        echo -e "${BLUE}📊 Estado de vRx Dashboard App${NC}"
        su root@192.168.1.200 -c "docker ps"
        ;;
    logs)
        echo -e "${BLUE}📋 Logs de vRx Dashboard App${NC}"
        echo "Presiona Ctrl+C para salir"
        su root@192.168.1.200 -c "docker logs vrx-app -f"
        ;;
    health)
        echo -e "${BLUE}🔍 Verificando health check...${NC}"
        if curl -s -f http://localhost:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Aplicación funcionando correctamente${NC}"
        else
            echo -e "${RED}❌ Aplicación no responde${NC}"
        fi
        ;;
    shell)
        echo -e "${BLUE}🐚 Accediendo al contenedor...${NC}"
        su root@192.168.1.200 -c "docker exec -it vrx-app bash"
        ;;
    help|--help|-h)
        print_help
        ;;
    *)
        echo -e "${YELLOW}Comando no reconocido: $1${NC}"
        echo ""
        print_help
        exit 1
        ;;
esac

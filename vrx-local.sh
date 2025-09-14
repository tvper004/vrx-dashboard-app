#!/bin/bash

# Script de comandos rápidos para vRx Dashboard App desde máquina local
# Servidor: 192.168.1.200

SERVER_IP="192.168.1.200"
SERVER_USER="rleon"
APP_DIR="/home/rleon/vrx-dashboard"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

print_help() {
    echo -e "${BLUE}vRx Dashboard App - Comandos desde Local${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  connect    - Conectar al servidor"
    echo "  start      - Iniciar la aplicación"
    echo "  stop       - Parar la aplicación"
    echo "  restart    - Reiniciar la aplicación"
    echo "  status     - Ver estado de la aplicación"
    echo "  logs       - Ver logs en tiempo real"
    echo "  health     - Verificar health check"
    echo "  update     - Actualizar aplicación"
    echo "  help       - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 connect"
    echo "  $0 start"
    echo "  $0 status"
}

case "$1" in
    connect)
        echo -e "${GREEN}🔗 Conectando al servidor...${NC}"
        ssh $SERVER_USER@$SERVER_IP
        ;;
    start)
        echo -e "${GREEN}🚀 Iniciando vRx Dashboard App...${NC}"
        ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && ./vrx-commands-su.sh start"
        ;;
    stop)
        echo -e "${YELLOW}🛑 Parando vRx Dashboard App...${NC}"
        ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && ./vrx-commands-su.sh stop"
        ;;
    restart)
        echo -e "${BLUE}🔄 Reiniciando vRx Dashboard App...${NC}"
        ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && ./vrx-commands-su.sh restart"
        ;;
    status)
        echo -e "${BLUE}📊 Estado de vRx Dashboard App${NC}"
        ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && ./vrx-commands-su.sh status"
        ;;
    logs)
        echo -e "${BLUE}📋 Logs de vRx Dashboard App${NC}"
        echo "Presiona Ctrl+C para salir"
        ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && ./vrx-commands-su.sh logs"
        ;;
    health)
        echo -e "${BLUE}🔍 Verificando health check...${NC}"
        if curl -s -f http://$SERVER_IP:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Aplicación funcionando correctamente${NC}"
            echo -e "${GREEN}🌐 Disponible en: http://$SERVER_IP:8000${NC}"
        else
            echo -e "${RED}❌ Aplicación no responde${NC}"
        fi
        ;;
    update)
        echo -e "${BLUE}🔄 Actualizando aplicación...${NC}"
        echo "Copiando archivos actualizados..."
        scp -r backend/ $SERVER_USER@$SERVER_IP:$APP_DIR/
        scp -r frontend/ $SERVER_USER@$SERVER_IP:$APP_DIR/
        scp Dockerfile $SERVER_USER@$SERVER_IP:$APP_DIR/
        scp docker-compose.yml $SERVER_USER@$SERVER_IP:$APP_DIR/
        echo "Reiniciando aplicación..."
        ssh $SERVER_USER@$SERVER_IP "cd $APP_DIR && ./vrx-commands-su.sh restart"
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

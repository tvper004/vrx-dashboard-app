#!/bin/bash

# Script de comandos rápidos para vRx Dashboard App
# Servidor: 192.168.1.200

SERVER_IP="192.168.1.200"
SERVER_USER="rleon"
APP_DIR="/opt/vrx-dashboard"

# Colores
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_help() {
    echo -e "${BLUE}vRx Dashboard App - Comandos Rápidos${NC}"
    echo ""
    echo "Uso: $0 [comando]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start     - Iniciar la aplicación"
    echo "  stop      - Parar la aplicación"
    echo "  restart   - Reiniciar la aplicación"
    echo "  status    - Ver estado de la aplicación"
    echo "  logs      - Ver logs en tiempo real"
    echo "  monitor   - Monitorear recursos"
    echo "  health    - Verificar health check"
    echo "  shell     - Acceder al contenedor"
    echo "  update    - Actualizar aplicación"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 status"
}

run_remote() {
    ssh $SERVER_USER@$SERVER_IP "$1"
}

case "$1" in
    start)
        echo -e "${GREEN}🚀 Iniciando vRx Dashboard App...${NC}"
        run_remote "cd $APP_DIR && ./start-vrx-app.sh"
        ;;
    stop)
        echo -e "${YELLOW}🛑 Parando vRx Dashboard App...${NC}"
        run_remote "cd $APP_DIR && ./stop-vrx-app.sh"
        ;;
    restart)
        echo -e "${BLUE}🔄 Reiniciando vRx Dashboard App...${NC}"
        run_remote "cd $APP_DIR && ./stop-vrx-app.sh && sleep 5 && ./start-vrx-app.sh"
        ;;
    status)
        echo -e "${BLUE}📊 Estado de vRx Dashboard App${NC}"
        run_remote "cd $APP_DIR && docker-compose -f easypanel-docker-compose.yml ps"
        ;;
    logs)
        echo -e "${BLUE}📋 Logs de vRx Dashboard App${NC}"
        echo "Presiona Ctrl+C para salir"
        run_remote "cd $APP_DIR && docker-compose -f easypanel-docker-compose.yml logs -f"
        ;;
    monitor)
        echo -e "${BLUE}📈 Monitoreo de vRx Dashboard App${NC}"
        run_remote "cd $APP_DIR && ./monitor-vrx-app.sh"
        ;;
    health)
        echo -e "${BLUE}🔍 Verificando health check...${NC}"
        if curl -s -f http://$SERVER_IP:8000/health > /dev/null; then
            echo -e "${GREEN}✅ Aplicación funcionando correctamente${NC}"
        else
            echo -e "${YELLOW}❌ Aplicación no responde${NC}"
        fi
        ;;
    shell)
        echo -e "${BLUE}🐚 Accediendo al contenedor...${NC}"
        run_remote "cd $APP_DIR && docker-compose -f easypanel-docker-compose.yml exec app bash"
        ;;
    update)
        echo -e "${BLUE}🔄 Actualizando aplicación...${NC}"
        echo "Copiando archivos actualizados..."
        scp -r backend/ $SERVER_USER@$SERVER_IP:$APP_DIR/
        scp -r frontend/ $SERVER_USER@$SERVER_IP:$APP_DIR/
        scp Dockerfile $SERVER_USER@$SERVER_IP:$APP_DIR/
        scp easypanel-docker-compose.yml $SERVER_USER@$SERVER_IP:$APP_DIR/
        echo "Reiniciando aplicación..."
        run_remote "cd $APP_DIR && ./restart-vrx-app.sh"
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

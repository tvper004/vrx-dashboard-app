// Configuración de la aplicación React
const config = {
  // URL de la API backend
  API_BASE_URL: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  
  // Configuración de la aplicación
  APP_NAME: 'vRx Dashboard',
  APP_VERSION: '1.0.0',
  
  // Configuración de paginación
  DEFAULT_PAGE_SIZE: 10,
  PAGE_SIZE_OPTIONS: ['10', '20', '50', '100'],
  
  // Configuración de gráficos
  CHART_COLORS: [
    '#0088FE', '#00C49F', '#FFBB28', '#FF8042', 
    '#8884D8', '#82CA9D', '#FFC658', '#FF7C7C'
  ],
  
  // Configuración de filtros
  SEVERITY_LEVELS: ['High', 'Medium', 'Low'],
  OPERATING_SYSTEMS: ['Windows', 'Linux', 'macOS'],
  TASK_STATUSES: ['Succeeded', 'Failed', 'Cancelled', 'Running'],
  
  // Configuración de actualización automática
  AUTO_REFRESH_INTERVAL: 30000, // 30 segundos
  EXTRACTION_CHECK_INTERVAL: 5000, // 5 segundos
  
  // Configuración de notificaciones
  NOTIFICATION_DURATION: 4.5, // segundos
  
  // Configuración de tabla
  TABLE_SCROLL_X: 1200,
  TABLE_SIZE: 'small'
};

export default config;

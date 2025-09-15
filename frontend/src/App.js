import React, { useState, useEffect } from 'react';
import { Layout, Card, Row, Col, Statistic, Button, Modal, Form, Input, message, Spin, Tabs, Dropdown, Menu } from 'antd';
import { 
  DashboardOutlined, 
  SecurityScanOutlined, 
  DesktopOutlined, 
  ToolOutlined,
  SyncOutlined,
  CheckCircleOutlined,
  BarChartOutlined,
  FilePdfOutlined,
  DownOutlined,
  BugOutlined,
  MinusOutlined,
  ExpandOutlined,
  UnorderedListOutlined,
  DeleteOutlined,
  CloudUploadOutlined
} from '@ant-design/icons';
import axios from 'axios';
import jsPDF from 'jspdf';
import 'jspdf-autotable';
import OverviewTab from './tabs/OverviewTab';
import EndpointStatusTab from './tabs/EndpointStatusTab';
import TopAppsTab from './tabs/TopAppsTab';
import RemediationComparisonTab from './tabs/RemediationComparisonTab';
// Importamos las tablas de datos detallados
import VulnerabilitiesTable from './components/VulnerabilitiesTable';
import EndpointsTable from './components/EndpointsTable';
import TasksTable from './components/TasksTable';
import './App.css';

const { Header, Content } = Layout;
const { TabPane } = Tabs;

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

function App() {
  const [loading, setLoading] = useState(false);
  const [extractionModalVisible, setExtractionModalVisible] = useState(false);
  const [extractionStatus, setExtractionStatus] = useState(null);
  const [form] = Form.useForm();
  const [activeTabKey, setActiveTabKey] = useState('1');
  const [logModalVisible, setLogModalVisible] = useState(false);
  const [logContent, setLogContent] = useState('');
  const [isLogModalMinimized, setIsLogModalMinimized] = useState(false);
  const [isExtractionFinished, setIsExtractionFinished] = useState(false);

  // Cargar datos del dashboard al iniciar
  useEffect(() => {
    checkExtractionStatus();
    const statusInterval = setInterval(checkExtractionStatus, 10000); // Check status every 10 seconds
    return () => clearInterval(statusInterval);
  }, []);

  const checkExtractionStatus = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/extraction-status`);
      setExtractionStatus(response.data);
    } catch (error) {
      console.error('Error checking extraction status:', error);
    }
  };

  const handleExtraction = async (values) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/extract-data`, {
        api_key: values.api_key,
        dashboard_url: values.dashboard_url,
        extraction_type: 'all'
      });
      
      message.success('Extracción de datos iniciada');
      form.resetFields();
      setExtractionModalVisible(false);

      // Iniciar el modal de logs
      const extractionId = response.data.extraction_id;
      if (extractionId) {
        setLogContent('Iniciando conexión con el servidor...\n');
        setIsExtractionFinished(false);
        setLogModalVisible(true);

        let reconnectionAttempts = 0;

        const eventSource = new EventSource(`${API_BASE_URL}/stream-extraction-logs/${extractionId}`);
        
        eventSource.onmessage = (event) => {
          const data = event.data;
          if (data.startsWith('__END__')) {
            setLogContent(prev => prev + '\n\n✅ Proceso completado exitosamente. Ahora puedes recargar los datos o cerrar esta ventana.\n');
            setIsExtractionFinished(true);
            reconnectionAttempts = 0;
            eventSource.close();
          } else if (data.startsWith('__ERROR__:')) {
            const errorMsg = data.replace('__ERROR__:', '');
            setLogContent(prev => prev + `\n\n❌ ERROR: ${errorMsg}\n`);
            setIsExtractionFinished(true);
            eventSource.close();
          } else {
            // Si recibimos un mensaje, la conexión es buena. Reiniciamos el contador.
            if (reconnectionAttempts > 0) {
              setLogContent(prev => prev + '✅ Conexión restablecida.\n');
              reconnectionAttempts = 0;
            }
            setLogContent(prev => prev + data + '\n');
          }
        };

        eventSource.onerror = () => {
          reconnectionAttempts++;
          if (reconnectionAttempts === 1) {
            setLogContent(prev => prev + '\n\n⚠️ Conexión perdida. Intentando reconectar...\n');
          } else if (reconnectionAttempts > 5) {
            setLogContent(prev => prev + '\n\n❌ No se pudo restablecer la conexión. El proceso puede continuar en segundo plano. Puedes cerrar esta ventana y revisar el estado más tarde.\n');
            eventSource.close();
          }
        };
      }
      checkExtractionStatus(); // Check status immediately
    } catch (error) {
      message.error('Error iniciando extracción de datos');
      console.error('Error starting extraction:', error);
    }
  };

  const handleExport = (type) => {
    message.info('Generando PDF...');
    const doc = new jsPDF('p', 'pt', 'a4');
    
    // Lógica de exportación
    // Esto requeriría capturar el contenido de cada pestaña como imagen o tabla
    // y añadirlo al documento PDF.
    // Ejemplo simple:
    doc.text("Reporte vRx Dashboard", 40, 40);
    doc.text(`Tipo de Reporte: ${type}`, 40, 60);
    // ... añadir más contenido ...
    
    doc.save(`vRx-Report-${type}-${new Date().toISOString().split('T')[0]}.pdf`);
    message.success('PDF generado exitosamente');
  };

  const showClearDbConfirm = () => {
    Modal.confirm({
      title: '¿Estás seguro de que quieres limpiar la base de datos?',
      icon: <DeleteOutlined style={{ color: 'red' }} />,
      content: 'Esta acción es irreversible y borrará todos los datos de endpoints, vulnerabilidades, tareas y extracciones.',
      okText: 'Sí, limpiar',
      okType: 'danger',
      cancelText: 'No, cancelar',
      onOk() {
        handleClearDb();
      },
    });
  };

  const handleClearDb = async () => {
    try {
      setLoading(true);
      await axios.post(`${API_BASE_URL}/database/clear`);
      message.success('La base de datos ha sido limpiada exitosamente. La página se recargará.');
      setTimeout(() => window.location.reload(), 1500); // Recargar para refrescar todo
    } catch (error) {
      message.error('Error al limpiar la base de datos.');
      console.error('Error clearing database:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleForceCsvLoad = async () => {
    try {
      message.info('Iniciando carga forzada de archivos CSV en el servidor...');
      await axios.post(`${API_BASE_URL}/database/load-csvs`);
      message.success('Proceso de carga de CSVs iniciado en segundo plano. Los datos deberían aparecer en breve.');
    } catch (error) {
      message.error('Error al iniciar la carga forzada de CSVs.');
      console.error('Error forcing CSV load:', error);
    }
  };

  const handleExtractionButtonClick = () => {
    if (extractionStatus?.status === 'running') {
      setLogModalVisible(true);
    } else {
      setExtractionModalVisible(true);
    }
  };

  const exportMenuItems = [
    { key: 'general', label: 'Reporte General' },
    { key: 'overview', label: 'Exportar Resumen' },
    { key: 'status', label: 'Exportar Estado de Endpoints' },
    { key: 'top_apps', label: 'Exportar Top Aplicaciones Vulnerables' },
    { key: 'top_remediated', label: 'Exportar Top Aplicaciones Remediadas' },
    { key: 'comparison', label: 'Exportar Comparativo de Remediación' },
  ];

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header className="dashboard-header">
        <div className="dashboard-title">
          <SecurityScanOutlined style={{ marginRight: '8px' }} />
          vRx Dashboard
        </div>
        <div className="header-actions">
          <Button 
            icon={<SyncOutlined />} 
            onClick={handleExtractionButtonClick}
            loading={extractionStatus?.status === 'running'}
          >
            {extractionStatus?.status === 'running' ? 'Extrayendo...' : 'Extraer Datos'}
          </Button>
          <Dropdown menu={{ items: exportMenuItems, onClick: (e) => handleExport(e.key) }}>
            <Button>
              <FilePdfOutlined /> Exportar <DownOutlined />
            </Button>
          </Dropdown>
          <Button 
            danger
            icon={<DeleteOutlined />} 
            onClick={showClearDbConfirm}
          >
            Limpiar DB
          </Button>
        </div>
      </Header>
      
      <Layout>
        <Content style={{ padding: '24px', background: '#f0f2f5' }}>
          <Tabs activeKey={activeTabKey} onChange={setActiveTabKey}>
            <TabPane tab={<span><DashboardOutlined />Resumen</span>} key="1">
              <OverviewTab apiBaseUrl={API_BASE_URL} />
            </TabPane>
            <TabPane tab={<span><DesktopOutlined />Estado de Endpoints</span>} key="2">
              <EndpointStatusTab apiBaseUrl={API_BASE_URL} />
            </TabPane>
            <TabPane tab={<span><SecurityScanOutlined />Top Apps Vulnerables</span>} key="3">
              <TopAppsTab apiBaseUrl={API_BASE_URL} remediated={false} />
            </TabPane>
            <TabPane tab={<span><CheckCircleOutlined />Top Apps Remediadas</span>} key="4">
              <TopAppsTab apiBaseUrl={API_BASE_URL} remediated={true} />
            </TabPane>
            <TabPane tab={<span><BarChartOutlined />Comparativo</span>} key="5">
              <RemediationComparisonTab apiBaseUrl={API_BASE_URL} />
            </TabPane>
            {/* Pestañas de datos detallados añadidas */}
            <TabPane tab={<span><BugOutlined />Vulnerabilidades (Detalle)</span>} key="6">
              <VulnerabilitiesTable />
            </TabPane>
            <TabPane tab={<span><DesktopOutlined />Endpoints (Detalle)</span>} key="7">
              <EndpointsTable />
            </TabPane>
            <TabPane tab={<span><UnorderedListOutlined />Tareas (Detalle)</span>} key="8">
              <TasksTable />
            </TabPane>
          </Tabs>
        </Content>
      </Layout>
      
      <Modal
        title="Extraer Datos de Vicarius"
        open={extractionModalVisible}
        onCancel={() => setExtractionModalVisible(false)}
        footer={null}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleExtraction}
        >
          <Form.Item
            label="API Key"
            name="api_key"
            rules={[{ required: true, message: 'Por favor ingresa la API Key' }]}
          >
            <Input.Password placeholder="Ingresa tu API Key de Vicarius" />
          </Form.Item>
          
          <Form.Item
            label="URL del Dashboard"
            name="dashboard_url"
            rules={[{ required: true, message: 'Por favor ingresa la URL del dashboard' }]}
          >
            <Input placeholder="https://tu-instancia.vicarius.cloud" />
          </Form.Item>
          
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={loading} block>
              Iniciar Extracción
            </Button>
          </Form.Item>
        </Form>
      </Modal>

      <Modal
        title="Progreso de la Extracción"
        open={logModalVisible}
        onCancel={() => {
          setLogModalVisible(false);
          setIsLogModalMinimized(false); // Reset on close
        }}
        width={800}
        wrapClassName={isLogModalMinimized ? 'log-modal-minimized' : ''}
        maskClosable={false}
        footer={
          isLogModalMinimized
            ? [
                <Button
                  key="maximize"
                  icon={<ExpandOutlined />}
                  onClick={() => setIsLogModalMinimized(false)}
                >
                  Maximizar
                </Button>,
              ]
            : [
                <Button key="minimize" icon={<MinusOutlined />} onClick={() => setIsLogModalMinimized(true)}>
                  Minimizar
                </Button>,
                <Button 
                  key="loadcsv" 
                  icon={<CloudUploadOutlined />} 
                  onClick={handleForceCsvLoad} 
                  disabled={!isExtractionFinished}
                  title="Forzar la carga de los CSV generados al a base de datos."
                >
                  Cargar CSVs Manualmente
                </Button>,
                <Button 
                  key="reload"
                  type="primary"
                  icon={<SyncOutlined />} 
                  onClick={() => window.location.reload()} 
                  disabled={!isExtractionFinished}
                >
                  Recargar Datos
                </Button>,
                <Button key="close" onClick={() => {
                  setLogModalVisible(false);
                  setIsLogModalMinimized(false); // Reset on close
                }}>
                  Cerrar
                </Button>,
              ]
        }
      >
        <div className="terminal-output">
          <pre>
            <code>
              {logContent}
            </code>
          </pre>
          {!isExtractionFinished && <Spin style={{ marginLeft: '10px' }} />}
        </div>
      </Modal>
    </Layout>
  );
}

export default App;
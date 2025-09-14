import React, { useState, useEffect } from 'react';
import { Layout, Card, Row, Col, Statistic, Button, Modal, Form, Input, message, Spin, Alert } from 'antd';
import { 
  DashboardOutlined, 
  SecurityScanOutlined, 
  DesktopOutlined, 
  ToolOutlined,
  SyncOutlined,
  ExclamationCircleOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons';
import axios from 'axios';
import OverviewChart from './components/OverviewChart';
import VulnerabilitiesTable from './components/VulnerabilitiesTable';
import EndpointsTable from './components/EndpointsTable';
import TasksTable from './components/TasksTable';
import './App.css';

const { Header, Content, Sider } = Layout;

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

function App() {
  const [loading, setLoading] = useState(false);
  const [extractionModalVisible, setExtractionModalVisible] = useState(false);
  const [extractionStatus, setExtractionStatus] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [form] = Form.useForm();

  // Cargar datos del dashboard al iniciar
  useEffect(() => {
    loadDashboardData();
    checkExtractionStatus();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API_BASE_URL}/dashboard/overview`);
      setDashboardData(response.data);
    } catch (error) {
      message.error('Error cargando datos del dashboard');
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

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
      setLoading(true);
      await axios.post(`${API_BASE_URL}/extract-data`, {
        api_key: values.api_key,
        dashboard_url: values.dashboard_url,
        extraction_type: 'all'
      });
      
      message.success('Extracción de datos iniciada');
      setExtractionModalVisible(false);
      form.resetFields();
      
      // Verificar estado periódicamente
      const interval = setInterval(async () => {
        await checkExtractionStatus();
        if (extractionStatus?.status === 'completed' || extractionStatus?.status === 'failed') {
          clearInterval(interval);
          await loadDashboardData();
          if (extractionStatus?.status === 'completed') {
            message.success('Extracción completada exitosamente');
          } else {
            message.error('Error en la extracción de datos');
          }
        }
      }, 5000);
      
    } catch (error) {
      message.error('Error iniciando extracción de datos');
      console.error('Error starting extraction:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />;
      case 'running':
        return <SyncOutlined spin style={{ color: '#1890ff' }} />;
      case 'failed':
        return <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />;
      default:
        return <ClockCircleOutlined style={{ color: '#d9d9d9' }} />;
    }
  };

  const getStatusText = (status) => {
    switch (status) {
      case 'completed':
        return 'Completado';
      case 'running':
        return 'Ejecutándose';
      case 'failed':
        return 'Fallido';
      default:
        return 'Sin datos';
    }
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{ background: '#001529', padding: '0 24px' }}>
        <div style={{ color: 'white', fontSize: '20px', fontWeight: 'bold' }}>
          <SecurityScanOutlined style={{ marginRight: '8px' }} />
          vRx Dashboard
        </div>
      </Header>
      
      <Layout>
        <Sider width={200} style={{ background: '#fff' }}>
          <div style={{ padding: '16px' }}>
            <Button 
              type="primary" 
              icon={<SyncOutlined />} 
              onClick={() => setExtractionModalVisible(true)}
              style={{ width: '100%', marginBottom: '16px' }}
            >
              Extraer Datos
            </Button>
            
            {extractionStatus && (
              <Card size="small" style={{ marginBottom: '16px' }}>
                <div style={{ textAlign: 'center' }}>
                  <div style={{ marginBottom: '8px' }}>
                    {getStatusIcon(extractionStatus.status)}
                  </div>
                  <div style={{ fontSize: '12px', color: '#666' }}>
                    {getStatusText(extractionStatus.status)}
                  </div>
                  {extractionStatus.records_processed && (
                    <div style={{ fontSize: '10px', color: '#999' }}>
                      {extractionStatus.records_processed} registros
                    </div>
                  )}
                </div>
              </Card>
            )}
            
            <div style={{ borderTop: '1px solid #f0f0f0', paddingTop: '16px' }}>
              <div 
                className={`menu-item ${activeTab === 'overview' ? 'active' : ''}`}
                onClick={() => setActiveTab('overview')}
              >
                <DashboardOutlined /> Resumen
              </div>
              <div 
                className={`menu-item ${activeTab === 'vulnerabilities' ? 'active' : ''}`}
                onClick={() => setActiveTab('vulnerabilities')}
              >
                <SecurityScanOutlined /> Vulnerabilidades
              </div>
              <div 
                className={`menu-item ${activeTab === 'endpoints' ? 'active' : ''}`}
                onClick={() => setActiveTab('endpoints')}
              >
                <DesktopOutlined /> Endpoints
              </div>
              <div 
                className={`menu-item ${activeTab === 'tasks' ? 'active' : ''}`}
                onClick={() => setActiveTab('tasks')}
              >
                <ToolOutlined /> Tareas
              </div>
            </div>
          </div>
        </Sider>
        
        <Content style={{ padding: '24px', background: '#f0f2f5' }}>
          {loading && (
            <div style={{ textAlign: 'center', padding: '50px' }}>
              <Spin size="large" />
            </div>
          )}
          
          {activeTab === 'overview' && dashboardData && (
            <div>
              <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Total Endpoints"
                      value={dashboardData.total_endpoints}
                      prefix={<DesktopOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Total Vulnerabilidades"
                      value={dashboardData.total_vulnerabilities}
                      prefix={<SecurityScanOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Tareas Completadas"
                      value={dashboardData.tasks_by_status?.Succeeded || 0}
                      prefix={<CheckCircleOutlined />}
                    />
                  </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                  <Card>
                    <Statistic
                      title="Última Actualización"
                      value={dashboardData.last_update ? new Date(dashboardData.last_update).toLocaleDateString() : 'N/A'}
                      prefix={<ClockCircleOutlined />}
                    />
                  </Card>
                </Col>
              </Row>
              
              <Row gutter={[16, 16]}>
                <Col xs={24} lg={12}>
                  <Card title="Vulnerabilidades por Severidad">
                    <OverviewChart 
                      data={dashboardData.vulnerabilities_by_severity} 
                      type="pie"
                    />
                  </Card>
                </Col>
                <Col xs={24} lg={12}>
                  <Card title="Endpoints por Sistema Operativo">
                    <OverviewChart 
                      data={dashboardData.endpoints_by_os} 
                      type="bar"
                    />
                  </Card>
                </Col>
              </Row>
              
              <Row gutter={[16, 16]} style={{ marginTop: '16px' }}>
                <Col xs={24}>
                  <Card title="Estado de Tareas">
                    <OverviewChart 
                      data={dashboardData.tasks_by_status} 
                      type="doughnut"
                    />
                  </Card>
                </Col>
              </Row>
            </div>
          )}
          
          {activeTab === 'vulnerabilities' && (
            <VulnerabilitiesTable />
          )}
          
          {activeTab === 'endpoints' && (
            <EndpointsTable />
          )}
          
          {activeTab === 'tasks' && (
            <TasksTable />
          )}
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
    </Layout>
  );
}

export default App;

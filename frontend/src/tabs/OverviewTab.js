// Contenido del componente para la pestaña de Resumen (la vista original)
import React, { useState, useEffect } from 'react';
import { Card, Row, Col, Statistic, message, Spin } from 'antd';
import { DesktopOutlined, SecurityScanOutlined, CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons';
import axios from 'axios';
import OverviewChart from '../components/OverviewChart';

const OverviewTab = ({ apiBaseUrl }) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);

  useEffect(() => {
    const loadData = async () => {
      try {
        setLoading(true);
        const response = await axios.get(`${apiBaseUrl}/dashboard/overview`);
        setData(response.data);
      } catch (error) {
        message.error('Error cargando datos del resumen');
      } finally {
        setLoading(false);
      }
    };
    loadData();
  }, [apiBaseUrl]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: '50px' }}><Spin size="large" /></div>;
  }

  if (!data) {
    return <div style={{ textAlign: 'center', padding: '50px' }}>No hay datos para mostrar.</div>;
  }

  return (
    <div>
      <Row gutter={[16, 16]} style={{ marginBottom: '24px' }}>
        <Col xs={24} sm={12} md={6}><Card><Statistic title="Total Endpoints" value={data.total_endpoints} prefix={<DesktopOutlined />} /></Card></Col>
        <Col xs={24} sm={12} md={6}><Card><Statistic title="Total Vulnerabilidades" value={data.total_vulnerabilities} prefix={<SecurityScanOutlined />} /></Card></Col>
        <Col xs={24} sm={12} md={6}><Card><Statistic title="Tareas Completadas" value={data.tasks_by_status?.Succeeded || 0} prefix={<CheckCircleOutlined />} /></Card></Col>
        <Col xs={24} sm={12} md={6}><Card><Statistic title="Última Actualización" value={data.last_update ? new Date(data.last_update).toLocaleDateString() : 'N/A'} prefix={<ClockCircleOutlined />} /></Card></Col>
      </Row>
      <Row gutter={[16, 16]}>
        <Col xs={24} lg={12}><Card title="Vulnerabilidades por Severidad"><OverviewChart data={data.vulnerabilities_by_severity} type="pie" /></Card></Col>
        <Col xs={24} lg={12}><Card title="Endpoints por Sistema Operativo"><OverviewChart data={data.endpoints_by_os} type="bar" /></Card></Col>
      </Row>
    </div>
  );
};

export default OverviewTab;

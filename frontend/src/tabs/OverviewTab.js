import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Statistic, Spin, Alert } from 'antd';
import { DesktopOutlined, BugOutlined, ToolOutlined, ClockCircleOutlined } from '@ant-design/icons';
import axios from 'axios';

const OverviewTab = ({ apiBaseUrl }) => {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${apiBaseUrl}/dashboard/overview`);
                setData(response.data);
                setError(null);
            } catch (err) {
                setError('No se pudieron cargar los datos del resumen.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [apiBaseUrl]);

    if (loading) return <Spin tip="Cargando Resumen..." />;
    if (error) return <Alert message="Error" description={error} type="error" showIcon />;
    if (!data) return <Alert message="Sin Datos" description="No hay datos para mostrar. Inicia una extracción." type="info" showIcon />;

    return (
        <div className="overview-stats">
            <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                    <Card><Statistic title="Total Endpoints" value={data.total_endpoints} prefix={<DesktopOutlined />} /></Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card><Statistic title="Total Vulnerabilidades" value={data.total_vulnerabilities} prefix={<BugOutlined />} /></Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card><Statistic title="Tareas Exitosas" value={data.tasks_by_status?.Succeeded || 0} prefix={<ToolOutlined />} /></Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card><Statistic title="Última Actualización" value={data.last_update ? new Date(data.last_update).toLocaleString() : 'N/A'} prefix={<ClockCircleOutlined />} /></Card>
                </Col>
            </Row>
        </div>
    );
};

export default OverviewTab;


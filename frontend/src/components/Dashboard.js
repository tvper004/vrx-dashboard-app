import React, { useState, useEffect } from 'react';
import { Tabs, Card, Row, Col, Statistic, Spin, Alert } from 'antd';
import axios from 'axios';
import { PieChartOutlined, DesktopOutlined, BugOutlined, UnorderedListOutlined } from '@ant-design/icons';

// Importar los componentes de tabla
import VulnerabilitiesTable from './VulnerabilitiesTable';
import EndpointsTable from './EndpointsTable';
import TasksTable from './TasksTable';

const { TabPane } = Tabs;

const Dashboard = () => {
    const [overviewData, setOverviewData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.get('/dashboard/overview');
                setOverviewData(response.data);
                setError(null);
            } catch (err) {
                setError('No se pudieron cargar los datos del resumen. Por favor, realiza una extracción de datos.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
        // Recargar datos cada 30 segundos
        const interval = setInterval(fetchData, 30000);
        return () => clearInterval(interval);
    }, []);

    const renderOverview = () => {
        if (loading) {
            return <Spin tip="Cargando Resumen..." size="large" />;
        }
        if (error) {
            return <Alert message="Error" description={error} type="error" showIcon />;
        }
        if (!overviewData) {
            return <Alert message="Sin Datos" description="No hay datos para mostrar. Inicia una extracción." type="info" showIcon />;
        }

        return (
            <Row gutter={[16, 16]}>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Total Endpoints"
                            value={overviewData.total_endpoints}
                            prefix={<DesktopOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Total Vulnerabilidades"
                            value={overviewData.total_vulnerabilities}
                            prefix={<BugOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Vulnerabilidades Críticas"
                            value={overviewData.vulnerabilities_by_severity?.Critical || 0}
                            valueStyle={{ color: '#cf1322' }}
                            prefix={<BugOutlined />}
                        />
                    </Card>
                </Col>
                <Col xs={24} sm={12} md={6}>
                    <Card>
                        <Statistic
                            title="Última Actualización"
                            value={overviewData.last_update ? new Date(overviewData.last_update).toLocaleString() : 'N/A'}
                        />
                    </Card>
                </Col>
            </Row>
        );
    };

    return (
        <div style={{ padding: '24px' }}>
            <Tabs defaultActiveKey="1" type="card">
                <TabPane
                    tab={<span><PieChartOutlined /> Resumen</span>}
                    key="1"
                >
                    {renderOverview()}
                </TabPane>
                <TabPane
                    tab={<span><BugOutlined /> Vulnerabilidades</span>}
                    key="2"
                >
                    <VulnerabilitiesTable />
                </TabPane>
                <TabPane
                    tab={<span><DesktopOutlined /> Endpoints</span>}
                    key="3"
                >
                    <EndpointsTable />
                </TabPane>
                <TabPane
                    tab={<span><UnorderedListOutlined /> Tareas</span>}
                    key="4"
                >
                    <TasksTable />
                </TabPane>
            </Tabs>
        </div>
    );
};

export default Dashboard;
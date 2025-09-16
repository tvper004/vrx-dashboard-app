import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Spin, Alert, Typography } from 'antd';
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const { Title } = Typography;
const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#844d8f', '#ff5733', '#c70039'];

const EndpointStatusTab = ({ apiBaseUrl }) => {
    const [data, setData] = useState({ status_chart: [], endpoint_table: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${apiBaseUrl}/dashboard/endpoint-status`);
                setData(response.data);
                setError(null);
            } catch (err) {
                setError('No se pudieron cargar los datos de estado de endpoints.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [apiBaseUrl]);

    const columns = [
        { title: 'Hostname', dataIndex: 'hostname', key: 'hostname', fixed: 'left', width: 200, sorter: (a, b) => a.hostname.localeCompare(b.hostname) },
        { title: 'Sistema Operativo', dataIndex: 'operating_system', key: 'operating_system', width: 150, sorter: (a, b) => a.operating_system.localeCompare(b.operating_system) },
        { title: 'Vulnerabilidades Totales', dataIndex: 'total_vulnerabilities', key: 'total_vulnerabilities', width: 100, sorter: (a, b) => a.total_vulnerabilities - b.total_vulnerabilities },
        { title: 'Críticas', dataIndex: 'critical', key: 'critical', width: 80, sorter: (a, b) => a.critical - b.critical },
        { title: 'Altas', dataIndex: 'high', key: 'high', width: 80, sorter: (a, b) => a.high - b.high },
        { title: 'Bajas', dataIndex: 'low', key: 'low', width: 80, sorter: (a, b) => a.low - b.low },
    ];

    if (loading) return <Spin tip="Cargando..." />;
    if (error) return <Alert message="Error" description={error} type="error" showIcon />;

    return (
        <Row gutter={[16, 16]}>
            <Col xs={24} md={8}>
                <Card title={<Title level={4}>Endpoints por Sistema Operativo</Title>}>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie data={data.status_chart} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} fill="#8884d8" label>
                                {data.status_chart.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip formatter={(value, name) => [value, name]} />
                            <Legend />
                        </PieChart>
                    </ResponsiveContainer>
                </Card>
            </Col>
            <Col xs={24} md={16}>
                <Card title={<Title level={4}>Detalle de Endpoints</Title>}>
                    <Table columns={columns} dataSource={data.endpoint_table} rowKey="hostname" pagination={{ pageSize: 10 }} scroll={{ x: 1200 }} />
                </Card>
            </Col>
        </Row>
    );
};

export default EndpointStatusTab;
import React, { useState, useEffect } from 'react';
import { Row, Col, Card, Table, Spin, Alert, Typography } from 'antd';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import axios from 'axios';

const { Title } = Typography;

const TopAppsTab = ({ apiBaseUrl, remediated }) => {
    const [data, setData] = useState({ chart_data: [], table_data: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${apiBaseUrl}/dashboard/top-apps`, {
                    params: { remediated }
                });
                setData(response.data);
                setError(null);
            } catch (err) {
                setError('No se pudieron cargar los datos.');
                console.error(err);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, [apiBaseUrl, remediated]);

    const columns = [
        { title: 'Aplicación', dataIndex: 'product_name', key: 'product_name', fixed: 'left', width: 250 },
        { title: 'Total Vulns', dataIndex: 'total_vulnerabilities', key: 'total_vulnerabilities', sorter: (a, b) => a.total_vulnerabilities - b.total_vulnerabilities },
        { title: 'Endpoints Afectados', dataIndex: 'affected_endpoints', key: 'affected_endpoints', sorter: (a, b) => a.affected_endpoints - b.affected_endpoints },
        { title: 'Críticas', dataIndex: 'critical', key: 'critical' },
        { title: 'Altas', dataIndex: 'high', key: 'high' },
        { title: 'Bajas', dataIndex: 'low', key: 'low' },
    ];

    if (loading) return <Spin tip="Cargando..." />;
    if (error) return <Alert message="Error" description={error} type="error" showIcon />;

    return (
        <Row gutter={[16, 16]}>
            <Col span={24}>
                <Card title={<Title level={5}>Top 15 Aplicaciones {remediated ? 'Remediadas' : 'Vulnerables'}</Title>}>
                    <ResponsiveContainer width="100%" height={400}>
                        <BarChart data={data.chart_data} layout="vertical" margin={{ top: 5, right: 30, left: 100, bottom: 5 }}>
                            <CartesianGrid strokeDasharray="3 3" />
                            <XAxis type="number" />
                            <YAxis dataKey="name" type="category" width={150} interval={0} />
                            <Tooltip />
                            <Legend />
                            <Bar dataKey="value" name="Vulnerabilidades" fill={remediated ? "#82ca9d" : "#8884d8"} />
                        </BarChart>
                    </ResponsiveContainer>
                </Card>
            </Col>
            <Col span={24}>
                <Card><Table columns={columns} dataSource={data.table_data} rowKey="product_name" pagination={{ pageSize: 10 }} scroll={{ x: 800 }} /></Card>
            </Col>
        </Row>
    );
};

export default TopAppsTab;


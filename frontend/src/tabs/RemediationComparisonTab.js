import React, { useState, useEffect } from 'react';
import { Row, Col, Typography, Card, DatePicker, Button, Space, Alert, Spin } from 'antd';
import axios from 'axios';
import moment from 'moment';

const { Title } = Typography;
const { RangePicker } = DatePicker;

const API_BASE_URL = process.env.REACT_APP_API_URL || '';

const RemediationComparisonTab = () => {
    const [startDate, setStartDate] = useState(null);
    const [endDate, setEndDate] = useState(null);
    const [resolvedVulnerabilities, setResolvedVulnerabilities] = useState(null);
    const [totalResolved, setTotalResolved] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    // Load total resolved vulnerabilities on component mount
    useEffect(() => {
        const loadTotalResolved = async () => {
            try {
                const response = await axios.get(`${API_BASE_URL}/dashboard/remediation-comparison`);
                setTotalResolved(response.data.resolved_vulnerabilities);
            } catch (err) {
                console.error('Error loading total resolved vulnerabilities:', err);
            }
        };
        loadTotalResolved();
    }, []);

    const handleDateChange = (dates) => {
        if (dates) {
            setStartDate(dates[0]);
            setEndDate(dates[1]);
        } else {
            setStartDate(null);
            setEndDate(null);
        }
    };

    const handleCompare = async () => {
        if (!startDate || !endDate) {
            setError('Por favor, selecciona un rango de fechas válido.');
            setResolvedVulnerabilities(null);
            return;
        }

        setLoading(true);
        setError(null);
        setResolvedVulnerabilities(null);

        try {
            const formattedStartDate = startDate.format('YYYY-MM-DD');
            const formattedEndDate = endDate.format('YYYY-MM-DD');

            const response = await axios.get(`${API_BASE_URL}/dashboard/remediation-comparison`, {
                params: {
                    start_date: formattedStartDate,
                    end_date: formattedEndDate,
                },
            });
            setResolvedVulnerabilities(response.data.resolved_vulnerabilities);
        } catch (err) {
            console.error('Error fetching remediation comparison:', err);
            setError('No se pudieron cargar los datos de comparación de remediación.');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div style={{ padding: '24px' }}>
            <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>
                Comparativo de Vulnerabilidades Resueltas por Fecha
            </Title>
            <Card>
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                    <Space>
                        <RangePicker onChange={handleDateChange} />
                        <Button
                            type="primary"
                            onClick={handleCompare}
                            loading={loading}
                            disabled={!startDate || !endDate}
                        >
                            Comparar
                        </Button>
                    </Space>
                    {error && <Alert message="Error" description={error} type="error" showIcon />}
                    {loading && <Spin tip="Cargando datos..." style={{ marginTop: '20px' }} />}
                    {totalResolved !== null && (
                        <Alert
                            message="Total de Vulnerabilidades Resueltas"
                            description={`Total de vulnerabilidades resueltas: ${totalResolved}`}
                            type="success"
                            showIcon
                        />
                    )}
                    {resolvedVulnerabilities !== null && !loading && !error && (
                        <Alert
                            message="Vulnerabilidades Resueltas en el Período"
                            description={`Se resolvieron ${resolvedVulnerabilities} vulnerabilidades en el rango de fechas seleccionado.`}
                            type="info"
                            showIcon
                        />
                    )}
                </Space>
            </Card>
        </div>
    );
};

export default RemediationComparisonTab;


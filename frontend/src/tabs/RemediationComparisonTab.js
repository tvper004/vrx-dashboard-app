import React from 'react';
import { Row, Col, Typography, Card } from 'antd';
import TopAppsTab from './TopAppsTab';

const { Title } = Typography;

const RemediationComparisonTab = ({ apiBaseUrl }) => {
    return (
        <div>
            <Title level={3} style={{ textAlign: 'center', marginBottom: '24px' }}>
                Comparativo de Remediación
            </Title>
            <Row gutter={[24, 24]}>
                <Col xs={24} lg={12}>
                    <TopAppsTab apiBaseUrl={apiBaseUrl} remediated={false} />
                </Col>
                <Col xs={24} lg={12}>
                    <TopAppsTab apiBaseUrl={apiBaseUrl} remediated={true} />
                </Col>
            </Row>
        </div>
    );
};

export default RemediationComparisonTab;


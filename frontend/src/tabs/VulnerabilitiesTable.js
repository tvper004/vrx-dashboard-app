import React, { useState, useEffect } from 'react';
import { Table, Card, Input, Select, Tag, Space, Button, message, Spin } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const VulnerabilitiesTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [filters, setFilters] = useState({
    severity: null,
    asset: null
  });

  const columns = [
    {
      title: 'Asset',
      dataIndex: 'asset',
      key: 'asset',
      sorter: true,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="Buscar asset"
            value={selectedKeys[0]}
            onChange={e => setSelectedKeys(e.target.value ? [e.target.value] : [])}
            onPressEnter={() => confirm()}
            style={{ width: 188, marginBottom: 8, display: 'block' }}
          />
          <Space>
            <Button
              type="primary"
              onClick={() => confirm()}
              icon={<SearchOutlined />}
              size="small"
              style={{ width: 90 }}
            >
              Buscar
            </Button>
            <Button onClick={() => clearFilters()} size="small" style={{ width: 90 }}>
              Reset
            </Button>
          </Space>
        </div>
      ),
      onFilter: (value, record) => record.asset.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: 'CVE',
      dataIndex: 'cve',
      key: 'cve',
      width: 120,
      render: (cve) => (
        <Tag color="red" style={{ cursor: 'pointer' }}>
          {cve}
        </Tag>
      ),
    },
    {
      title: 'Severidad',
      dataIndex: 'severity',
      key: 'severity',
      width: 120,
      render: (severity) => {
        let color = 'default';
        if (severity === 'High') color = 'red';
        else if (severity === 'Medium') color = 'orange';
        else if (severity === 'Low') color = 'green';
        return <Tag color={color}>{severity}</Tag>;
      },
      filters: [
        { text: 'High', value: 'High' },
        { text: 'Medium', value: 'Medium' },
        { text: 'Low', value: 'Low' },
      ],
      onFilter: (value, record) => record.severity === value,
    },
    {
      title: 'Producto',
      dataIndex: 'product_name',
      key: 'product_name',
      ellipsis: true,
    },
    {
      title: 'CVSS Score',
      dataIndex: 'v3_base_score',
      key: 'v3_base_score',
      width: 100,
      sorter: true,
      render: (score) => score ? score.toFixed(1) : 'N/A',
    },
    {
      title: 'Resumen',
      dataIndex: 'vulnerability_summary',
      key: 'vulnerability_summary',
      ellipsis: true,
      width: 300,
    },
    {
      title: 'Fecha',
      dataIndex: 'created_at',
      key: 'created_at',
      width: 120,
      render: (date) => new Date(date).toLocaleDateString(),
      sorter: true,
    },
  ];

  const loadData = async (page = 1, pageSize = 10) => {
    try {
      setLoading(true);
      const params = {
        limit: pageSize,
        offset: (page - 1) * pageSize,
        ...filters
      };

      const response = await axios.get(`${API_BASE_URL}/dashboard/vulnerabilities`, { params });
      
      setData(response.data.data);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: response.data.total
      }));
    } catch (error) {
      message.error('Error cargando vulnerabilidades');
      console.error('Error loading vulnerabilities:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [filters]);

  const handleTableChange = (paginationInfo, filters, sorter) => {
    loadData(paginationInfo.current, paginationInfo.pageSize);
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleRefresh = () => {
    loadData(pagination.current, pagination.pageSize);
  };

  return (
    <Card 
      title="Vulnerabilidades" 
      extra={
        <Space>
          <Select
            placeholder="Filtrar por severidad"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => handleFilterChange('severity', value)}
          >
            <Option value="High">High</Option>
            <Option value="Medium">Medium</Option>
            <Option value="Low">Low</Option>
          </Select>
          <Button icon={<ReloadOutlined />} onClick={handleRefresh}>
            Actualizar
          </Button>
        </Space>
      }
    >
      <Table
        columns={columns}
        dataSource={data}
        loading={loading}
        rowKey="id"
        pagination={{
          ...pagination,
          showSizeChanger: true,
          showQuickJumper: true,
          showTotal: (total, range) => 
            `${range[0]}-${range[1]} de ${total} vulnerabilidades`,
        }}
        onChange={handleTableChange}
        scroll={{ x: 1200 }}
        size="small"
      />
    </Card>
  );
};

export default VulnerabilitiesTable;



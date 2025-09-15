import React, { useState, useEffect } from 'react';
import { Table, Card, Input, Select, Tag, Space, Button, message, Spin } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const EndpointsTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [filters, setFilters] = useState({
    os_filter: null
  });

  const columns = [
    {
      title: 'Hostname',
      dataIndex: 'hostname',
      key: 'hostname',
      sorter: true,
      filterDropdown: ({ setSelectedKeys, selectedKeys, confirm, clearFilters }) => (
        <div style={{ padding: 8 }}>
          <Input
            placeholder="Buscar hostname"
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
      onFilter: (value, record) => record.hostname.toLowerCase().includes(value.toLowerCase()),
    },
    {
      title: 'Sistema Operativo',
      dataIndex: 'operating_system',
      key: 'operating_system',
      width: 200,
      render: (os) => {
        let color = 'default';
        if (os.includes('Windows')) color = 'blue';
        else if (os.includes('Linux')) color = 'green';
        else if (os.includes('macOS')) color = 'purple';
        return <Tag color={color}>{os}</Tag>;
      },
      filters: [
        { text: 'Windows', value: 'Windows' },
        { text: 'Linux', value: 'Linux' },
        { text: 'macOS', value: 'macOS' },
      ],
      onFilter: (value, record) => record.operating_system.includes(value),
    },
    {
      title: 'Versión',
      dataIndex: 'version',
      key: 'version',
      width: 120,
    },
    {
      title: 'ID Endpoint',
      dataIndex: 'endpoint_id',
      key: 'endpoint_id',
      width: 120,
      sorter: true,
    },
    {
      title: 'Última Actualización',
      dataIndex: 'endpoint_updated_at',
      key: 'endpoint_updated_at',
      width: 150,
      render: (date) => date ? new Date(date).toLocaleString() : 'N/A',
      sorter: true,
    },
    {
      title: 'Fecha Creación',
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

      const response = await axios.get(`${API_BASE_URL}/dashboard/endpoints`, { params });
      
      setData(response.data.data);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: response.data.total
      }));
    } catch (error) {
      message.error('Error cargando endpoints');
      console.error('Error loading endpoints:', error);
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
      title="Endpoints" 
      extra={
        <Space>
          <Select
            placeholder="Filtrar por SO"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => handleFilterChange('os_filter', value)}
          >
            <Option value="Windows">Windows</Option>
            <Option value="Linux">Linux</Option>
            <Option value="macOS">macOS</Option>
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
            `${range[0]}-${range[1]} de ${total} endpoints`,
        }}
        onChange={handleTableChange}
        scroll={{ x: 1000 }}
        size="small"
      />
    </Card>
  );
};

export default EndpointsTable;



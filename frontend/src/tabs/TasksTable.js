import React, { useState, useEffect } from 'react';
import { Table, Card, Input, Select, Tag, Space, Button, message, Spin } from 'antd';
import { SearchOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { Option } = Select;

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

const TasksTable = () => {
  const [data, setData] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [filters, setFilters] = useState({
    status_filter: null,
    asset_filter: null
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
      title: 'ID Tarea',
      dataIndex: 'task_id',
      key: 'task_id',
      width: 120,
      sorter: true,
    },
    {
      title: 'Tipo de Tarea',
      dataIndex: 'task_type',
      key: 'task_type',
      width: 200,
      ellipsis: true,
    },
    {
      title: 'Estado',
      dataIndex: 'action_status',
      key: 'action_status',
      width: 120,
      render: (status) => {
        let color = 'default';
        if (status === 'Succeeded') color = 'green';
        else if (status === 'Failed') color = 'red';
        else if (status === 'Cancelled') color = 'orange';
        else if (status === 'Running') color = 'blue';
        return <Tag color={color}>{status}</Tag>;
      },
      filters: [
        { text: 'Succeeded', value: 'Succeeded' },
        { text: 'Failed', value: 'Failed' },
        { text: 'Cancelled', value: 'Cancelled' },
        { text: 'Running', value: 'Running' },
      ],
      onFilter: (value, record) => record.action_status === value,
    },
    {
      title: 'Mensaje de Estado',
      dataIndex: 'message_status',
      key: 'message_status',
      ellipsis: true,
      width: 200,
    },
    {
      title: 'Fecha Creación',
      dataIndex: 'create_at',
      key: 'create_at',
      width: 150,
      render: (date) => date ? new Date(date).toLocaleString() : 'N/A',
      sorter: true,
    },
    {
      title: 'Fecha Actualización',
      dataIndex: 'update_at',
      key: 'update_at',
      width: 150,
      render: (date) => date ? new Date(date).toLocaleString() : 'N/A',
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

      const response = await axios.get(`${API_BASE_URL}/dashboard/tasks`, { params });
      
      setData(response.data.data);
      setPagination(prev => ({
        ...prev,
        current: page,
        pageSize,
        total: response.data.total
      }));
    } catch (error) {
      message.error('Error cargando tareas');
      console.error('Error loading tasks:', error);
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
      title="Tareas de Endpoints" 
      extra={
        <Space>
          <Select
            placeholder="Filtrar por estado"
            style={{ width: 150 }}
            allowClear
            onChange={(value) => handleFilterChange('status_filter', value)}
          >
            <Option value="Succeeded">Succeeded</Option>
            <Option value="Failed">Failed</Option>
            <Option value="Cancelled">Cancelled</Option>
            <Option value="Running">Running</Option>
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
            `${range[0]}-${range[1]} de ${total} tareas`,
        }}
        onChange={handleTableChange}
        scroll={{ x: 1200 }}
        size="small"
      />
    </Card>
  );
};

export default TasksTable;



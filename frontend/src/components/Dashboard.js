import React, { useState, useEffect } from 'react';
import { Tabs, Card, Row, Col, Statistic, Spin, Alert } from 'antd';
import axios from 'axios';
import { PieChartOutlined, DesktopOutlined, BugOutlined, UnorderedListOutlined } from '@ant-design/icons';

// Estos serían tus componentes de tabla, asegúrate de importarlos correctamente
// import VulnerabilitiesTable from './VulnerabilitiesTable';
// import EndpointsTable from './EndpointsTable';
// import TasksTable from './TasksTable';

const { TabPane } = Tabs;

// Componentes de ejemplo si no los tienes
const VulnerabilitiesTable = () => <div>Tabla de Vulnerabilidades aquí</div>;
const EndpointsTable = () => <div>Tabla de Endpoints aquí</div>;
const TasksTable = () => <div>Tabla de Tareas aquí</div>;


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

```

**Para integrarlo:**
1.  Crea el archivo `frontend/src/components/Dashboard.js` y pega el código anterior.
2.  Abre tu archivo principal `frontend/src/App.js`.
3.  Importa el nuevo componente: `import Dashboard from './components/Dashboard';`.
4.  Reemplaza el contenido actual de tu `App.js` para que renderice el componente `<Dashboard />`.

### 2. Solución para la Lentitud de Extracción

El problema principal es que la aplicación inserta los datos en la base de datos fila por fila, lo cual es extremadamente lento para cientos o miles de registros.

Voy a modificar tu archivo `backend/main.py` para usar el comando `COPY` de PostgreSQL, que es la forma más rápida de cargar grandes volúmenes de datos desde un CSV. Este cambio reducirá el tiempo de carga de minutos a solo unos segundos.

```diff
from contextlib import asynccontextmanager 
import psycopg2
from psycopg2.extras import RealDictCursor
import io
import json

# Configuración de logging
        logger.error(f"Error procesando archivos CSV: {e}")
        raise

async def bulk_load_csv(file_path: str, table_name: str, columns: list):
    """Carga datos desde un archivo CSV a una tabla usando el comando COPY de PostgreSQL."""
    try:
        df = pd.read_csv(file_path, usecols=columns)
        df = df.reindex(columns=columns) # Asegurar el orden de las columnas

        # Limpiar datos: reemplazar NaN por None (NULL en SQL) y manejar saltos de línea
        df = df.replace({pd.NA: None, pd.NaT: None})
        for col in df.select_dtypes(include=['object']).columns:
            df[col] = df[col].str.replace('\n', ' ', regex=False).str.replace('\r', ' ', regex=False)

        with engine.connect() as conn:
            raw_conn = conn.connection
            with raw_conn.cursor() as cursor:
                # Vaciar la tabla antes de cargar nuevos datos
                cursor.execute(f"TRUNCATE TABLE {table_name} RESTART IDENTITY;")
                
                # Preparar CSV en memoria
                output = io.StringIO()
                df.to_csv(output, sep='\t', header=False, index=False, na_rep='\\N')
                output.seek(0)
                
                # Ejecutar COPY
                cursor.copy_expert(
                    f"COPY {table_name} ({','.join(columns)}) FROM STDIN WITH (FORMAT csv, DELIMITER E'\\t', NULL '\\N')",
                    output
                )
            conn.commit()
        logger.info(f"Cargados {len(df)} registros en la tabla '{table_name}' exitosamente.")
    except Exception as e:
        logger.error(f"Error en la carga masiva para la tabla {table_name}: {e}")
        raise

async def load_endpoints_csv(file_path: str):
    """Cargar datos de endpoints desde CSV"""
    columns = [
        'ID', 'HOSTNAME', 'HASH', 'SO', 'VERSION', 
        'status', 'sub_status', 'endpointUpdatedAt'
    ]
    # Renombrar columnas para coincidir con la tabla
    # Esta parte se manejará en la función bulk_load_csv
    await bulk_load_csv(file_path, 'endpoints', columns)

async def load_vulnerabilities_csv(file_path: str):
    """Cargar datos de vulnerabilidades desde CSV"""
    columns = [
        'asset', 'assethash', 'group', 'productName', 'productRawEntryName',
        'sensitivityLevelName', 'cve', 'vulnerabilityid', 'patchid', 'patchName',
        'patchReleaseDate', 'createAt', 'updateAt', 'link', 'vulnerabilitySummary',
        'V3BaseScore', 'V3ExploitabilityLevel'
    ]
    await bulk_load_csv(file_path, 'vulnerabilities', columns)

async def load_patches_csv(file_path: str):
    """Cargar datos de patches desde CSV"""
    columns = [
        'Asset', 'SO', 'PatchName', 'SeverityLevel', 
        'SeverityName', 'Description', 'PatchID'
    ]
    await bulk_load_csv(file_path, 'endpoint_patches', columns)

async def load_tasks_csv(file_path: str):
    """Cargar datos de tareas desde CSV"""
    columns = [
        'Taskid', 'AutomationId', 'AutomationName', 'Asset', 'TaskType',
        'PublisherName', 'PathOrProduct', 'PathOrProductDesc',
        'ActionStatus', 'MessageStatus', 'Username', 'CreateAt', 'UpdateAt'
    ]
    await bulk_load_csv(file_path, 'endpoint_event_tasks', columns)

if __name__ == "__main__":
    import uvicorn


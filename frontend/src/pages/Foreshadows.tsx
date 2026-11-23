import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams } from 'react-router-dom';
import {
  Card, Table, Button, Tag, Space, Modal, Form, Input, Select,
  InputNumber, Switch, message, Tooltip, Popconfirm, Statistic,
  Row, Col, Empty, Divider, Badge, Alert, Pagination, Dropdown, theme
} from 'antd';
import type { MenuProps } from 'antd';
import {
  PlusOutlined, SyncOutlined, EditOutlined, DeleteOutlined,
  CheckCircleOutlined, CloseCircleOutlined, ExclamationCircleOutlined,
  BulbOutlined, EyeOutlined, FlagOutlined, WarningOutlined,
  ClockCircleOutlined, MoreOutlined, ReloadOutlined, InfoCircleOutlined
} from '@ant-design/icons';
import { foreshadowApi, chapterApi, characterApi } from '../services/api';
import type {
  Foreshadow, ForeshadowCreate, ForeshadowUpdate, ForeshadowStats,
  ForeshadowStatus, ForeshadowCategory, Chapter, Character
} from '../types';
import { eventBus, EventNames } from '../store/eventBus';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

const { TextArea } = Input;
const { Option } = Select;

// 状态配置
const STATUS_CONFIG: Record<ForeshadowStatus, { label: string; color: string; icon: React.ReactNode }> = {
  pending: { label: i18n.t('foreshadows:plantar'), color: 'default', icon: <ClockCircleOutlined /> },
  planted: { label: i18n.t('foreshadows:plantada'), color: 'green', icon: <BulbOutlined /> },
  resolved: { label: i18n.t('foreshadows:resolvida'), color: 'blue', icon: <CheckCircleOutlined /> },
  partially_resolved: { label: i18n.t('foreshadows:parcialmenteResolvida'), color: 'orange', icon: <ExclamationCircleOutlined /> },
  abandoned: { label: i18n.t('foreshadows:descartada'), color: 'default', icon: <CloseCircleOutlined /> },
};

// 分类配置
const CATEGORY_CONFIG: Record<string, { label: string; color: string }> = {
  identity: { label: i18n.t('foreshadows:identidade'), color: 'purple' },
  mystery: { label: i18n.t('foreshadows:misterio'), color: 'magenta' },
  item: { label: i18n.t('foreshadows:objeto'), color: 'gold' },
  relationship: { label: i18n.t('foreshadows:relacao'), color: 'cyan' },
  event: { label: i18n.t('foreshadows:evento'), color: 'blue' },
  ability: { label: i18n.t('foreshadows:habilidade'), color: 'green' },
  prophecy: { label: i18n.t('foreshadows:profecia'), color: 'volcano' },
};

export default function Foreshadows() {
  const { t } = useTranslation('foreshadows');
  const { projectId } = useParams<{ projectId: string }>();
  const [loading, setLoading] = useState(false);
  const [foreshadows, setForeshadows] = useState<Foreshadow[]>([]);
  const [stats, setStats] = useState<ForeshadowStats | null>(null);
  const [chapters, setChapters] = useState<Chapter[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [total, setTotal] = useState(0);
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  
  // 筛选条件
  const [statusFilter, setStatusFilter] = useState<string | undefined>(undefined);
  const [categoryFilter, setCategoryFilter] = useState<string | undefined>(undefined);
  const [sourceFilter, setSourceFilter] = useState<string | undefined>(undefined);
  
  // 模态框状态
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [syncModalVisible, setSyncModalVisible] = useState(false);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [plantModalVisible, setPlantModalVisible] = useState(false);
  const [resolveModalVisible, setResolveModalVisible] = useState(false);
  
  const [currentForeshadow, setCurrentForeshadow] = useState<Foreshadow | null>(null);
  const [form] = Form.useForm();
  const [plantForm] = Form.useForm();
  const [resolveForm] = Form.useForm();
  const [syncing, setSyncing] = useState(false);
  
  // 表格容器引用，用于计算滚动高度
  const tableContainerRef = useRef<HTMLDivElement>(null);
  const [tableScrollY, setTableScrollY] = useState<number>(400);
  const { token } = theme.useToken();

  // 加载伏笔列表
  const loadForeshadows = useCallback(async () => {
    if (!projectId) return;
    
    setLoading(true);
    try {
      const response = await foreshadowApi.getProjectForeshadows(projectId, {
        status: statusFilter,
        category: categoryFilter,
        source_type: sourceFilter,
        page: currentPage,
        limit: pageSize,
      });
      
      setForeshadows(response.items);
      setTotal(response.total);
      if (response.stats) {
        setStats(response.stats);
      }
    } catch (error) {
      console.error(t('falhaCarregarPistas'), error);
    } finally {
      setLoading(false);
    }
  }, [projectId, statusFilter, categoryFilter, sourceFilter, currentPage, pageSize, t]);

  // 加载章节列表（用于选择）
  const loadChapters = useCallback(async () => {
    if (!projectId) return;
    try {
      const chaptersData = await chapterApi.getChapters(projectId);
      setChapters(chaptersData);
    } catch (error) {
      console.error(t('falhaCarregarCapitulos'), error);
    }
  }, [projectId, t]);

  // 加载角色列表（用于关联角色）
  const loadCharacters = useCallback(async () => {
    if (!projectId) return;
    try {
      const charactersData = await characterApi.getCharacters(projectId);
      setCharacters(charactersData);
    } catch (error) {
      console.error(t('falhaCarregarPersonagens'), error);
    }
  }, [projectId, t]);

  // 加载统计
  const loadStats = useCallback(async () => {
    if (!projectId) return;
    try {
      // 获取当前最大章节号（只计算有内容的章节，与表格显示逻辑保持一致）
      const chaptersWithContent = chapters.filter(c => c.content);
      const maxChapter = chaptersWithContent.length > 0
        ? Math.max(...chaptersWithContent.map(c => c.chapter_number))
        : undefined;
      const statsData = await foreshadowApi.getForeshadowStats(projectId, maxChapter);
      setStats(statsData);
    } catch (error) {
      console.error(t('falhaCarregarEstatisticas'), error);
    }
  }, [projectId, chapters, t]);

  useEffect(() => {
    loadForeshadows();
    loadChapters();
    loadCharacters();
  }, [loadForeshadows, loadChapters, loadCharacters]);

  useEffect(() => {
    const handleTaskSettled = (payload?: unknown) => {
      if (!payload || typeof payload !== 'object') return;
      const data = payload as { projectId?: string; resources?: string[] };
      if (data.projectId && data.projectId !== projectId) return;
      if (!data.resources?.includes('foreshadows')) return;
      void loadForeshadows();
      void loadStats();
    };
    eventBus.on(EventNames.BACKGROUND_TASK_SETTLED, handleTaskSettled);
    return () => eventBus.off(EventNames.BACKGROUND_TASK_SETTLED, handleTaskSettled);
  }, [loadForeshadows, loadStats, projectId]);

  // 计算表格滚动高度
  useEffect(() => {
    const calculateTableHeight = () => {
      if (tableContainerRef.current) {
        // 获取容器高度，减去表头高度（约55px）
        const containerHeight = tableContainerRef.current.clientHeight;
        setTableScrollY(Math.max(containerHeight - 55, 200));
      }
    };
    
    calculateTableHeight();
    window.addEventListener('resize', calculateTableHeight);
    
    // 延迟再计算一次，确保布局完成
    const timer = setTimeout(calculateTableHeight, 100);
    
    return () => {
      window.removeEventListener('resize', calculateTableHeight);
      clearTimeout(timer);
    };
  }, [stats]); // stats 变化时重新计算（因为统计卡片高度可能变化）

  useEffect(() => {
    if (chapters.length > 0) {
      loadStats();
    }
  }, [chapters, loadStats]);

  // 创建/编辑伏笔
  const handleSave = async (values: ForeshadowCreate | ForeshadowUpdate) => {
    try {
      if (currentForeshadow) {
        await foreshadowApi.updateForeshadow(currentForeshadow.id, values as ForeshadowUpdate);
        message.success(t('pistaAtualizadaSucesso'));
      } else {
        await foreshadowApi.createForeshadow({
          ...values,
          project_id: projectId!,
        } as ForeshadowCreate);
        message.success(t('pistaCriadaSucesso'));
      }
      setEditModalVisible(false);
      form.resetFields();
      setCurrentForeshadow(null);
      loadForeshadows();
    } catch (error) {
      console.error(t('falhaSalvarPista'), error);
    }
  };

  // 删除伏笔
  const handleDelete = async (id: string) => {
    try {
      await foreshadowApi.deleteForeshadow(id);
      message.success(t('pistaExcluidaSucesso'));
      loadForeshadows();
    } catch (error) {
      console.error(t('falhaExcluirPista'), error);
    }
  };

  // 标记埋入
  const handlePlant = async (values: { chapter_id: string; hint_text?: string }) => {
    if (!currentForeshadow) return;
    
    const chapter = chapters.find(c => c.id === values.chapter_id);
    if (!chapter) return;
    
    try {
      await foreshadowApi.plantForeshadow(currentForeshadow.id, {
        chapter_id: values.chapter_id,
        chapter_number: chapter.chapter_number,
        hint_text: values.hint_text,
      });
      message.success(t('pistaMarcadaComoPlantada'));
      setPlantModalVisible(false);
      plantForm.resetFields();
      setCurrentForeshadow(null);
      loadForeshadows();
    } catch (error) {
      console.error(t('falhaMarcarComoPlantada'), error);
    }
  };

  // 标记回收
  const handleResolve = async (values: { chapter_id: string; resolution_text?: string; is_partial?: boolean }) => {
    if (!currentForeshadow) return;
    
    const chapter = chapters.find(c => c.id === values.chapter_id);
    if (!chapter) return;
    
    try {
      await foreshadowApi.resolveForeshadow(currentForeshadow.id, {
        chapter_id: values.chapter_id,
        chapter_number: chapter.chapter_number,
        resolution_text: values.resolution_text,
        is_partial: values.is_partial,
      });
      message.success(t('pistaMarcadaComoResolvida'));
      setResolveModalVisible(false);
      resolveForm.resetFields();
      setCurrentForeshadow(null);
      loadForeshadows();
    } catch (error) {
      console.error(t('falhaMarcarComoResolvida'), error);
    }
  };

  // 标记废弃
  const handleAbandon = async (id: string) => {
    try {
      await foreshadowApi.abandonForeshadow(id);
      message.success(t('pistaMarcadaComoDescartada'));
      loadForeshadows();
    } catch (error) {
      console.error(t('falhaMarcarComoDescartada'), error);
    }
  };

  // 从分析同步
  const handleSync = async () => {
    if (!projectId) return;
    
    setSyncing(true);
    try {
      const result = await foreshadowApi.syncFromAnalysis(projectId, {
        auto_set_planted: true,
      });
      message.success(t('sincronizacaoConcluidaNovaS', { synced_count: result.synced_count, skipped_count: result.skipped_count }));
      setSyncModalVisible(false);
      loadForeshadows();
    } catch (error) {
      console.error(t('falhaSincronizacao'), error);
    } finally {
      setSyncing(false);
    }
  };

  // 打开编辑模态框
  const openEditModal = (foreshadow?: Foreshadow) => {
    setCurrentForeshadow(foreshadow || null);
    if (foreshadow) {
      // 确保数组类型字段不为null
      form.setFieldsValue({
        ...foreshadow,
        tags: foreshadow.tags || [],
        related_characters: foreshadow.related_characters || [],
      });
    } else {
      form.resetFields();
    }
    setEditModalVisible(true);
  };

  // 打开详情模态框
  const openDetailModal = (foreshadow: Foreshadow) => {
    setCurrentForeshadow(foreshadow);
    setDetailModalVisible(true);
  };

  // 打开埋入模态框
  const openPlantModal = (foreshadow: Foreshadow) => {
    setCurrentForeshadow(foreshadow);
    plantForm.resetFields();
    setPlantModalVisible(true);
  };

  // 打开回收模态框
  const openResolveModal = (foreshadow: Foreshadow) => {
    setCurrentForeshadow(foreshadow);
    resolveForm.resetFields();
    setResolveModalVisible(true);
  };

  // 计算紧急程度
  const getUrgencyBadge = (foreshadow: Foreshadow) => {
    if (foreshadow.status !== 'planted' || !foreshadow.target_resolve_chapter_number) {
      return null;
    }
    
    const chaptersWithContent = chapters.filter(c => c.content);
    const currentMaxChapter = chaptersWithContent.length > 0
      ? Math.max(...chaptersWithContent.map(c => c.chapter_number))
      : 0;
    
    const remaining = foreshadow.target_resolve_chapter_number - currentMaxChapter;
    
    if (remaining < 0) {
      return <Badge status="error" text={t('atrasadaCapituloS', { v0: Math.abs(remaining) })} />;
    } else if (remaining <= 3) {
      return <Badge status="warning" text={t('faltamCapituloS', { remaining })} />;
    }
    return null;
  };

  // 状态排序优先级
  const statusOrder: Record<ForeshadowStatus, number> = {
    planted: 1,      // 已埋入优先（需要关注回收）
    pending: 2,      // 待埋入次之
    partially_resolved: 3,
    resolved: 4,
    abandoned: 5,
  };

  // 表格列定义
  const columns = [
    {
      title: t('status'),
      dataIndex: 'status',
      key: 'status',
      width: 100,
      sorter: (a: Foreshadow, b: Foreshadow) => statusOrder[a.status] - statusOrder[b.status],
      render: (status: ForeshadowStatus) => {
        const config = STATUS_CONFIG[status];
        return (
          <Tag color={config.color} icon={config.icon}>
            {config.label}
          </Tag>
        );
      },
    },
    {
      title: t('titulo'),
      dataIndex: 'title',
      key: 'title',
      ellipsis: true,
      sorter: (a: Foreshadow, b: Foreshadow) => a.title.localeCompare(b.title, 'pt-BR'),
      render: (title: string, record: Foreshadow) => (
        <Space direction="vertical" size={0}>
          <Space>
            <a onClick={() => openDetailModal(record)}>{title}</a>
            {record.is_long_term && (
              <Tag color="purple" style={{ marginLeft: 4 }}>{t('longaDuracao')}</Tag>
            )}
          </Space>
          {getUrgencyBadge(record)}
        </Space>
      ),
    },
    {
      title: t('categoria'),
      dataIndex: 'category',
      key: 'category',
      width: 80,
      sorter: (a: Foreshadow, b: Foreshadow) => {
        const catA = a.category || '';
        const catB = b.category || '';
        return catA.localeCompare(catB, 'pt-BR');
      },
      render: (category?: ForeshadowCategory) => {
        if (!category) return '-';
        const config = CATEGORY_CONFIG[category];
        return config ? <Tag color={config.color}>{config.label}</Tag> : category;
      },
    },
    {
      title: t('capituloPlantio'),
      dataIndex: 'plant_chapter_number',
      key: 'plant_chapter_number',
      width: 120,
      sorter: (a: Foreshadow, b: Foreshadow) => {
        const valA = a.plant_chapter_number ?? 999999;
        const valB = b.plant_chapter_number ?? 999999;
        return valA - valB;
      },
      defaultSortOrder: 'ascend' as const,
      render: (num?: number) => num ? t('capitulo', { num }) : '-',
    },
    {
      title: t('resolucaoPrevista'),
      dataIndex: 'target_resolve_chapter_number',
      key: 'target_resolve_chapter_number',
      width: 120,
      sorter: (a: Foreshadow, b: Foreshadow) => {
        const valA = a.target_resolve_chapter_number ?? 999999;
        const valB = b.target_resolve_chapter_number ?? 999999;
        return valA - valB;
      },
      render: (num?: number) => num ? t('capitulo', { num }) : '-',
    },
    {
      title: t('importancia'),
      dataIndex: 'importance',
      key: 'importance',
      width: 100,
      sorter: (a: Foreshadow, b: Foreshadow) => a.importance - b.importance,
      render: (importance: number) => {
        const stars = Math.round(importance * 5);
        return '★'.repeat(stars) + '☆'.repeat(5 - stars);
      },
    },
    {
      title: t('origem'),
      dataIndex: 'source_type',
      key: 'source_type',
      width: 80,
      sorter: (a: Foreshadow, b: Foreshadow) => {
        const srcA = a.source_type || '';
        const srcB = b.source_type || '';
        return srcA.localeCompare(srcB);
      },
      render: (source?: string) => (
        <Tag color={source === 'analysis' ? 'blue' : 'green'}>
          {source === 'analysis' ? t('analise') : t('manual')}
        </Tag>
      ),
    },
    {
      title: t('acoes'),
      key: 'actions',
      width: 200,
      render: (_: unknown, record: Foreshadow) => (
        <Space size="small">
          <Tooltip title={t('verDetalhes')}>
            <Button type="text" size="small" icon={<EyeOutlined />} onClick={() => openDetailModal(record)} />
          </Tooltip>
          <Tooltip title={t('editar')}>
            <Button type="text" size="small" icon={<EditOutlined />} onClick={() => openEditModal(record)} />
          </Tooltip>
          {record.status === 'pending' && (
            <Tooltip title={t('marcarComoPlantada')}>
              <Button type="text" size="small" icon={<FlagOutlined />} onClick={() => openPlantModal(record)} />
            </Tooltip>
          )}
          {record.status === 'planted' && (
            <Tooltip title={t('marcarComoResolvida')}>
              <Button type="text" size="small" icon={<CheckCircleOutlined />} onClick={() => openResolveModal(record)} />
            </Tooltip>
          )}
          {record.status !== 'abandoned' && record.status !== 'resolved' && (
            <Popconfirm
              title={t('temCertezaDesejaDescartar')}
              onConfirm={() => handleAbandon(record.id)}
            >
              <Tooltip title={t('descartar')}>
                <Button type="text" size="small" danger icon={<CloseCircleOutlined />} />
              </Tooltip>
            </Popconfirm>
          )}
          <Popconfirm
            title={t('temCertezaDesejaExcluir')}
            onConfirm={() => handleDelete(record.id)}
          >
            <Tooltip title={t('excluir')}>
              <Button type="text" size="small" danger icon={<DeleteOutlined />} />
            </Tooltip>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
      {/* 统计卡片 */}
      {stats && (
        <Row gutter={16} style={{ marginBottom: 16 }}>
          <Col span={3}>
            <Card size="small">
              <Statistic title={t('total')} value={stats.total} />
            </Card>
          </Col>
          <Col span={3}>
            <Card size="small">
              <Statistic title={t('plantar')} value={stats.pending} valueStyle={{ color: token.colorTextSecondary }} />
            </Card>
          </Col>
          <Col span={3}>
            <Card size="small">
              <Statistic title={t('plantadas')} value={stats.planted} valueStyle={{ color: token.colorSuccess }} />
            </Card>
          </Col>
          <Col span={3}>
            <Card size="small">
              <Statistic title={t('resolvidas')} value={stats.resolved} valueStyle={{ color: token.colorPrimary }} />
            </Card>
          </Col>
          <Col span={3}>
            <Card size="small">
              <Statistic title={t('pistasLongaDuracao')} value={stats.long_term_count} valueStyle={{ color: token.colorInfo }} />
            </Card>
          </Col>
          <Col span={3}>
            <Card size="small">
              <Statistic 
                title={t('atrasadasSemResolucao')} 
                value={stats.overdue_count} 
                valueStyle={{ color: stats.overdue_count > 0 ? token.colorError : token.colorTextSecondary }}
                prefix={stats.overdue_count > 0 ? <WarningOutlined /> : null}
              />
            </Card>
          </Col>
        </Row>
      )}

      {/* 超期提醒 */}
      {stats && stats.overdue_count > 0 && (
        <Alert
          message={t('pistaSPassaramPrazo', { overdue_count: stats.overdue_count })}
          description={t('resolvaEssasPistasProximos')}
          type="warning"
          showIcon
          style={{ marginBottom: 16 }}
        />
      )}

      {/* 自动同步提示 */}
      <Alert
        message={
          <Space>
            <InfoCircleOutlined />
            <span>{t('pistasSaoSincronizadasAutomaticamente')}</span>
          </Space>
        }
        type="info"
        showIcon={false}
        style={{ marginBottom: 16 }}
        closable
      />

      {/* 工具栏 */}
      <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Space>
          <Select
            placeholder={t('filtrarStatus')}
            allowClear
            style={{ width: 120 }}
            value={statusFilter}
            onChange={setStatusFilter}
          >
            {Object.entries(STATUS_CONFIG).map(([key, config]) => (
              <Option key={key} value={key}>{config.label}</Option>
            ))}
          </Select>
          <Select
            placeholder={t('filtrarCategoria')}
            allowClear
            style={{ width: 100 }}
            value={categoryFilter}
            onChange={setCategoryFilter}
          >
            {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
              <Option key={key} value={key}>{config.label}</Option>
            ))}
          </Select>
          <Select
            placeholder={t('filtrarOrigem')}
            allowClear
            style={{ width: 100 }}
            value={sourceFilter}
            onChange={setSourceFilter}
          >
            <Option value="analysis">{t('analise')}</Option>
            <Option value="manual">{t('manual')}</Option>
          </Select>
        </Space>
        <Space>
          <Tooltip title={t('atualizarLista')}>
            <Button
              icon={<ReloadOutlined spin={loading} />}
              onClick={loadForeshadows}
            />
          </Tooltip>
          <Dropdown
            menu={{
              items: [
                {
                  key: 'sync',
                  icon: <SyncOutlined />,
                  label: t('sincronizarPistasAnaliseManualmente'),
                  onClick: () => setSyncModalVisible(true),
                },
              ] as MenuProps['items'],
            }}
            placement="bottomRight"
          >
            <Button icon={<MoreOutlined />}>{t('mais')}</Button>
          </Dropdown>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => openEditModal()}
          >
            {t('adicionarPista')}
          </Button>
        </Space>
      </div>

      {/* 伏笔列表 - 表格内容可滚动，表头固定 */}
      <div
        ref={tableContainerRef}
        style={{
          flex: 1,
          overflow: 'hidden',
          display: 'flex',
          flexDirection: 'column',
          minHeight: 0, // 重要：让 flex 子元素可以收缩
        }}
      >
        <Table
          dataSource={foreshadows}
          columns={columns}
          rowKey="id"
          loading={loading}
          pagination={false}
          scroll={{ y: tableScrollY }}
          locale={{
            emptyText: <Empty description={t('nenhumaPistaAindaClique')} />,
          }}
        />
      </div>

      {/* 分页器 - 固定在底部居中 */}
      <div style={{
        padding: '12px 0',
        borderTop: `1px solid ${token.colorBorderSecondary}`,
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        flexShrink: 0,
        background: token.colorBgContainer,
      }}>
        <Pagination
          current={currentPage}
          pageSize={pageSize}
          total={total}
          onChange={(page, size) => {
            setCurrentPage(page);
            if (size !== pageSize) {
              setPageSize(size);
            }
          }}
          showSizeChanger
          showTotal={(total) => t('totalContagem', { total })}
          showQuickJumper
        />
      </div>

      {/* 创建/编辑模态框 */}
      <Modal
        title={currentForeshadow ? t('editarPista') : t('adicionarPista')}
        open={editModalVisible}
        centered
        onCancel={() => {
          setEditModalVisible(false);
          setCurrentForeshadow(null);
          form.resetFields();
        }}
        onOk={() => form.submit()}
        width={800}
        destroyOnClose
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleSave}
          initialValues={{
            importance: 0.5,
            strength: 5,
            subtlety: 5,
            is_long_term: false,
            auto_remind: true,
            remind_before_chapters: 5,
            include_in_context: true,
          }}
        >
          <Row gutter={16}>
            <Col span={16}>
              <Form.Item name="title" label={t('tituloPista')} rules={[{ required: true, message: t('informeTitulo') }]}>
                <Input placeholder={t('descrevaBrevementePista')} maxLength={200} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="category" label={t('categoria')}>
                <Select placeholder={t('selecioneCategoria')} allowClear>
                  {Object.entries(CATEGORY_CONFIG).map(([key, config]) => (
                    <Option key={key} value={key}>{config.label}</Option>
                  ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Form.Item name="content" label={t('conteudoPista')} rules={[{ required: true, message: t('informeConteudo') }]}>
            <TextArea rows={3} placeholder={t('descrevaDetalhesConteudoIntencao')} />
          </Form.Item>
          
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="plant_chapter_number" label={t('plantioPrevisto')}>
                <InputNumber min={1} placeholder={t('nCapitulo')} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="target_resolve_chapter_number" label={t('resolucaoPrevista')}>
                <InputNumber min={1} placeholder={t('nCapitulo')} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="related_characters" label={t('personagensRelacionados')}>
                <Select
                  mode="multiple"
                  placeholder={t('selecionePersonagensRelacionados')}
                  optionFilterProp="children"
                  maxTagCount={3}
                >
                  {characters
                    .filter(char => !char.is_organization)
                    .map(char => (
                      <Option key={char.name} value={char.name}>
                        {char.name} {char.role_type ? `(${char.role_type})` : ''}
                      </Option>
                    ))}
                </Select>
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={6}>
              <Form.Item name="importance" label={t('importanciaEscala')}>
                <InputNumber min={0} max={1} step={0.1} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="strength" label={t('intensidadeEscala')}>
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="subtlety" label={t('sutilezaEscala')}>
                <InputNumber min={1} max={10} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={6}>
              <Form.Item name="is_long_term" label={t('pistaLongaDuracao')} valuePropName="checked">
                <Switch checkedChildren={t('sim')} unCheckedChildren={t('nao')} />
              </Form.Item>
            </Col>
          </Row>
          
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="hint_text" label={t('textoDica')}>
                <TextArea rows={2} placeholder={t('trechoSutilUsadoPlantar')} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="notes" label={t('observacoes')}>
                <TextArea rows={2} placeholder={t('observacoesEscritaVisiveisApenas')} />
              </Form.Item>
            </Col>
          </Row>
          
          <Divider style={{ margin: '12px 0' }}>{t('configuracoesApoioIa')}</Divider>
          
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item name="auto_remind" label={t('lembreteAutomatico')} valuePropName="checked" style={{ marginBottom: 0 }}>
                <Switch checkedChildren={t('ligado')} unCheckedChildren={t('desligado')} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="include_in_context" label={t('incluirContextoGeracao')} valuePropName="checked" style={{ marginBottom: 0 }}>
                <Switch checkedChildren={t('sim')} unCheckedChildren={t('nao')} />
              </Form.Item>
            </Col>
            <Col span={8}>
              <Form.Item name="remind_before_chapters" label={t('avisarQuantosCapitulosAntecedencia')} style={{ marginBottom: 0 }}>
                <InputNumber min={1} max={20} style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
        </Form>
      </Modal>

      {/* 详情模态框 */}
      <Modal
        title={t('detalhesPista')}
        open={detailModalVisible}
        centered
        onCancel={() => {
          setDetailModalVisible(false);
          setCurrentForeshadow(null);
        }}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            {t('fechar')}
          </Button>,
          <Button key="edit" type="primary" onClick={() => {
            setDetailModalVisible(false);
            openEditModal(currentForeshadow!);
          }}>
            {t('editar')}
          </Button>,
        ]}
        width={600}
      >
        {currentForeshadow && (
          <div>
            <Row gutter={[16, 16]}>
              <Col span={24}>
                <h3>{currentForeshadow.title}</h3>
                <Space>
                  <Tag color={STATUS_CONFIG[currentForeshadow.status].color}>
                    {STATUS_CONFIG[currentForeshadow.status].label}
                  </Tag>
                  {currentForeshadow.is_long_term && <Tag color="purple">{t('pistaLongaDuracao')}</Tag>}
                  {currentForeshadow.category && CATEGORY_CONFIG[currentForeshadow.category] && (
                    <Tag color={CATEGORY_CONFIG[currentForeshadow.category].color}>
                      {CATEGORY_CONFIG[currentForeshadow.category].label}
                    </Tag>
                  )}
                </Space>
              </Col>
              
              <Col span={24}>
                <strong>{t('conteudoPistaDetalhe')}</strong>
                <p style={{ marginTop: 8, whiteSpace: 'pre-wrap' }}>{currentForeshadow.content}</p>
              </Col>
              
              {currentForeshadow.hint_text && (
                <Col span={24}>
                  <strong>{t('textoDicaDetalhe')}</strong>
                  <p style={{ marginTop: 8, whiteSpace: 'pre-wrap', color: token.colorTextSecondary }}>
                    {currentForeshadow.hint_text}
                  </p>
                </Col>
              )}
              
              {currentForeshadow.resolution_text && (
                <Col span={24}>
                  <strong>{t('textoRevelacao')}</strong>
                  <p style={{ marginTop: 8, whiteSpace: 'pre-wrap', color: token.colorTextSecondary }}>
                    {currentForeshadow.resolution_text}
                  </p>
                </Col>
              )}
              
              <Col span={12}>
                <strong>{t('capituloPlantioDetalhe')}</strong> {currentForeshadow.plant_chapter_number ? t('capituloPlantioNumero', { plant_chapter_number: currentForeshadow.plant_chapter_number }) : t('naoDefinido')}
              </Col>
              <Col span={12}>
                <strong>{t('resolucaoPrevistaDetalhe')}</strong> {currentForeshadow.target_resolve_chapter_number ? t('capituloResolucaoPrevistaNumero', { target_resolve_chapter_number: currentForeshadow.target_resolve_chapter_number }) : t('naoDefinido')}
              </Col>
              
              {currentForeshadow.actual_resolve_chapter_number && (
                <Col span={24}>
                  <strong>{t('resolucaoEfetiva')}</strong> {t('capituloResolucaoEfetivaNumero', { actual_resolve_chapter_number: currentForeshadow.actual_resolve_chapter_number })}
                </Col>
              )}
              
              <Col span={8}>
                <strong>{t('importanciaDetalhe')}</strong> {'★'.repeat(Math.round(currentForeshadow.importance * 5))}
              </Col>
              <Col span={8}>
                <strong>{t('intensidade')}</strong> {currentForeshadow.strength}/10
              </Col>
              <Col span={8}>
                <strong>{t('sutileza')}</strong> {currentForeshadow.subtlety}/10
              </Col>
              
              {currentForeshadow.related_characters && currentForeshadow.related_characters.length > 0 && (
                <Col span={24}>
                  <strong>{t('personagensRelacionadosDetalhe')}</strong>
                  <div style={{ marginTop: 4 }}>
                    {currentForeshadow.related_characters.map((name, idx) => (
                      <Tag key={idx}>{name}</Tag>
                    ))}
                  </div>
                </Col>
              )}
              
              {currentForeshadow.notes && (
                <Col span={24}>
                  <strong>{t('observacoesDetalhe')}</strong>
                  <p style={{ marginTop: 8, color: token.colorTextSecondary }}>{currentForeshadow.notes}</p>
                </Col>
              )}
              
              <Col span={24}>
                <strong>{t('origemDetalhe')}</strong> {currentForeshadow.source_type === 'analysis' ? t('extraidaAnaliseCapitulo') : t('adicionadaManualmente')}
              </Col>
            </Row>
          </div>
        )}
      </Modal>

      {/* 标记埋入模态框 */}
      <Modal
        title={t('marcarPistaComoPlantada')}
        open={plantModalVisible}
        centered
        onCancel={() => {
          setPlantModalVisible(false);
          setCurrentForeshadow(null);
          plantForm.resetFields();
        }}
        onOk={() => plantForm.submit()}
        destroyOnClose
      >
        <Form form={plantForm} layout="vertical" onFinish={handlePlant}>
          <Form.Item name="chapter_id" label={t('selecioneCapituloPlantio')} rules={[{ required: true, message: t('selecioneCapitulo') }]}>
            <Select placeholder={t('selecioneCapituloPlaceholder')}>
              {chapters.map(chapter => (
                <Option key={chapter.id} value={chapter.id}>
                  {t('capituloComTitulo', { chapter_number: chapter.chapter_number, title: chapter.title })}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="hint_text" label={t('textoDicaOpcional')}>
            <TextArea rows={3} placeholder={t('registreTrechoSutilUsado')} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 标记回收模态框 */}
      <Modal
        title={t('marcarPistaComoResolvida')}
        open={resolveModalVisible}
        centered
        onCancel={() => {
          setResolveModalVisible(false);
          setCurrentForeshadow(null);
          resolveForm.resetFields();
        }}
        onOk={() => resolveForm.submit()}
        destroyOnClose
      >
        <Form form={resolveForm} layout="vertical" onFinish={handleResolve}>
          <Form.Item name="chapter_id" label={t('selecioneCapituloResolucao')} rules={[{ required: true, message: t('selecioneCapitulo') }]}>
            <Select placeholder={t('selecioneCapituloPlaceholder')}>
              {chapters.map(chapter => (
                <Option key={chapter.id} value={chapter.id}>
                  {t('capituloComTitulo', { chapter_number: chapter.chapter_number, title: chapter.title })}
                </Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="resolution_text" label={t('textoRevelacaoOpcional')}>
            <TextArea rows={3} placeholder={t('registreFoiReveladoResolver')} />
          </Form.Item>
          <Form.Item name="is_partial" label={t('resolucaoParcial')} valuePropName="checked">
            <Switch checkedChildren={t('parcial')} unCheckedChildren={t('completa')} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 同步模态框 */}
      <Modal
        title={t('sincronizarPistasAnaliseManualmente')}
        open={syncModalVisible}
        centered
        onCancel={() => setSyncModalVisible(false)}
        onOk={handleSync}
        confirmLoading={syncing}
        okText={t('iniciarSincronizacao')}
      >
        <Alert
          message={t('aviso')}
          description={t('normalmentePistasSaoSincronizadas')}
          type="info"
          showIcon
          style={{ marginBottom: 16 }}
        />
        <p>{t('operacaoExtraiInformacoesPistas')}</p>
        <ul>
          <li>{t('registrosPistasExistentesNao')}</li>
          <li>{t('pistasRecemSincronizadasReceberao')}</li>
          <li>{t('aposSincronizacaoVocePode')}</li>
        </ul>
      </Modal>
    </div>
  );
}

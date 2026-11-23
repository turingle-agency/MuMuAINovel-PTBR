import { useState, useEffect } from 'react';
import { Button, Table, Modal, Form, Input, Tag, Space, message, Popconfirm, Card, theme, Empty, Badge, Tooltip, Select } from 'antd';
import { PlusOutlined, EditOutlined, DeleteOutlined, ReloadOutlined, ThunderboltOutlined, FileTextOutlined } from '@ant-design/icons';
import { useTranslation } from 'react-i18next';

const { TextArea } = Input;

interface SkillItem {
  template_key: string;
  name: string;
  template_name: string;
  display_name: string;
  category: string;
  description: string;
  triggers: string[];
}

interface SkillDetail {
  template_key: string;
  name: string;
  template_name: string;
  display_name: string;
  category: string;
  description: string;
  triggers: string[];
  body: string;
  raw_content: string;
  standalone_references: Record<string, string>;
}

const SKILL_CATEGORY_OPTIONS = [
  { label: 'Skill · Romance longo', value: 'Skill · Romance longo' },
  { label: 'Skill · Conto', value: 'Skill · Conto' },
  { label: 'Skill · Revisão', value: 'Skill · Revisão' },
  { label: 'Skill · Ferramentas', value: 'Skill · Ferramentas' },
  { label: 'Skill', value: 'Skill' },
];

const parseTriggers = (value: string): string[] => (
  (value || '')
    .split(/[\n,;]+/)
    .map(item => item.trim())
    .filter(Boolean)
    .filter((item, index, array) => array.indexOf(item) === index)
);

const formatTriggers = (triggers: string[]) => (triggers || []).join('\n');

const normalizeCategory = (value: string | string[]) => (
  Array.isArray(value) ? (value[0] || '').trim() : (value || '').trim()
);

export default function SkillManage() {
  const { t } = useTranslation('skillManage');
  const { token } = theme.useToken();
  const [skills, setSkills] = useState<SkillItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [editModalVisible, setEditModalVisible] = useState(false);
  const [createModalVisible, setCreateModalVisible] = useState(false);
  const [editingSkill, setEditingSkill] = useState<SkillDetail | null>(null);
  const [editForm] = Form.useForm();
  const [createForm] = Form.useForm();
  const [saving, setSaving] = useState(false);
  const [viewModalVisible, setViewModalVisible] = useState(false);
  const [viewingContent, setViewingContent] = useState('');

  // 加载 Skill 列表
  const loadSkills = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/skills/list');
      if (response.ok) {
        const data = await response.json();
        setSkills(data);
      }
    } catch {
      message.error(t('falhaCarregarLista'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSkills();
  }, []);

  // 打开编辑弹窗
  const handleEdit = async (skill: SkillItem) => {
    try {
      const response = await fetch(`/api/skills/detail/${skill.template_key}`);
      if (response.ok) {
        const detail: SkillDetail = await response.json();
        setEditingSkill(detail);
        editForm.setFieldsValue({
          name: detail.name,
          display_name: detail.display_name || detail.template_name,
          category: detail.category,
          description: detail.description,
          triggers: formatTriggers(detail.triggers),
          body: detail.body,
          references: JSON.stringify(detail.standalone_references, null, 2),
        });
        setEditModalVisible(true);
      } else {
        message.error(t('falhaObterDetalhes'));
      }
    } catch {
      message.error(t('falhaObterDetalhes'));
    }
  };

  // 打开查看原始内容弹窗
  const handleViewRaw = async (skill: SkillItem) => {
    try {
      const response = await fetch(`/api/skills/detail/${skill.template_key}`);
      if (response.ok) {
        const detail: SkillDetail = await response.json();
        setViewingContent(detail.raw_content);
        setViewModalVisible(true);
      }
    } catch {
      message.error(t('falhaObterConteudo'));
    }
  };

  // 保存编辑
  const handleSaveEdit = async () => {
    if (!editingSkill) return;
    const values = await editForm.validateFields();
    setSaving(true);
    try {
      // 解析 references JSON
      let refs: Record<string, string> | undefined;
      if (values.references?.trim()) {
        try {
          refs = JSON.parse(values.references);
        } catch {
          message.error(t('jsonMateriaisReferencia'));
          setSaving(false);
          return;
        }
      }

      const triggers = parseTriggers(values.triggers);
      if (triggers.length === 0) {
        message.error(t('informePeloMenos'));
        setSaving(false);
        return;
      }
      const category = normalizeCategory(values.category);
      if (!category) {
        message.error(t('selecioneOuInforme'));
        setSaving(false);
        return;
      }

      const response = await fetch(`/api/skills/update/${editingSkill.template_key}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          display_name: values.display_name,
          category,
          description: values.description,
          triggers,
          body: values.body,
          references: refs,
        }),
      });

      if (response.ok) {
        message.success(t('skillAtualizadaSucesso'));
        setEditModalVisible(false);
        loadSkills();
      } else {
        const err = await response.json();
        message.error(err.detail || t('falhaAoAtualizar'));
      }
    } catch {
      message.error(t('falhaAoSalvar'));
    } finally {
      setSaving(false);
    }
  };

  // 创建新 Skill
  const handleCreate = async () => {
    const values = await createForm.validateFields();
    setSaving(true);
    try {
      let refs: Record<string, string> | undefined;
      if (values.references?.trim()) {
        try {
          refs = JSON.parse(values.references);
        } catch {
          message.error(t('jsonMateriaisReferencia'));
          setSaving(false);
          return;
        }
      }

      const triggers = parseTriggers(values.triggers);
      if (triggers.length === 0) {
        message.error(t('informePeloMenos'));
        setSaving(false);
        return;
      }
      const category = normalizeCategory(values.category);
      if (!category) {
        message.error(t('selecioneOuInforme'));
        setSaving(false);
        return;
      }

      const response = await fetch('/api/skills/create', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          name: values.name,
          display_name: values.display_name,
          category,
          description: values.description,
          triggers,
          body: values.body,
          references: refs,
        }),
      });

      if (response.ok) {
        message.success(t('skillCriadaSucesso'));
        setCreateModalVisible(false);
        createForm.resetFields();
        loadSkills();
      } else {
        const err = await response.json();
        message.error(err.detail || t('falhaAoCriar'));
      }
    } catch {
      message.error(t('falhaAoCriar'));
    } finally {
      setSaving(false);
    }
  };

  // 删除 Skill
  const handleDelete = async (skillKey: string) => {
    try {
      const response = await fetch(`/api/skills/delete/${skillKey}`, { method: 'DELETE' });
      if (response.ok) {
        message.success(t('excluidaComSucesso'));
        loadSkills();
      } else {
        const err = await response.json();
        message.error(err.detail || t('falhaAoExcluir'));
      }
    } catch {
      message.error(t('falhaAoExcluir'));
    }
  };

  const columns = [
    {
      title: t('nome'),
      dataIndex: 'display_name',
      key: 'display_name',
      width: 220,
      ellipsis: true,
      render: (text: string, record: SkillItem) => (
        <div style={{ minWidth: 0 }}>
          <Tooltip title={text}>
            <strong style={{ display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{text}</strong>
          </Tooltip>
          <Tooltip title={record.name || record.template_key}>
            <span style={{ display: 'block', marginTop: 2, color: token.colorTextTertiary, fontSize: 11, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {record.name || record.template_key}
            </span>
          </Tooltip>
        </div>
      ),
    },
    {
      title: t('categoria'),
      dataIndex: 'category',
      key: 'category',
      width: 120,
      render: (cat: string) => {
        const colorMap: Record<string, string> = {
          'Skill · Romance longo': 'blue',
          'Skill · Conto': 'green',
          'Skill · Revisão': 'orange',
          'Skill · Ferramentas': 'purple',
          'Skill': 'default',
        };
        return <Tag color={colorMap[cat] || 'default'}>{cat}</Tag>;
      },
    },
    {
      title: t('descricao'),
      dataIndex: 'description',
      key: 'description',
      width: 260,
      ellipsis: true,
      render: (text: string) => (
        <Tooltip title={text}>
          <span
            style={{
              display: 'block',
              maxWidth: 240,
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
              color: token.colorTextSecondary,
              fontSize: 13,
            }}
          >
            {text}
          </span>
        </Tooltip>
      ),
    },
    {
      title: t('gatilhos'),
      dataIndex: 'triggers',
      key: 'triggers',
      width: 180,
      render: (triggers: string[]) => (
        <Space wrap size={4}>
          {triggers.slice(0, 3).map((t, i) => (
            <Tag key={i} style={{ fontSize: 11 }}>{t}</Tag>
          ))}
          {triggers.length > 3 && <Tag>+{triggers.length - 3}</Tag>}
        </Space>
      ),
    },
    {
      title: t('acoes'),
      key: 'actions',
      width: 200,
      render: (_: unknown, record: SkillItem) => (
        <Space>
          <Button
            type="text"
            icon={<FileTextOutlined />}
            onClick={() => handleViewRaw(record)}
            size="small"
          >
            {t('ver')}
          </Button>
          <Button
            type="text"
            icon={<EditOutlined />}
            onClick={() => handleEdit(record)}
            size="small"
          >
            {t('editar')}
          </Button>
          <Popconfirm
            title={t('excluirEstaSkill')}
            description={t('aposExclusaoNao')}
            onConfirm={() => handleDelete(record.template_key)}
            okText={t('excluir')}
            cancelText={t('cancelar')}
            okButtonProps={{ danger: true }}
          >
            <Button type="text" danger icon={<DeleteOutlined />} size="small">
              {t('excluir')}
            </Button>
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* 顶部标题栏 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: 16,
        flexWrap: 'wrap',
        gap: 12,
      }}>
        <div>
          <h2 style={{ margin: 0, fontSize: 20 }}>
            <ThunderboltOutlined style={{ marginRight: 8, color: token.colorPrimary }} />
            {t('gerenciamentoDeSkills')}
            <Badge count={skills.length} style={{ marginLeft: 8, backgroundColor: token.colorPrimary }} />
          </h2>
          <div style={{ fontSize: 12, color: token.colorTextSecondary, marginTop: 4 }}>
            {t('gerencieOnlineFluxos')}
          </div>
        </div>
        <Space wrap>
          <Button
            icon={<ReloadOutlined />}
            onClick={loadSkills}
            loading={loading}
          >
            {t('atualizar')}
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              createForm.resetFields();
              setCreateModalVisible(true);
            }}
          >
            {t('adicionarSkill')}
          </Button>
        </Space>
      </div>

      {/* Skill 列表 */}
      {skills.length === 0 && !loading ? (
        <Card>
          <Empty description={t('nenhumaSkillClique')}>
            <Button type="primary" icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>
              {t('adicionarSkill')}
            </Button>
          </Empty>
        </Card>
      ) : (
        <div style={{ flex: 1, overflowY: 'auto' }}>
          <Table
            dataSource={skills}
            columns={columns}
            rowKey="template_key"
            loading={loading}
            pagination={false}
            size="middle"
            style={{ background: token.colorBgContainer }}
          />
        </div>
      )}

      {/* 查看原始内容弹窗 */}
      <Modal
        title={t('conteudoOriginalSkill')}
        open={viewModalVisible}
        onCancel={() => setViewModalVisible(false)}
        width={800}
        footer={<Button onClick={() => setViewModalVisible(false)}>{t('fechar')}</Button>}
        styles={{ body: { maxHeight: '60vh', overflowY: 'auto' } }}
      >
        <pre style={{
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
          fontSize: 13,
          lineHeight: 1.6,
          background: token.colorFillQuaternary,
          padding: 16,
          borderRadius: 8,
        }}>
          {viewingContent}
        </pre>
      </Modal>

      {/* 编辑 Skill 弹窗 */}
      <Modal
        title={t('editarSkill')}
        open={editModalVisible}
        onCancel={() => setEditModalVisible(false)}
        width={900}
        footer={
          <Space>
            <Button onClick={() => setEditModalVisible(false)}>{t('cancelar')}</Button>
            <Button type="primary" onClick={handleSaveEdit} loading={saving}>{t('salvar')}</Button>
          </Space>
        }
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
        destroyOnClose
      >
        <Form form={editForm} layout="vertical">
          <Form.Item label={t('identificadorInterno')} name="name" tooltip={t('campoNameSkill')}>
            <Input disabled />
          </Form.Item>
          <Form.Item label={t('nomeDeExibicao')} name="display_name" rules={[{ required: true, whitespace: true, message: t('informeNomeExibicao') }]}
            tooltip={t('nomeMostradoTabela')}>
            <Input placeholder={t('exDesmontagemRomances')} maxLength={60} />
          </Form.Item>
          <Form.Item label={t('categoria')} name="category" rules={[{ required: true, message: t('selecioneACategoria') }]}
            tooltip={t('categoriaSkillMostrada')}>
            <Select
              showSearch
              options={SKILL_CATEGORY_OPTIONS}
              placeholder={t('selecioneOuInforme')}
              mode="tags"
              maxCount={1}
              tokenSeparators={[',', ';']}
            />
          </Form.Item>
          <Form.Item label={t('descricao')} name="description" rules={[{ required: true, whitespace: true, message: t('informeADescricao') }]}
            tooltip={t('explicaFinalidadeSkill')}>
            <TextArea rows={4} placeholder={t('descrevaBrevementeFuncao')} />
          </Form.Item>
          <Form.Item label={t('gatilhos')} name="triggers" rules={[{ required: true, whitespace: true, message: t('informePeloMenos') }]}
            tooltip={t('linhaTambemAceita')}>
            <TextArea rows={4} placeholder={t('storyLongAnalyze')} />
          </Form.Item>
          <Form.Item label={t('instrucoesFluxoTrabalho')} name="body" rules={[{ required: true, message: t('informeInstrucoesFluxo') }]}
            tooltip={t('corpoMarkdownApos')}>
            <TextArea rows={15} placeholder={t('informeInstrucoesCompletas')} style={{ fontFamily: 'monospace', fontSize: 13 }} />
          </Form.Item>
          <Form.Item label={t('materiaisReferenciaJson')} name="references"
            tooltip={t('formatoNomeArquivo')}>
            <TextArea rows={8} placeholder={t('antiAiTips')} style={{ fontFamily: 'monospace', fontSize: 12 }} />
          </Form.Item>
        </Form>
      </Modal>

      {/* 创建 Skill 弹窗 */}
      <Modal
        title={t('adicionarNovaSkill')}
        open={createModalVisible}
        onCancel={() => setCreateModalVisible(false)}
        width={900}
        footer={
          <Space>
            <Button onClick={() => setCreateModalVisible(false)}>{t('cancelar')}</Button>
            <Button type="primary" onClick={handleCreate} loading={saving}>{t('criar')}</Button>
          </Space>
        }
        styles={{ body: { maxHeight: '70vh', overflowY: 'auto' } }}
        destroyOnClose
      >
        <Form form={createForm} layout="vertical">
          <Form.Item label={t('nomeSkillIngles')} name="name" rules={[{ required: true, message: t('informeONome') }]}
            tooltip={t('minusculasInglesHifens')}>
            <Input placeholder="my-new-skill" />
          </Form.Item>
          <Form.Item label={t('nomeDeExibicao')} name="display_name" rules={[{ required: true, whitespace: true, message: t('informeNomeExibicao') }]}
            tooltip={t('nomeMostradoTabela')}>
            <Input placeholder={t('exMinhaNova')} maxLength={60} />
          </Form.Item>
          <Form.Item label={t('categoria')} name="category" rules={[{ required: true, message: t('selecioneACategoria') }]}
            tooltip={t('categoriaSkillMostrada')}>
            <Select
              showSearch
              options={SKILL_CATEGORY_OPTIONS}
              placeholder={t('selecioneOuInforme')}
              mode="tags"
              maxCount={1}
              tokenSeparators={[',', ';']}
            />
          </Form.Item>
          <Form.Item label={t('descricao')} name="description" rules={[{ required: true, whitespace: true, message: t('informeADescricao') }]}
            tooltip={t('explicaFinalidadeSkill')}>
            <TextArea rows={4} placeholder={t('descrevaBrevementeFuncao')} />
          </Form.Item>
          <Form.Item label={t('gatilhos')} name="triggers" rules={[{ required: true, whitespace: true, message: t('informePeloMenos') }]}
            tooltip={t('linhaTambemAceita')}>
            <TextArea rows={4} placeholder={t('myNewSkill')} />
          </Form.Item>
          <Form.Item label={t('instrucoesFluxoTrabalho')} name="body" rules={[{ required: true, message: t('informeInstrucoesFluxo') }]}
            tooltip={t('conteudoMarkdownPrincipal')}>
            <TextArea rows={15} placeholder={t('myNewSkillTitulo')} style={{ fontFamily: 'monospace', fontSize: 13 }} />
          </Form.Item>
          <Form.Item label={t('materiaisReferenciaJsonOpcional')} name="references"
            tooltip={t('formatoNomeArquivoConteudo')}>
            <TextArea rows={8} placeholder={t('tipsTecnicasReferencia')} style={{ fontFamily: 'monospace', fontSize: 12 }} />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

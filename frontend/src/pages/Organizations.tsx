import { useState, useEffect, useCallback } from 'react';
import { useParams } from 'react-router-dom';
import { Card, Table, Tag, Button, Space, message, Modal, Form, Select, InputNumber, Input, Descriptions, Drawer, theme } from 'antd';
import { PlusOutlined, UserOutlined, EditOutlined, DeleteOutlined, UnorderedListOutlined, BankOutlined } from '@ant-design/icons';
import { useStore } from '../store';
import { useCharacterSync } from '../store/hooks';
import axios from 'axios';
import { eventBus, EventNames } from '../store/eventBus';
import { useTranslation } from 'react-i18next';

interface Organization {
  id: string;
  character_id: string;
  name: string;
  type: string;
  purpose: string;
  member_count: number;
  power_level: number;
  location?: string;
  motto?: string;
  color?: string;
}

interface OrganizationMember {
  id: string;
  character_id: string;
  character_name: string;
  position: string;
  rank: number;
  loyalty: number;
  contribution: number;
  status: string;
  joined_at?: string;
  left_at?: string;
  notes?: string;
}

interface Character {
  id: string;
  name: string;
  is_organization: boolean;
}

export default function Organizations() {
  const { t } = useTranslation('organizations');
  const { projectId } = useParams<{ projectId: string }>();
  const { currentProject } = useStore();
  const { refreshCharacters } = useCharacterSync();
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [selectedOrg, setSelectedOrg] = useState<Organization | null>(null);
  const [members, setMembers] = useState<OrganizationMember[]>([]);
  const [characters, setCharacters] = useState<Character[]>([]);
  const [loading, setLoading] = useState(false);
  const [isAddMemberModalOpen, setIsAddMemberModalOpen] = useState(false);
  const [isEditMemberModalOpen, setIsEditMemberModalOpen] = useState(false);
  const [isEditOrgModalOpen, setIsEditOrgModalOpen] = useState(false);
  const [editingMember, setEditingMember] = useState<OrganizationMember | null>(null);
  const [form] = Form.useForm();
  const [editMemberForm] = Form.useForm();
  const [editOrgForm] = Form.useForm();
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [modal, contextHolder] = Modal.useModal();
  const [orgListVisible, setOrgListVisible] = useState(false);
  const { token } = theme.useToken();

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };

    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const loadOrganizations = useCallback(async () => {
    setLoading(true);
    try {
      const res = await axios.get(`/api/organizations/project/${projectId}`);
      setOrganizations(res.data);
      if (res.data.length > 0 && !selectedOrg) {
        setSelectedOrg(res.data[0]);
        loadMembers(res.data[0].id);
      }
    } catch (error) {
      message.error(t('falhaCarregarLista'));
      console.error(error);
    } finally {
      setLoading(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  const loadCharacters = useCallback(async () => {
    try {
      const res = await axios.get(`/api/characters?project_id=${projectId}`);
      setCharacters(res.data.items || []);
    } catch (error) {
      console.error('Falha ao carregar a lista de personagens:', error);
    }
  }, [projectId]);

  useEffect(() => {
    if (projectId) {
      loadOrganizations();
      loadCharacters();
    }
  }, [projectId, loadOrganizations, loadCharacters]);

  useEffect(() => {
    const handleTaskSettled = (payload?: unknown) => {
      if (!payload || typeof payload !== 'object') return;
      const data = payload as { projectId?: string; resources?: string[] };
      if (data.projectId && data.projectId !== projectId) return;
      if (!data.resources?.includes('organizations')) return;
      void loadOrganizations();
      void loadCharacters();
      if (selectedOrg?.id) void loadMembers(selectedOrg.id);
    };
    eventBus.on(EventNames.BACKGROUND_TASK_SETTLED, handleTaskSettled);
    return () => eventBus.off(EventNames.BACKGROUND_TASK_SETTLED, handleTaskSettled);
  }, [loadCharacters, loadOrganizations, projectId, selectedOrg?.id]);

  const loadMembers = async (orgId: string) => {
    try {
      const res = await axios.get(`/api/organizations/${orgId}/members`);
      setMembers(res.data);
    } catch (error) {
      message.error(t('falhaCarregarListaMembros'));
      console.error(error);
    }
  };

  const handleSelectOrganization = (org: Organization) => {
    setSelectedOrg(org);
    loadMembers(org.id);
  };

  const handleAddMember = async (values: Record<string, unknown>) => {
    if (!selectedOrg) return;

    try {
      await axios.post(`/api/organizations/${selectedOrg.id}/members`, values);
      message.success(t('membroAdicionadoSucesso'));
      setIsAddMemberModalOpen(false);
      form.resetFields();
      loadMembers(selectedOrg.id);
      loadOrganizations(); // 刷新成员计数
    } catch (error) {
      message.error(t('falhaAdicionarMembro'));
      console.error(error);
    }
  };

  const handleRemoveMember = async (memberId: string) => {
    modal.confirm({
      title: t('confirmarRemocao'),
      content: t('temCertezaDeseja'),
      centered: true,
      okText: t('remover'),
      okType: 'danger',
      cancelText: t('cancelar'),
      onOk: async () => {
        try {
          await axios.delete(`/api/organizations/members/${memberId}`);
          message.success(t('membroRemovidoSucesso'));
          if (selectedOrg) {
            loadMembers(selectedOrg.id);
            loadOrganizations(); // 刷新成员计数
          }
        } catch (error) {
          message.error(t('falhaAoRemover'));
          console.error(error);
        }
      }
    });
  };

  const handleEditMember = (member: OrganizationMember) => {
    setEditingMember(member);
    editMemberForm.setFieldsValue({
      position: member.position,
      rank: member.rank,
      loyalty: member.loyalty,
      contribution: member.contribution,
      status: member.status,
      notes: member.notes,
      joined_at: member.joined_at
    });
    setIsEditMemberModalOpen(true);
  };

  const handleUpdateMember = async (values: Record<string, unknown>) => {
    if (!editingMember) return;

    try {
      await axios.put(`/api/organizations/members/${editingMember.id}`, values);
      message.success(t('informacoesMembroAtualizadas'));
      setIsEditMemberModalOpen(false);
      editMemberForm.resetFields();
      setEditingMember(null);
      if (selectedOrg) {
        loadMembers(selectedOrg.id);
      }
    } catch (error) {
      message.error(t('falhaAoAtualizar'));
      console.error(error);
    }
  };

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      active: 'green',
      retired: 'default',
      expelled: 'red',
      deceased: 'black'
    };
    return colors[status] || 'default';
  };

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      active: t('ativo'),
      retired: t('aposentado'),
      expelled: t('expulso'),
      deceased: t('falecido')
    };
    return texts[status] || status;
  };

  const memberColumns = [
    {
      title: t('nome'),
      dataIndex: 'character_name',
      key: 'name',
      render: (name: string) => (
        <Space>
          <UserOutlined />
          <span>{name}</span>
        </Space>
      ),
      width: isMobile ? 100 : undefined,
    },
    {
      title: t('cargo'),
      dataIndex: 'position',
      key: 'position',
      render: (position: string, record: OrganizationMember) => (
        <Tag color="blue">{position} {!isMobile && t('nivel', { rank: record.rank })}</Tag>
      ),
      width: isMobile ? 120 : undefined,
    },
    {
      title: t('lealdade'),
      dataIndex: 'loyalty',
      key: 'loyalty',
      render: (loyalty: number) => (
        <span style={{ color: loyalty >= 70 ? 'green' : loyalty >= 40 ? 'orange' : 'red' }}>
          {loyalty}%
        </span>
      ),
      width: isMobile ? 80 : undefined,
    },
    {
      title: t('contribuicao'),
      dataIndex: 'contribution',
      key: 'contribution',
      render: (contribution: number) => `${contribution}%`,
      width: isMobile ? 80 : undefined,
    },
    {
      title: t('status'),
      dataIndex: 'status',
      key: 'status',
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
      width: isMobile ? 80 : undefined,
    },
    {
      title: t('dataDeEntrada'),
      dataIndex: 'joined_at',
      key: 'joined_at',
      render: (time: string) => time || '-',
      width: isMobile ? 120 : undefined,
    },
    {
      title: t('acoes'),
      key: 'action',
      render: (_: unknown, record: OrganizationMember) => (
        <Space size={isMobile ? 0 : 'small'}>
          <Button
            type="link"
            size="small"
            icon={<EditOutlined />}
            onClick={() => handleEditMember(record)}
            style={isMobile ? { padding: '4px' } : undefined}
          >
            {isMobile ? '' : t('editar')}
          </Button>
          <Button
            type="link"
            danger
            size="small"
            icon={<DeleteOutlined />}
            onClick={() => handleRemoveMember(record.id)}
            style={isMobile ? { padding: '4px' } : undefined}
          >
            {isMobile ? '' : t('remover')}
          </Button>
        </Space>
      ),
      width: isMobile ? 50 : undefined,
      fixed: isMobile ? 'right' as const : undefined,
    },
  ];

  // 过滤掉已是成员的角色
  const availableCharacters = characters.filter(
    c => !c.is_organization && !members.some(m => m.character_id === c.id)
  );

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {contextHolder}
      
      {/* 页面标题 - 仅桌面端显示 */}
      {!isMobile && (
        <div style={{
          padding: '16px 0',
          marginBottom: 16,
          borderBottom: `1px solid ${token.colorBorderSecondary}`
        }}>
          <h2 style={{ margin: 0, fontSize: 24 }}>
            <BankOutlined style={{ marginRight: 8 }} />
            {t('gerenciamentoDeOrganizacoes')}
          </h2>
        </div>
      )}
      
      <div style={{
        flex: 1,
        display: 'flex',
        gap: isMobile ? 0 : 16,
        flexDirection: isMobile ? 'column' : 'row',
        overflow: 'hidden'
      }}>
        {/* 左侧组织列表 - 桌面端 */}
        {!isMobile && (
        <Card
          title={t('listaDeOrganizacoes', { organizationsCount: organizations.length })}
          style={{ width: 300, height: '100%', overflow: 'hidden' }}
          bodyStyle={{ padding: 0, height: 'calc(100% - 57px)', overflow: 'auto' }}
          loading={loading}
        >
          {organizations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: token.colorTextTertiary }}>
              {t('nenhumaOrganizacao')}
            </div>
          ) : (
            <Space direction="vertical" style={{ width: '100%', padding: '12px' }}>
              {organizations.map(org => (
                <Card
                  key={org.id}
                  size="small"
                  hoverable
                  style={{
                    cursor: 'pointer',
                    border: selectedOrg?.id === org.id ? `2px solid ${token.colorPrimary}` : `1px solid ${token.colorBorder}`,
                    background: selectedOrg?.id === org.id ? token.colorPrimaryBg : 'transparent'
                  }}
                  onClick={() => handleSelectOrganization(org)}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <strong style={{ fontSize: 14 }}>{org.name}</strong>
                    <Tag color="blue">{org.type}</Tag>
                    <div style={{ fontSize: '12px', color: token.colorTextSecondary }}>
                      {t('membrosPoder', { member_count: org.member_count, power_level: org.power_level })}
                    </div>
                  </Space>
                </Card>
              ))}
            </Space>
          )}
        </Card>
        )}

        {/* 移动端组织列表抽屉 */}
      {isMobile && (
        <Drawer
          title={t('listaDeOrganizacoes2')}
          placement="left"
          onClose={() => setOrgListVisible(false)}
          open={orgListVisible}
          width="85%"
          styles={{ body: { padding: 0 } }}
        >
          {organizations.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 20px', color: token.colorTextTertiary }}>
              {t('nenhumaOrganizacao')}
            </div>
          ) : (
            <Space direction="vertical" style={{ width: '100%', padding: '12px' }}>
              {organizations.map(org => (
                <Card
                  key={org.id}
                  size="small"
                  hoverable
                  style={{
                    cursor: 'pointer',
                    border: selectedOrg?.id === org.id ? `2px solid ${token.colorPrimary}` : `1px solid ${token.colorBorder}`,
                    background: selectedOrg?.id === org.id ? token.colorPrimaryBg : 'transparent'
                  }}
                  onClick={() => {
                    handleSelectOrganization(org);
                    setOrgListVisible(false);
                  }}
                >
                  <Space direction="vertical" size="small" style={{ width: '100%' }}>
                    <strong style={{ fontSize: 14 }}>{org.name}</strong>
                    <Tag color="blue">{org.type}</Tag>
                    <div style={{ fontSize: '12px', color: token.colorTextSecondary }}>
                      {t('membrosPoder', { member_count: org.member_count, power_level: org.power_level })}
                    </div>
                  </Space>
                </Card>
              ))}
            </Space>
          )}
        </Drawer>
        )}

        {/* 右侧内容区域 */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', height: '100%', overflow: 'hidden' }}>
        {!selectedOrg ? (
          <Card style={{ height: '100%' }}>
            <div style={{ textAlign: 'center', padding: '100px 20px', color: token.colorTextTertiary }}>
              {isMobile && organizations.length > 0 && (
                <Button
                  type="primary"
                  icon={<UnorderedListOutlined />}
                  onClick={() => setOrgListVisible(true)}
                  style={{ marginBottom: 20 }}
                >
                  {t('selecioneUmaOrganizacao')}
                </Button>
              )}
              <div>{t('selecioneOrganizacaoVer')}</div>
            </div>
          </Card>
        ) : (
          <>
            {/* 工具栏 - 移动端显示项目标题和组织列表按钮 */}
            {isMobile && (
              <Card size="small" style={{ marginBottom: 8 }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <Space>
                    <BankOutlined />
                    <span style={{ fontSize: 14, fontWeight: 600 }}>
                      {t('gerenciamentoDeOrganizacoes')}
                    </span>
                    <Tag color="blue">{currentProject?.title}</Tag>
                  </Space>
                  <Button
                    icon={<UnorderedListOutlined />}
                    onClick={() => setOrgListVisible(true)}
                    size="small"
                  >
                    {t('lista')}
                  </Button>
                </div>
              </Card>
            )}

            {/* 内容区域 */}
            <div style={{
              flex: 1,
              display: 'flex',
              gap: isMobile ? 0 : 16,
              overflow: 'hidden'
            }}>
              <Card
                style={{ flex: 1, overflow: 'auto' }}
                bodyStyle={{ padding: isMobile ? '12px' : '24px' }}
              >
                <Space direction="vertical" style={{ width: '100%' }} size={isMobile ? 'middle' : 'large'}>
                <Card
                  title={t('detalhesDaOrganizacao')}
                  size="small"
                  extra={
                    <Button
                      type="link"
                      size="small"
                      icon={<EditOutlined />}
                      onClick={() => {
                        editOrgForm.setFieldsValue({
                          power_level: selectedOrg.power_level,
                          location: selectedOrg.location,
                          motto: selectedOrg.motto,
                          color: selectedOrg.color
                        });
                        setIsEditOrgModalOpen(true);
                      }}
                    >
                      {t('editar')}
                    </Button>
                  }
                >
                  <Descriptions column={isMobile ? 1 : 2} size="small">
                    <Descriptions.Item label={t('nomeDaOrganizacao')}>{selectedOrg.name}</Descriptions.Item>
                    <Descriptions.Item label={t('tipo')}>{selectedOrg.type}</Descriptions.Item>
                    <Descriptions.Item label={t('numeroDeMembros')}>{selectedOrg.member_count}</Descriptions.Item>
                    <Descriptions.Item label={t('nivelDePoder')}>
                      <Tag color={selectedOrg.power_level >= 70 ? 'red' : selectedOrg.power_level >= 50 ? 'orange' : 'default'}>
                        {selectedOrg.power_level}
                      </Tag>
                    </Descriptions.Item>
                    {selectedOrg.location && (
                      <Descriptions.Item label={t('localizacao')} span={isMobile ? 1 : 2}>
                        {selectedOrg.location}
                      </Descriptions.Item>
                    )}
                    {selectedOrg.color && (
                      <Descriptions.Item label={t('corRepresentativa')}>
                        {selectedOrg.color}
                      </Descriptions.Item>
                    )}
                    {selectedOrg.motto && (
                      <Descriptions.Item label={t('lemaSlogan')} span={2}>
                        {selectedOrg.motto}
                      </Descriptions.Item>
                    )}
                    <Descriptions.Item label={t('propositoDaOrganizacao')} span={2}>
                      {selectedOrg.purpose}
                    </Descriptions.Item>
                  </Descriptions>
                </Card>

                <Card
                  title={t('membrosDaOrganizacao', { membersCount: members.length })}
                  extra={
                    <Button
                      type="primary"
                      size="small"
                      icon={<PlusOutlined />}
                      onClick={() => setIsAddMemberModalOpen(true)}
                      disabled={availableCharacters.length === 0}
                    >
                      {t('adicionarMembro')}
                    </Button>
                  }
                >
                  <Table
                    columns={memberColumns}
                    dataSource={members}
                    rowKey="id"
                    pagination={
                      members.length > 5
                        ? {
                          defaultPageSize: 5,
                          showSizeChanger: true,
                          showQuickJumper: !isMobile,
                          showTotal: (total) => t('totalDeMembros', { total }),
                          pageSizeOptions: [5, 10, 20],
                          simple: isMobile,
                          position: ['bottomCenter'],
                        }
                        : false
                    }
                    size="small"
                    scroll={{
                      x: isMobile ? 'max-content' : undefined,
                      y: members.length > 10 ? 500 : undefined,
                    }}
                  />
                </Card>
                </Space>
              </Card>
            </div>
          </>
        )}
        </div>
      </div>

      {/* 添加成员模态框 */}
      <Modal
        title={t('adicionarMembroOrganizacao')}
        open={isAddMemberModalOpen}
        onCancel={() => {
          setIsAddMemberModalOpen(false);
          form.resetFields();
        }}
        footer={null}
        centered={!isMobile}
        width={isMobile ? '100%' : 500}
        style={isMobile ? { top: 0, paddingBottom: 0, maxWidth: '100vw' } : undefined}
        styles={isMobile ? { body: { maxHeight: 'calc(100vh - 110px)', overflowY: 'auto' } } : undefined}
      >
        <Form
          form={form}
          layout="vertical"
          onFinish={handleAddMember}
        >
          <Form.Item
            name="character_id"
            label={t('selecionarPersonagem')}
            rules={[{ required: true, message: t('selecioneUmPersonagem') }]}
          >
            <Select
              placeholder={t('selecionePersonagemVai')}
              showSearch
              filterOption={(input, option) =>
                (option?.label ?? '').toLowerCase().includes(input.toLowerCase())
              }
              options={availableCharacters.map(c => ({
                label: c.name,
                value: c.id
              }))}
            />
          </Form.Item>

          <Form.Item
            name="position"
            label={t('cargo')}
            rules={[{ required: true, message: t('informeOCargo') }]}
          >
            <Input placeholder={t('exLiderAnciao')} />
          </Form.Item>

          <Form.Item
            name="rank"
            label={t('nivelDoCargo')}
            initialValue={5}
            tooltip={t('quantoMaiorNumero')}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="loyalty"
            label={t('lealdadeInicial')}
            initialValue={50}
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>

          <Form.Item
            name="status"
            label={t('status')}
            initialValue="active"
          >
            <Select>
              <Select.Option value="active">{t('ativo')}</Select.Option>
              <Select.Option value="retired">{t('aposentado')}</Select.Option>
              <Select.Option value="expelled">{t('expulso')}</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="joined_at"
            label={t('dataDeEntrada')}
          >
            <Input placeholder={t('exCerimoniaFundacao')} />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsAddMemberModalOpen(false)}>{t('cancelar')}</Button>
              <Button type="primary" htmlType="submit">
                {t('adicionar')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑成员模态框 */}
      <Modal
        title={t('editarInformacoesMembro')}
        open={isEditMemberModalOpen}
        onCancel={() => {
          setIsEditMemberModalOpen(false);
          editMemberForm.resetFields();
          setEditingMember(null);
        }}
        footer={null}
        centered={true}
        width={isMobile ? '90%' : 500}
        style={isMobile ? {
          maxWidth: '90vw',
          margin: '0 auto'
        } : undefined}
        styles={isMobile ? {
          body: {
            maxHeight: 'calc(80vh - 110px)',
            overflowY: 'auto',
            padding: '20px 16px'
          }
        } : undefined}
      >
        <Form
          form={editMemberForm}
          layout="vertical"
          onFinish={handleUpdateMember}
        >
          <Form.Item
            name="position"
            label={t('cargo')}
            rules={[{ required: true, message: t('informeOCargo') }]}
          >
            <Input placeholder={t('exLiderAnciao')} />
          </Form.Item>

          <Form.Item
            name="rank"
            label={t('nivelDoCargo')}
            tooltip={t('quantoMaiorNumero')}
          >
            <InputNumber min={0} max={10} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="loyalty"
            label={t('lealdade')}
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>

          <Form.Item
            name="contribution"
            label={t('contribuicao')}
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} addonAfter="%" />
          </Form.Item>

          <Form.Item
            name="status"
            label={t('status')}
          >
            <Select>
              <Select.Option value="active">{t('ativo')}</Select.Option>
              <Select.Option value="retired">{t('aposentado')}</Select.Option>
              <Select.Option value="expelled">{t('expulso')}</Select.Option>
              <Select.Option value="deceased">{t('falecido')}</Select.Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="joined_at"
            label={t('dataDeEntrada')}
          >
            <Input placeholder={t('exCerimoniaFundacao')} />
          </Form.Item>

          <Form.Item
            name="notes"
            label={t('observacoes')}
          >
            <Input.TextArea rows={3} placeholder={t('observacoesRelacionadasMembro')} />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setIsEditMemberModalOpen(false);
                editMemberForm.resetFields();
                setEditingMember(null);
              }}>
                {t('cancelar')}
              </Button>
              <Button type="primary" htmlType="submit">
                {t('salvar')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 编辑组织模态框 */}
      <Modal
        title={t('editarInformacoesOrganizacao')}
        open={isEditOrgModalOpen}
        onCancel={() => {
          setIsEditOrgModalOpen(false);
          editOrgForm.resetFields();
        }}
        footer={null}
        centered={!isMobile}
        width={isMobile ? '100%' : 500}
        style={isMobile ? { top: 0, paddingBottom: 0, maxWidth: '100vw' } : undefined}
        styles={isMobile ? { body: { maxHeight: 'calc(100vh - 110px)', overflowY: 'auto' } } : undefined}
      >
        <Form
          form={editOrgForm}
          layout="vertical"
          onFinish={async (values) => {
            if (!selectedOrg) return;
            try {
              await axios.put(`/api/organizations/${selectedOrg.id}`, values);
              message.success(t('informacoesOrganizacaoAtualizadas'));
              setIsEditOrgModalOpen(false);
              editOrgForm.resetFields();

              // 重新获取更新后的组织列表
              const res = await axios.get(`/api/organizations/project/${projectId}`);
              setOrganizations(res.data);

              // 更新当前选中的组织详情
              const updatedOrg = res.data.find((org: Organization) => org.id === selectedOrg.id);
              if (updatedOrg) {
                setSelectedOrg(updatedOrg);
              }

              // 刷新全局 store
              await refreshCharacters();
            } catch (error) {
              message.error(t('falhaAoAtualizar'));
              console.error(error);
            }
          }}
        >
          <Form.Item
            name="power_level"
            label={t('nivelDePoder')}
            rules={[{ required: true, message: t('informeNivelPoder') }]}
            tooltip={t('valor0100')}
          >
            <InputNumber min={0} max={100} style={{ width: '100%' }} />
          </Form.Item>

          <Form.Item
            name="location"
            label={t('localizacao')}
          >
            <Input placeholder={t('principalAreaAtuacao')} />
          </Form.Item>

          <Form.Item
            name="motto"
            label={t('lemaSlogan')}
          >
            <Input placeholder={t('propositoLemaOu')} />
          </Form.Item>

          <Form.Item
            name="color"
            label={t('corRepresentativa')}
          >
            <Input placeholder={t('exVermelhoEscuro')} />
          </Form.Item>

          <Form.Item>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => setIsEditOrgModalOpen(false)}>{t('cancelar')}</Button>
              <Button type="primary" htmlType="submit">
                {t('salvar')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
}

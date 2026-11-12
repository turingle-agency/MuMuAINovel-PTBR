import { useState, useEffect, useRef } from 'react';
import { Button, Modal, Form, Input, Select, message, Row, Col, Empty, Tabs, Divider, Typography, Space, InputNumber, Checkbox, theme } from 'antd';
import { ThunderboltOutlined, UserOutlined, TeamOutlined, PlusOutlined, ExportOutlined, ImportOutlined, DownloadOutlined } from '@ant-design/icons';
import { useStore } from '../store';
import { useCharacterSync } from '../store/hooks';
import { charactersPageGridConfig } from '../components/CardStyles';
import { CharacterCard } from '../components/CharacterCard';
import { SSELoadingOverlay } from '../components/SSELoadingOverlay';
import type { Character, ApiError } from '../types';
import { characterApi } from '../services/api';
import { SSEPostClient } from '../utils/sseClient';
import api from '../services/api';
import { useTranslation } from 'react-i18next';

const { Title } = Typography;
const { TextArea } = Input;

interface Career {
  id: string;
  name: string;
  type: 'main' | 'sub';
  max_stage: number;
}

// 副职业数据类型
interface SubCareerData {
  career_id: string;
  stage: number;
}

// 角色创建表单值类型
interface CharacterFormValues {
  name: string;
  age?: string;
  gender?: string;
  role_type?: string;
  personality?: string;
  appearance?: string;
  background?: string;
  main_career_id?: string;
  main_career_stage?: number;
  sub_career_data?: SubCareerData[];
  // 组织字段
  organization_type?: string;
  organization_purpose?: string;
  organization_members?: string;
  power_level?: number;
  location?: string;
  motto?: string;
  color?: string;
}

// 角色创建数据类型
interface CharacterCreateData {
  project_id: string;
  name: string;
  is_organization: boolean;
  age?: string;
  gender?: string;
  role_type?: string;
  personality?: string;
  appearance?: string;
  background?: string;
  main_career_id?: string;
  main_career_stage?: number;
  sub_careers?: string;
  organization_type?: string;
  organization_purpose?: string;
  organization_members?: string;
  power_level?: number;
  location?: string;
  motto?: string;
  color?: string;
}

// 角色更新数据类型
interface CharacterUpdateData {
  name?: string;
  age?: string;
  gender?: string;
  role_type?: string;
  personality?: string;
  appearance?: string;
  background?: string;
  main_career_id?: string;
  main_career_stage?: number;
  sub_careers?: string;
  organization_type?: string;
  organization_purpose?: string;
  organization_members?: string;
  power_level?: number;
  location?: string;
  motto?: string;
  color?: string;
}

export default function Characters() {
  const { t } = useTranslation('characters');
  const { token } = theme.useToken();
  const { currentProject, characters } = useStore();
  const [isGenerating, setIsGenerating] = useState(false);
  const [progress, setProgress] = useState(0);
  const [progressMessage, setProgressMessage] = useState('');
  const [activeTab, setActiveTab] = useState<'all' | 'character' | 'organization'>('all');
  const [generateForm] = Form.useForm();
  const [generateOrgForm] = Form.useForm();
  const [createForm] = Form.useForm();
  const [editForm] = Form.useForm();
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false);
  const [createType, setCreateType] = useState<'character' | 'organization'>('character');
  const [editingCharacter, setEditingCharacter] = useState<Character | null>(null);
  const [mainCareers, setMainCareers] = useState<Career[]>([]);
  const [subCareers, setSubCareers] = useState<Career[]>([]);
  const [selectedCharacters, setSelectedCharacters] = useState<string[]>([]);
  const [isImportModalOpen, setIsImportModalOpen] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const {
    refreshCharacters,
    deleteCharacter
  } = useCharacterSync();

  useEffect(() => {
    if (currentProject?.id) {
      refreshCharacters();
      fetchCareers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [currentProject?.id]);
  const [modal, contextHolder] = Modal.useModal();

  const fetchCareers = async () => {
    if (!currentProject?.id) return;
    try {
      const response = await api.get<unknown, { main_careers: Career[]; sub_careers: Career[] }>('/careers', {
        params: { project_id: currentProject.id }
      });
      setMainCareers(response.main_careers || []);
      setSubCareers(response.sub_careers || []);
    } catch (error) {
      console.error(t('falhaCarregarCarreiras'), error);
    }
  };

  if (!currentProject) return null;

  const handleDeleteCharacter = async (id: string) => {
    try {
      await deleteCharacter(id);
      message.success(t('excluidoSucesso'));
    } catch {
      message.error(t('falhaExcluir'));
    }
  };

  const handleGenerate = async (values: { name?: string; role_type: string; background?: string }) => {
    try {
      setIsGenerating(true);
      setProgress(0);
      setProgressMessage(t('preparandoGeracaoPersonagem'));

      const client = new SSEPostClient(
        '/api/characters/generate-stream',
        {
          project_id: currentProject.id,
          name: values.name,
          role_type: values.role_type,
          background: values.background,
        },
        {
          onProgress: (msg, prog) => {
            setProgress(prog);
            setProgressMessage(msg);
          },
          onResult: (data) => {
            console.log(t('personagemGerado'), data);
          },
          onError: (error) => {
            message.error(t('falhaGeracao', { error }));
          },
          onComplete: () => {
            setProgress(100);
            setProgressMessage(t('geracaoConcluida'));
          }
        }
      );

      await client.connect();
      message.success(t('personagemGeradoPelaIa'));
      Modal.destroyAll();
      await refreshCharacters();
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : t('falhaGeracaoPelaIa');
      message.error(errorMessage);
    } finally {
      setTimeout(() => {
        setIsGenerating(false);
        setProgress(0);
        setProgressMessage('');
      }, 500);
    }
  };

  const handleGenerateOrganization = async (values: {
    name?: string;
    organization_type?: string;
    background?: string;
    requirements?: string;
  }) => {
    try {
      setIsGenerating(true);
      setProgress(0);
      setProgressMessage(t('preparandoGeracaoOrganizacao'));

      const client = new SSEPostClient(
        '/api/organizations/generate-stream',
        {
          project_id: currentProject.id,
          name: values.name,
          organization_type: values.organization_type,
          background: values.background,
          requirements: values.requirements,
        },
        {
          onProgress: (msg, prog) => {
            setProgress(prog);
            setProgressMessage(msg);
          },
          onResult: (data) => {
            console.log(t('organizacaoGerada'), data);
          },
          onError: (error) => {
            message.error(t('falhaGeracao', { error }));
          },
          onComplete: () => {
            setProgress(100);
            setProgressMessage(t('geracaoConcluida'));
          }
        }
      );

      await client.connect();
      message.success(t('organizacaoGeradaPelaIa'));
      Modal.destroyAll();
      await refreshCharacters();
    } catch (error: unknown) {
      const errorMessage = error instanceof Error ? error.message : t('falhaGeracaoPelaIa');
      message.error(errorMessage);
    } finally {
      setTimeout(() => {
        setIsGenerating(false);
        setProgress(0);
        setProgressMessage('');
      }, 500);
    }
  };

  const handleCreateCharacter = async (values: CharacterFormValues) => {
    try {
      const createData: CharacterCreateData = {
        project_id: currentProject.id,
        name: values.name,
        is_organization: createType === 'organization',
      };

      if (createType === 'character') {
        // 角色字段
        createData.age = values.age;
        createData.gender = values.gender;
        createData.role_type = values.role_type || 'supporting';
        createData.personality = values.personality;
        createData.appearance = values.appearance;
        createData.background = values.background;
        
        // 职业字段
        if (values.main_career_id) {
          createData.main_career_id = values.main_career_id;
          createData.main_career_stage = values.main_career_stage || 1;
        }
        
        // 处理副职业数据
        if (values.sub_career_data && Array.isArray(values.sub_career_data) && values.sub_career_data.length > 0) {
          createData.sub_careers = JSON.stringify(values.sub_career_data);
        }
      } else {
        // 组织字段
        createData.organization_type = values.organization_type;
        createData.organization_purpose = values.organization_purpose;
        createData.background = values.background;
        createData.power_level = values.power_level;
        createData.location = values.location;
        createData.motto = values.motto;
        createData.color = values.color;
        createData.role_type = 'supporting'; // 组织默认为配角
      }

      await characterApi.createCharacter(createData);
      message.success(createType === 'character' ? t('personagemCriadoSucesso') : t('organizacaoCriadaSucesso'));
      setIsCreateModalOpen(false);
      createForm.resetFields();
      await refreshCharacters();
    } catch {
      message.error(t('falhaCriar'));
    }
  };

  const handleEditCharacter = (character: Character) => {
    setEditingCharacter(character);

    // 提取副职业数据（包含职业ID和阶段）
    const subCareerData: SubCareerData[] = character.sub_careers?.map((sc) => ({
      career_id: sc.career_id,
      stage: sc.stage || 1
    })) || [];

    editForm.setFieldsValue({
      ...character,
      sub_career_data: subCareerData
    });
    setIsEditModalOpen(true);
  };

  const handleUpdateCharacter = async (values: CharacterFormValues) => {
    if (!editingCharacter) return;

    try {
      // 提取副职业数据，剩余的作为更新数据
      const { sub_career_data: subCareerData, ...restValues } = values;
      const updateData: CharacterUpdateData = { ...restValues };

      // 转换为sub_careers格式
      if (subCareerData && Array.isArray(subCareerData) && subCareerData.length > 0) {
        updateData.sub_careers = JSON.stringify(subCareerData);
      } else {
        updateData.sub_careers = JSON.stringify([]);
      }

      await characterApi.updateCharacter(editingCharacter.id, updateData);
      message.success(t('atualizadoSucesso'));
      setIsEditModalOpen(false);
      editForm.resetFields();
      setEditingCharacter(null);
      await refreshCharacters();
    } catch (error) {
      console.error(t('falhaAtualizar'), error);
      message.error(t('falhaAtualizarToast'));
    }
  };

  const handleDeleteCharacterWrapper = (id: string) => {
    handleDeleteCharacter(id);
  };

  // 导出选中的角色/组织
  const handleExportSelected = async () => {
    if (selectedCharacters.length === 0) {
      message.warning(t('selecionePeloMenosPersonagem'));
      return;
    }

    try {
      await characterApi.exportCharacters(selectedCharacters);
      message.success(t('personagemNsOrganizacaoOes', { length: selectedCharacters.length }));
      setSelectedCharacters([]);
    } catch (error) {
      message.error(t('falhaExportar'));
      console.error(t('erroExportar'), error);
    }
  };

  // 导出单个角色/组织
  const handleExportSingle = async (characterId: string) => {
    try {
      await characterApi.exportCharacters([characterId]);
      message.success(t('exportadoSucesso'));
    } catch (error) {
      message.error(t('falhaExportar'));
      console.error(t('erroExportar'), error);
    }
  };

  // 处理文件选择
  const handleFileSelect = async (file: File) => {
    try {
      // 验证文件
      const validation = await characterApi.validateImportCharacters(file);
      
      if (!validation.valid) {
        modal.error({
          title: t('falhaValidacaoArquivo'),
          centered: true,
          content: (
            <div>
              {validation.errors.map((error, index) => (
                <div key={index} style={{ color: token.colorError }}>• {error}</div>
              ))}
            </div>
          ),
        });
        return;
      }

      // 显示预览对话框
      modal.confirm({
        title: t('previaImportacao'),
        width: 500,
        centered: true,
        content: (
          <div>
            <p><strong>{t('versaoArquivo')}</strong> {validation.version}</p>
            <Divider style={{ margin: '12px 0' }} />
            <p><strong>{t('seraImportado')}</strong></p>
            <ul style={{ marginLeft: 20 }}>
              <li>{t('personagens', { characters: validation.statistics.characters })}</li>
              <li>{t('organizacoes', { organizations: validation.statistics.organizations })}</li>
            </ul>
            {validation.warnings.length > 0 && (
              <>
                <Divider style={{ margin: '12px 0' }} />
                <p style={{ color: token.colorWarning }}><strong>{t('avisos')}</strong></p>
                <ul style={{ marginLeft: 20 }}>
                  {validation.warnings.map((warning, index) => (
                    <li key={index} style={{ color: token.colorWarning }}>{warning}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
        ),
        okText: t('confirmarImportacao'),
        cancelText: t('cancelar'),
        onOk: async () => {
          try {
            const result = await characterApi.importCharacters(currentProject.id, file);
            
            if (result.success) {
              // 显示导入结果
              modal.success({
                title: t('importacaoConcluida'),
                width: 600,
                centered: true,
                content: (
                  <div>
                    <p><strong>{t('importadosSucesso', { imported: result.statistics.imported })}</strong></p>
                    {result.details.imported_characters.length > 0 && (
                      <>
                        <p style={{ marginTop: 12, marginBottom: 4 }}>{t('personagensImportados')}</p>
                        <ul style={{ marginLeft: 20 }}>
                          {result.details.imported_characters.map((name, index) => (
                            <li key={index}>{name}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {result.details.imported_organizations.length > 0 && (
                      <>
                        <p style={{ marginTop: 12, marginBottom: 4 }}>{t('organizacoesImportadas')}</p>
                        <ul style={{ marginLeft: 20 }}>
                          {result.details.imported_organizations.map((name, index) => (
                            <li key={index}>{name}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {result.statistics.skipped > 0 && (
                      <>
                        <Divider style={{ margin: '12px 0' }} />
                        <p style={{ color: token.colorWarning }}>{t('ignorados', { skipped: result.statistics.skipped })}</p>
                        <ul style={{ marginLeft: 20 }}>
                          {result.details.skipped.map((name, index) => (
                            <li key={index} style={{ color: token.colorWarning }}>{name}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {result.warnings.length > 0 && (
                      <>
                        <Divider style={{ margin: '12px 0' }} />
                        <p style={{ color: token.colorWarning }}>{t('avisos')}</p>
                        <ul style={{ marginLeft: 20 }}>
                          {result.warnings.map((warning, index) => (
                            <li key={index} style={{ color: token.colorWarning }}>{warning}</li>
                          ))}
                        </ul>
                      </>
                    )}
                    {result.details.errors.length > 0 && (
                      <>
                        <Divider style={{ margin: '12px 0' }} />
                        <p style={{ color: token.colorError }}>{t('falhas', { errors: result.statistics.errors })}</p>
                        <ul style={{ marginLeft: 20 }}>
                          {result.details.errors.map((error, index) => (
                            <li key={index} style={{ color: token.colorError }}>{error}</li>
                          ))}
                        </ul>
                      </>
                    )}
                  </div>
                ),
              });
              
              // 刷新列表
              await refreshCharacters();
              setIsImportModalOpen(false);
            } else {
              message.error(result.message || t('falhaImportacao'));
            }
          } catch (error: unknown) {
            const apiError = error as ApiError;
            message.error(apiError.response?.data?.detail || t('falhaImportacao'));
            console.error(t('erroImportacao'), error);
          }
        },
      });
    } catch (error: unknown) {
      const apiError = error as ApiError;
      message.error(apiError.response?.data?.detail || t('falhaValidacaoArquivo'));
      console.error(t('erroValidacao'), error);
    }
  };

  // 切换选择
  const toggleSelectCharacter = (id: string) => {
    setSelectedCharacters(prev =>
      prev.includes(id) ? prev.filter(cid => cid !== id) : [...prev, id]
    );
  };

  // 全选/取消全选
  const toggleSelectAll = () => {
    if (selectedCharacters.length === displayList.length) {
      setSelectedCharacters([]);
    } else {
      setSelectedCharacters(displayList.map(c => c.id));
    }
  };

  const showGenerateModal = () => {
    modal.confirm({
      title: t('gerarPersonagemIa'),
      width: 600,
      centered: true,
      content: (
        <Form form={generateForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label={t('nomePersonagem')}
            name="name"
          >
            <Input placeholder={t('exAnaSouzaCarlos')} />
          </Form.Item>
          <Form.Item
            label={t('papelPersonagem')}
            name="role_type"
            rules={[{ required: true, message: t('selecionePapelPersonagem') }]}
          >
            <Select placeholder={t('selecionePapelPersonagem')}>
              <Select.Option value="protagonist">{t('protagonista')}</Select.Option>
              <Select.Option value="supporting">{t('coadjuvante')}</Select.Option>
              <Select.Option value="antagonist">{t('antagonista')}</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item label={t('contexto')} name="background">
            <TextArea rows={3} placeholder={t('descrevaBrevementeContextoPersonagem')} />
          </Form.Item>
        </Form>
      ),
      okText: t('gerar'),
      cancelText: t('cancelar'),
      onOk: async () => {
        const values = await generateForm.validateFields();
        await handleGenerate(values);
      },
    });
  };

  const showGenerateOrgModal = () => {
    modal.confirm({
      title: t('gerarOrganizacaoIa'),
      width: 600,
      centered: true,
      content: (
        <Form form={generateOrgForm} layout="vertical" style={{ marginTop: 16 }}>
          <Form.Item
            label={t('nomeOrganizacao')}
            name="name"
          >
            <Input placeholder={t('exOrdemEspadaCeleste')} />
          </Form.Item>
          <Form.Item
            label={t('tipoOrganizacao')}
            name="organization_type"
          >
            <Input placeholder={t('exSeitaGangueEmpresa')} />
          </Form.Item>
          <Form.Item label={t('contexto')} name="background">
            <TextArea rows={3} placeholder={t('descrevaBrevementeContextoAmbiente')} />
          </Form.Item>
          <Form.Item label={t('outrosRequisitos')} name="requirements">
            <TextArea rows={2} placeholder={t('outrosRequisitosEspecificos')} />
          </Form.Item>
        </Form>
      ),
      okText: t('gerar'),
      cancelText: t('cancelar'),
      onOk: async () => {
        const values = await generateOrgForm.validateFields();
        await handleGenerateOrganization(values);
      },
    });
  };

  const characterList = characters.filter(c => !c.is_organization);
  const organizationList = characters.filter(c => c.is_organization);

  const getDisplayList = () => {
    if (activeTab === 'character') return characterList;
    if (activeTab === 'organization') return organizationList;
    return characters;
  };

  const displayList = getDisplayList();

  const isMobile = window.innerWidth <= 768;

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {contextHolder}
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 10,
        backgroundColor: 'var(--color-bg-container)',
        padding: isMobile ? '12px 0' : '16px 0',
        marginBottom: isMobile ? 12 : 16,
        borderBottom: '1px solid var(--color-border-secondary)',
        display: 'flex',
        flexDirection: isMobile ? 'column' : 'row',
        gap: isMobile ? 12 : 0,
        justifyContent: 'space-between',
        alignItems: isMobile ? 'stretch' : 'center'
      }}>
        <h2 style={{ margin: 0, fontSize: isMobile ? 18 : 24 }}>
          <TeamOutlined style={{ marginRight: 8 }} />
          {t('gerenciamentoPersonagensOrganizacoes')}
        </h2>
        <Space wrap>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setCreateType('character');
              setIsCreateModalOpen(true);
            }}
            size={isMobile ? 'small' : 'middle'}
          >
            {t('criarPersonagem')}
          </Button>
          <Button
            type="primary"
            icon={<PlusOutlined />}
            onClick={() => {
              setCreateType('organization');
              setIsCreateModalOpen(true);
            }}
            size={isMobile ? 'small' : 'middle'}
          >
            {t('criarOrganizacao')}
          </Button>
          <Button
            type="dashed"
            icon={<ThunderboltOutlined />}
            onClick={showGenerateModal}
            loading={isGenerating}
            size={isMobile ? 'small' : 'middle'}
          >
            {t('gerarPersonagemIa')}
          </Button>
          <Button
            type="dashed"
            icon={<ThunderboltOutlined />}
            onClick={showGenerateOrgModal}
            loading={isGenerating}
            size={isMobile ? 'small' : 'middle'}
          >
            {t('gerarOrganizacaoIa')}
          </Button>
          <Button
            icon={<ImportOutlined />}
            onClick={() => setIsImportModalOpen(true)}
            size={isMobile ? 'small' : 'middle'}
          >
            {t('importar')}
          </Button>
          {selectedCharacters.length > 0 && (
            <Button
              icon={<ExportOutlined />}
              onClick={handleExportSelected}
              size={isMobile ? 'small' : 'middle'}
            >
              {t('exportarLote', { length: selectedCharacters.length })}
            </Button>
          )}
        </Space>
      </div>

      {characters.length > 0 && (
        <div style={{
          position: 'sticky',
          top: isMobile ? 60 : 72,
          zIndex: 9,
          backgroundColor: 'var(--color-bg-container)',
          paddingBottom: 8,
          borderBottom: '1px solid var(--color-border-secondary)',
        }}>
          <Tabs
            activeKey={activeTab}
            onChange={(key) => setActiveTab(key as 'all' | 'character' | 'organization')}
            items={[
              {
                key: 'all',
                label: t('todos', { length: characters.length }),
              },
              {
                key: 'character',
                label: (
                  <span>
                    <UserOutlined /> {t('personagensContagem', { length: characterList.length })}
                  </span>
                ),
              },
              {
                key: 'organization',
                label: (
                  <span>
                    <TeamOutlined /> {t('organizacoesContagem', { length: organizationList.length })}
                  </span>
                ),
              },
            ]}
          />
        </div>
      )}

      {/* 批量选择工具栏 */}
      {characters.length > 0 && (
        <div style={{
          position: 'sticky',
          top: isMobile ? 120 : 132,
          zIndex: 8,
          backgroundColor: 'var(--color-bg-container)',
          paddingBottom: 8,
          paddingTop: 8,
          marginTop: 8,
          borderBottom: selectedCharacters.length > 0 ? '1px solid var(--color-border-secondary)' : 'none',
        }}>
          <Space>
            <Checkbox
              checked={selectedCharacters.length === displayList.length && displayList.length > 0}
              indeterminate={selectedCharacters.length > 0 && selectedCharacters.length < displayList.length}
              onChange={toggleSelectAll}
            >
              {selectedCharacters.length > 0 ? t('selecionadoS', { length: selectedCharacters.length }) : t('selecionarTudo')}
            </Checkbox>
            {selectedCharacters.length > 0 && (
              <Button
                type="link"
                size="small"
                onClick={() => setSelectedCharacters([])}
              >
                {t('desmarcar')}
              </Button>
            )}
          </Space>
        </div>
      )}

      <div style={{ flex: 1, overflowY: 'auto' }}>
        {characters.length === 0 ? (
          <Empty description={t('aindaNaoHaPersonagens')} />
        ) : (
          <>
            <Row gutter={isMobile ? [8, 8] : charactersPageGridConfig.gutter}>
              {activeTab === 'all' && (
                <>
                  {characterList.length > 0 && (
                    <>
                      <Col span={24}>
                        <Divider orientation="left">
                          <Title level={5} style={{ margin: 0 }}>
                            <UserOutlined style={{ marginRight: 8 }} />
                            {t('personagensContagem', { length: characterList.length })}
                          </Title>
                        </Divider>
                      </Col>
                      {characterList.map((character) => (
                        <Col
                          xs={24}
                          sm={charactersPageGridConfig.sm}
                          md={charactersPageGridConfig.md}
                          lg={charactersPageGridConfig.lg}
                          xl={charactersPageGridConfig.xl}
                          key={character.id}
                          style={{ padding: isMobile ? '4px' : '8px' }}
                        >
                          <div style={{ position: 'relative' }}>
                            <Checkbox
                              checked={selectedCharacters.includes(character.id)}
                              onChange={() => toggleSelectCharacter(character.id)}
                              style={{ position: 'absolute', top: 8, left: 8, zIndex: 1 }}
                            />
                            <CharacterCard
                              character={character}
                              onEdit={handleEditCharacter}
                              onDelete={handleDeleteCharacterWrapper}
                              onExport={() => handleExportSingle(character.id)}
                            />
                          </div>
                        </Col>
                      ))}
                    </>
                  )}

                  {organizationList.length > 0 && (
                    <>
                      <Col span={24}>
                        <Divider orientation="left">
                          <Title level={5} style={{ margin: 0 }}>
                            <TeamOutlined style={{ marginRight: 8 }} />
                            {t('organizacoesContagem', { length: organizationList.length })}
                          </Title>
                        </Divider>
                      </Col>
                      {organizationList.map((org) => (
                        <Col
                          xs={24}
                          sm={charactersPageGridConfig.sm}
                          md={charactersPageGridConfig.md}
                          lg={charactersPageGridConfig.lg}
                          xl={charactersPageGridConfig.xl}
                          key={org.id}
                          style={{ padding: isMobile ? '4px' : '8px' }}
                        >
                          <div style={{ position: 'relative' }}>
                            <Checkbox
                              checked={selectedCharacters.includes(org.id)}
                              onChange={() => toggleSelectCharacter(org.id)}
                              style={{ position: 'absolute', top: 8, left: 8, zIndex: 1 }}
                            />
                            <CharacterCard
                              character={org}
                              onEdit={handleEditCharacter}
                              onDelete={handleDeleteCharacterWrapper}
                              onExport={() => handleExportSingle(org.id)}
                            />
                          </div>
                        </Col>
                      ))}
                    </>
                  )}
                </>
              )}

              {activeTab === 'character' && characterList.map((character) => (
                <Col
                  xs={24}
                  sm={charactersPageGridConfig.sm}
                  md={charactersPageGridConfig.md}
                  lg={charactersPageGridConfig.lg}
                  xl={charactersPageGridConfig.xl}
                  key={character.id}
                  style={{ padding: isMobile ? '4px' : '8px' }}
                >
                  <div style={{ position: 'relative' }}>
                    <Checkbox
                      checked={selectedCharacters.includes(character.id)}
                      onChange={() => toggleSelectCharacter(character.id)}
                      style={{ position: 'absolute', top: 8, left: 8, zIndex: 1 }}
                    />
                    <CharacterCard
                      character={character}
                      onEdit={handleEditCharacter}
                      onDelete={handleDeleteCharacterWrapper}
                      onExport={() => handleExportSingle(character.id)}
                    />
                  </div>
                </Col>
              ))}

              {activeTab === 'organization' && organizationList.map((org) => (
                <Col
                  xs={24}
                  sm={charactersPageGridConfig.sm}
                  md={charactersPageGridConfig.md}
                  lg={charactersPageGridConfig.lg}
                  xl={charactersPageGridConfig.xl}
                  key={org.id}
                  style={{ padding: isMobile ? '4px' : '8px' }}
                >
                  <div style={{ position: 'relative' }}>
                    <Checkbox
                      checked={selectedCharacters.includes(org.id)}
                      onChange={() => toggleSelectCharacter(org.id)}
                      style={{ position: 'absolute', top: 8, left: 8, zIndex: 1 }}
                    />
                    <CharacterCard
                      character={org}
                      onEdit={handleEditCharacter}
                      onDelete={handleDeleteCharacterWrapper}
                      onExport={() => handleExportSingle(org.id)}
                    />
                  </div>
                </Col>
              ))}
            </Row>

            {displayList.length === 0 && (
              <Empty
                description={
                  activeTab === 'character'
                    ? t('nenhumPersonagem')
                    : activeTab === 'organization'
                      ? t('nenhumaOrganizacao')
                      : t('semDados')
                }
              />
            )}
          </>
        )}
      </div>

      <Modal
        title={editingCharacter?.is_organization ? t('editarOrganizacao') : t('editarPersonagem')}
        open={isEditModalOpen}
        onCancel={() => {
          setIsEditModalOpen(false);
          editForm.resetFields();
          setEditingCharacter(null);
        }}
        footer={
          <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
            <Button onClick={() => {
              setIsEditModalOpen(false);
              editForm.resetFields();
              setEditingCharacter(null);
            }}>
              {t('cancelar')}
            </Button>
            <Button type="primary" onClick={() => editForm.submit()}>
              {t('salvar')}
            </Button>
          </Space>
        }
        centered
        width={isMobile ? '100%' : 700}
        style={isMobile ? { top: 0, paddingBottom: 0, maxWidth: '100vw' } : undefined}
        styles={{
          body: {
            maxHeight: isMobile ? 'calc(100vh - 110px)' : 'calc(100vh - 200px)',
            overflowY: 'auto',
            overflowX: 'hidden'
          }
        }}
      >
        <Form form={editForm} layout="vertical" onFinish={handleUpdateCharacter} style={{ marginTop: 8 }}>
          {!editingCharacter?.is_organization ? (
            <>
              {/* 编辑角色 - 第一行：名称、定位、年龄、性别 */}
              <Row gutter={12}>
                <Col span={8}>
                  <Form.Item
                    label={t('nomePersonagem')}
                    name="name"
                    rules={[{ required: true, message: t('informeNomePersonagem') }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder={t('nomePersonagem')} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label={t('papelPersonagem')} name="role_type" style={{ marginBottom: 12 }}>
                    <Select>
                      <Select.Option value="protagonist">{t('protagonista')}</Select.Option>
                      <Select.Option value="supporting">{t('coadjuvante')}</Select.Option>
                      <Select.Option value="antagonist">{t('antagonista')}</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={5}>
                  <Form.Item label={t('idade')} name="age" style={{ marginBottom: 12 }}>
                    <Input placeholder={t('ex25Anos')} />
                  </Form.Item>
                </Col>
                <Col span={5}>
                  <Form.Item label={t('genero')} name="gender" style={{ marginBottom: 12 }}>
                    <Select placeholder={t('genero')}>
                      <Select.Option value="masculino">{t('masculino')}</Select.Option>
                      <Select.Option value="feminino">{t('feminino')}</Select.Option>
                      <Select.Option value="outro">{t('outro')}</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              {/* 第二行：性格特点、外貌描写 */}
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={t('personalidade')} name="personality" style={{ marginBottom: 12 }}>
                    <TextArea rows={2} placeholder={t('descrevaPersonalidadePersonagem')} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={t('aparencia')} name="appearance" style={{ marginBottom: 12 }}>
                    <TextArea rows={2} placeholder={t('descrevaCaracteristicasFisicasPersonagem')} />
                  </Form.Item>
                </Col>
              </Row>

              {/* 人际关系（只读，由关系管理页面维护） */}
              {editingCharacter?.relationships && (
                <Form.Item label={t('relacionamentosMantidosPeloGerenciador')} style={{ marginBottom: 12 }}>
                  <Input.TextArea
                    value={editingCharacter.relationships}
                    readOnly
                    autoSize={{ minRows: 1, maxRows: 3 }}
                    style={{ backgroundColor: token.colorFillTertiary, cursor: 'default' }}
                  />
                </Form.Item>
              )}

              {/* 第四行：角色背景 */}
              <Form.Item label={t('historicoPersonagem')} name="background" style={{ marginBottom: 12 }}>
                <TextArea rows={2} placeholder={t('descrevaHistoriaFundoPersonagem')} />
              </Form.Item>

              {/* 职业信息 */}
              {(mainCareers.length > 0 || subCareers.length > 0) && (
                <>
                  <Divider style={{ margin: '8px 0' }}>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>{t('informacoesCarreira')}</Typography.Text>
                  </Divider>
                  {mainCareers.length > 0 && (
                    <Row gutter={12}>
                      <Col span={16}>
                        <Form.Item label={t('carreiraPrincipal')} name="main_career_id" tooltip={t('principalCarreiraDesenvolvimentoPersonagem')} style={{ marginBottom: 12 }}>
                          <Select placeholder={t('selecioneCarreiraPrincipal')} allowClear size="small">
                            {mainCareers.map(career => (
                              <Select.Option key={career.id} value={career.id}>
                                {t('estagioMax', { name: career.name, max_stage: career.max_stage })}
                              </Select.Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item label={t('estagioAtual')} name="main_career_stage" tooltip={t('estagioAtualCarreiraPrincipal')} style={{ marginBottom: 12 }}>
                          <InputNumber
                            min={1}
                            max={editForm.getFieldValue('main_career_id') ?
                              mainCareers.find(c => c.id === editForm.getFieldValue('main_career_id'))?.max_stage || 10
                              : 10}
                            style={{ width: '100%' }}
                            placeholder={t('estagio')}
                            size="small"
                          />
                        </Form.Item>
                      </Col>
                    </Row>
                  )}
                  {subCareers.length > 0 && (
                    <Form.List name="sub_career_data">
                      {(fields, { add, remove }) => (
                        <>
                          <div style={{ marginBottom: 4 }}>
                            <Typography.Text strong style={{ fontSize: 12 }}>{t('carreiraSecundaria')}</Typography.Text>
                          </div>
                          <div style={{ maxHeight: '80px', overflowY: 'auto', overflowX: 'hidden', marginBottom: 8, paddingRight: 8 }}>
                            {fields.map((field) => (
                              <Row key={field.key} gutter={8} style={{ marginBottom: 4 }}>
                                <Col span={16}>
                                  <Form.Item
                                    {...field}
                                    name={[field.name, 'career_id']}
                                    rules={[{ required: true, message: t('selecioneCarreiraSecundaria') }]}
                                    style={{ marginBottom: 0 }}
                                  >
                                    <Select placeholder={t('selecioneCarreiraSecundaria')} size="small">
                                      {subCareers.map(career => (
                                        <Select.Option key={career.id} value={career.id}>
                                          {t('estagioMax', { name: career.name, max_stage: career.max_stage })}
                                        </Select.Option>
                                      ))}
                                    </Select>
                                  </Form.Item>
                                </Col>
                                <Col span={5}>
                                  <Form.Item
                                    {...field}
                                    name={[field.name, 'stage']}
                                    rules={[{ required: true, message: t('estagio') }]}
                                    style={{ marginBottom: 0 }}
                                  >
                                    <InputNumber
                                      min={1}
                                      max={(() => {
                                        const careerId = editForm.getFieldValue(['sub_career_data', field.name, 'career_id']);
                                        const career = subCareers.find(c => c.id === careerId);
                                        return career?.max_stage || 10;
                                      })()}
                                      placeholder={t('estagio')}
                                      style={{ width: '100%' }}
                                      size="small"
                                    />
                                  </Form.Item>
                                </Col>
                                <Col span={3}>
                                  <Button
                                    type="text"
                                    danger
                                    size="small"
                                    onClick={() => remove(field.name)}
                                  >
                                    {t('remover')}
                                  </Button>
                                </Col>
                              </Row>
                            ))}
                          </div>
                          <Button
                            type="dashed"
                            onClick={() => add({ career_id: undefined, stage: 1 })}
                            block
                            size="small"
                          >
                            {t('adicionarCarreiraSecundaria')}
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )}
                </>
              )}
            </>
          ) : (
            <>
              {/* 编辑组织 - 第一行：名称、类型、势力等级 */}
              <Row gutter={12}>
                <Col span={10}>
                  <Form.Item
                    label={t('nomeOrganizacao')}
                    name="name"
                    rules={[{ required: true, message: t('informeNomeOrganizacao') }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder={t('nomeOrganizacao')} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label={t('tipoOrganizacao')}
                    name="organization_type"
                    rules={[{ required: true, message: t('informeTipoOrganizacao') }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder={t('exSeitaGangue')} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    label={t('nivelInfluencia')}
                    name="power_level"
                    tooltip={t('valorZeroACem')}
                    style={{ marginBottom: 12 }}
                  >
                    <InputNumber min={0} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              {/* 第二行：组织目的 */}
              <Form.Item
                label={t('propositoOrganizacao')}
                name="organization_purpose"
                rules={[{ required: true, message: t('informePropositoOrganizacao') }]}
                style={{ marginBottom: 12 }}
              >
                <Input placeholder={t('descrevaMissaoObjetivosOrganizacao')} />
              </Form.Item>

              {/* 第三行：主要成员（只读展示） */}
              <Form.Item
                label={t('membrosPrincipais')}
                name="organization_members"
                style={{ marginBottom: 4 }}
                tooltip={t('informacoesMembrosSaoMantidas')}
              >
                <TextArea
                  disabled
                  autoSize={{ minRows: 1, maxRows: 4 }}
                  placeholder={t('nenhumMembroAindaAdicione')}
                  style={{ color: token.colorText, backgroundColor: token.colorFillAlter }}
                />
              </Form.Item>
              <div style={{ marginBottom: 12, fontSize: 12, color: token.colorTextTertiary }}>
                {t('acessePaginaOrganizacoesAdicionar')}
              </div>

              {/* 第四行：所在地、代表颜色 */}
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={t('localizacao')} name="location" style={{ marginBottom: 12 }}>
                    <Input placeholder={t('sede')} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={t('corRepresentativa')} name="color" style={{ marginBottom: 12 }}>
                    <Input placeholder={t('exDourado')} />
                  </Form.Item>
                </Col>
              </Row>

              {/* 第四行：格言/口号 */}
              <Form.Item label={t('lemaSlogan')} name="motto" style={{ marginBottom: 12 }}>
                <Input placeholder={t('missaoLemaSloganOrganizacao')} />
              </Form.Item>

              {/* 第五行：组织背景 */}
              <Form.Item label={t('historicoOrganizacao')} name="background" style={{ marginBottom: 12 }}>
                <TextArea rows={2} placeholder={t('descrevaHistoriaFundoOrganizacao')} />
              </Form.Item>
            </>
          )}
        </Form>
      </Modal>

      {/* 手动创建角色/组织模态框 */}
      <Modal
        title={createType === 'character' ? t('criarPersonagem') : t('criarOrganizacao')}
        open={isCreateModalOpen}
        onCancel={() => {
          setIsCreateModalOpen(false);
          createForm.resetFields();
        }}
        footer={null}
        centered
        width={isMobile ? '100%' : 700}
        style={isMobile ? { top: 0, paddingBottom: 0, maxWidth: '100vw' } : undefined}
        styles={{
          body: {
            maxHeight: isMobile ? 'calc(100vh - 110px)' : 'calc(100vh - 200px)',
            overflowY: 'auto',
            overflowX: 'hidden'
          }
        }}
      >
        <Form form={createForm} layout="vertical" onFinish={handleCreateCharacter} style={{ marginTop: 8 }}>
          {createType === 'character' ? (
            <>
              {/* 角色基本信息 - 第一行：名称、定位、年龄、性别 */}
              <Row gutter={12}>
                <Col span={8}>
                  <Form.Item
                    label={t('nomePersonagem')}
                    name="name"
                    rules={[{ required: true, message: t('informeNomePersonagem') }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder={t('nomePersonagem')} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item label={t('papelPersonagem')} name="role_type" initialValue="supporting" style={{ marginBottom: 12 }}>
                    <Select>
                      <Select.Option value="protagonist">{t('protagonista')}</Select.Option>
                      <Select.Option value="supporting">{t('coadjuvante')}</Select.Option>
                      <Select.Option value="antagonist">{t('antagonista')}</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
                <Col span={5}>
                  <Form.Item label={t('idade')} name="age" style={{ marginBottom: 12 }}>
                    <Input placeholder={t('ex25Anos')} />
                  </Form.Item>
                </Col>
                <Col span={5}>
                  <Form.Item label={t('genero')} name="gender" style={{ marginBottom: 12 }}>
                    <Select placeholder={t('genero')}>
                      <Select.Option value="masculino">{t('masculino')}</Select.Option>
                      <Select.Option value="feminino">{t('feminino')}</Select.Option>
                      <Select.Option value="outro">{t('outro')}</Select.Option>
                    </Select>
                  </Form.Item>
                </Col>
              </Row>

              {/* 第二行：性格特点、外貌描写 */}
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={t('personalidade')} name="personality" style={{ marginBottom: 12 }}>
                    <TextArea rows={2} placeholder={t('descrevaPersonalidadePersonagem')} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={t('aparencia')} name="appearance" style={{ marginBottom: 12 }}>
                    <TextArea rows={2} placeholder={t('descrevaCaracteristicasFisicasPersonagem')} />
                  </Form.Item>
                </Col>
              </Row>

              {/* 第三行：角色背景 */}
              <Form.Item label={t('historicoPersonagem')} name="background" style={{ marginBottom: 12 }}>
                <TextArea rows={2} placeholder={t('descrevaHistoriaFundoPersonagem')} />
              </Form.Item>

              {/* 职业信息 - 折叠区域 */}
              {(mainCareers.length > 0 || subCareers.length > 0) && (
                <>
                  <Divider style={{ margin: '8px 0' }}>
                    <Typography.Text type="secondary" style={{ fontSize: 12 }}>{t('informacoesCarreiraOpcional')}</Typography.Text>
                  </Divider>
                  {mainCareers.length > 0 && (
                    <Row gutter={12}>
                      <Col span={16}>
                        <Form.Item label={t('carreiraPrincipal')} name="main_career_id" tooltip={t('principalCarreiraDesenvolvimentoPersonagem')} style={{ marginBottom: 12 }}>
                          <Select placeholder={t('selecioneCarreiraPrincipal')} allowClear size="small">
                            {mainCareers.map(career => (
                              <Select.Option key={career.id} value={career.id}>
                                {t('estagioMax', { name: career.name, max_stage: career.max_stage })}
                              </Select.Option>
                            ))}
                          </Select>
                        </Form.Item>
                      </Col>
                      <Col span={8}>
                        <Form.Item label={t('estagioAtual')} name="main_career_stage" tooltip={t('estagioAtualCarreiraPrincipal')} style={{ marginBottom: 12 }}>
                          <InputNumber
                            min={1}
                            max={createForm.getFieldValue('main_career_id') ?
                              mainCareers.find(c => c.id === createForm.getFieldValue('main_career_id'))?.max_stage || 10
                              : 10}
                            style={{ width: '100%' }}
                            placeholder={t('estagio')}
                            size="small"
                          />
                        </Form.Item>
                      </Col>
                    </Row>
                  )}
                  {subCareers.length > 0 && (
                    <Form.List name="sub_career_data">
                      {(fields, { add, remove }) => (
                        <>
                          <div style={{ marginBottom: 4 }}>
                            <Typography.Text strong style={{ fontSize: 12 }}>{t('carreiraSecundaria')}</Typography.Text>
                          </div>
                          <div style={{ maxHeight: '80px', overflowY: 'auto', overflowX: 'hidden', marginBottom: 8, paddingRight: 8 }}>
                            {fields.map((field) => (
                              <Row key={field.key} gutter={8} style={{ marginBottom: 4 }}>
                                <Col span={16}>
                                  <Form.Item
                                    {...field}
                                    name={[field.name, 'career_id']}
                                    rules={[{ required: true, message: t('selecioneCarreiraSecundaria') }]}
                                    style={{ marginBottom: 0 }}
                                  >
                                    <Select placeholder={t('selecioneCarreiraSecundaria')} size="small">
                                      {subCareers.map(career => (
                                        <Select.Option key={career.id} value={career.id}>
                                          {t('estagioMax', { name: career.name, max_stage: career.max_stage })}
                                        </Select.Option>
                                      ))}
                                    </Select>
                                  </Form.Item>
                                </Col>
                                <Col span={5}>
                                  <Form.Item
                                    {...field}
                                    name={[field.name, 'stage']}
                                    rules={[{ required: true, message: t('estagio') }]}
                                    style={{ marginBottom: 0 }}
                                  >
                                    <InputNumber
                                      min={1}
                                      max={(() => {
                                        const careerId = createForm.getFieldValue(['sub_career_data', field.name, 'career_id']);
                                        const career = subCareers.find(c => c.id === careerId);
                                        return career?.max_stage || 10;
                                      })()}
                                      placeholder={t('estagio')}
                                      style={{ width: '100%' }}
                                      size="small"
                                    />
                                  </Form.Item>
                                </Col>
                                <Col span={3}>
                                  <Button
                                    type="text"
                                    danger
                                    size="small"
                                    onClick={() => remove(field.name)}
                                  >
                                    {t('remover')}
                                  </Button>
                                </Col>
                              </Row>
                            ))}
                          </div>
                          <Button
                            type="dashed"
                            onClick={() => add({ career_id: undefined, stage: 1 })}
                            block
                            size="small"
                          >
                            {t('adicionarCarreiraSecundaria')}
                          </Button>
                        </>
                      )}
                    </Form.List>
                  )}
                </>
              )}
            </>
          ) : (
            <>
              {/* 组织基本信息 - 第一行：名称、类型、势力等级 */}
              <Row gutter={12}>
                <Col span={10}>
                  <Form.Item
                    label={t('nomeOrganizacao')}
                    name="name"
                    rules={[{ required: true, message: t('informeNomeOrganizacao') }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder={t('nomeOrganizacao')} />
                  </Form.Item>
                </Col>
                <Col span={8}>
                  <Form.Item
                    label={t('tipoOrganizacao')}
                    name="organization_type"
                    rules={[{ required: true, message: t('informeTipoOrganizacao') }]}
                    style={{ marginBottom: 12 }}
                  >
                    <Input placeholder={t('exSeitaGangue')} />
                  </Form.Item>
                </Col>
                <Col span={6}>
                  <Form.Item
                    label={t('nivelInfluencia')}
                    name="power_level"
                    initialValue={50}
                    tooltip={t('valorZeroACem')}
                    style={{ marginBottom: 12 }}
                  >
                    <InputNumber min={0} max={100} style={{ width: '100%' }} />
                  </Form.Item>
                </Col>
              </Row>

              {/* 第二行：组织目的 */}
              <Form.Item
                label={t('propositoOrganizacao')}
                name="organization_purpose"
                rules={[{ required: true, message: t('informePropositoOrganizacao') }]}
                style={{ marginBottom: 12 }}
              >
                <Input placeholder={t('descrevaMissaoObjetivosOrganizacao')} />
              </Form.Item>

              {/* 第三行：所在地、代表颜色 */}
              <Row gutter={12}>
                <Col span={12}>
                  <Form.Item label={t('localizacao')} name="location" style={{ marginBottom: 12 }}>
                    <Input placeholder={t('sede')} />
                  </Form.Item>
                </Col>
                <Col span={12}>
                  <Form.Item label={t('corRepresentativa')} name="color" style={{ marginBottom: 12 }}>
                    <Input placeholder={t('exDourado')} />
                  </Form.Item>
                </Col>
              </Row>

              {/* 第四行：格言/口号 */}
              <Form.Item label={t('lemaSlogan')} name="motto" style={{ marginBottom: 12 }}>
                <Input placeholder={t('missaoLemaSloganOrganizacao')} />
              </Form.Item>

              {/* 第五行：组织背景 */}
              <Form.Item label={t('historicoOrganizacao')} name="background" style={{ marginBottom: 12 }}>
                <TextArea rows={2} placeholder={t('descrevaHistoriaFundoOrganizacao')} />
              </Form.Item>
            </>
          )}

          <Form.Item style={{ marginBottom: 0, marginTop: 16 }}>
            <Space style={{ width: '100%', justifyContent: 'flex-end' }}>
              <Button onClick={() => {
                setIsCreateModalOpen(false);
                createForm.resetFields();
              }}>
                {t('cancelar')}
              </Button>
              <Button type="primary" htmlType="submit">
                {t('criar')}
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Modal>

      {/* 导入对话框 */}
      <Modal
        title={t('importarPersonagensOrganizacoes')}
        open={isImportModalOpen}
        onCancel={() => setIsImportModalOpen(false)}
        footer={null}
        width={500}
        centered
      >
        <div style={{ textAlign: 'center', padding: '40px 20px' }}>
          <DownloadOutlined style={{ fontSize: 48, color: '#1890ff', marginBottom: 16 }} />
          <p style={{ fontSize: 16, marginBottom: 24 }}>
            {t('selecioneArquivoJsonPersonagens')}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            style={{ display: 'none' }}
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) {
                handleFileSelect(file);
                e.target.value = ''; // 清空input，允许重复选择同一文件
              }
            }}
          />
          <Button
            type="primary"
            size="large"
            icon={<ImportOutlined />}
            onClick={() => fileInputRef.current?.click()}
          >
            {t('selecionarArquivo')}
          </Button>
          <Divider />
          <div style={{ textAlign: 'left', fontSize: 12, color: '#666' }}>
            <p style={{ marginBottom: 8 }}><strong>{t('observacoes')}</strong></p>
            <ul style={{ marginLeft: 20 }}>
              <li>{t('saoAceitosArquivosFormato')}</li>
              <li>{t('personagensOrganizacoesNomeRepetido')}</li>
              <li>{t('informacoesCarreiraInexistentesSerao')}</li>
            </ul>
          </div>
        </div>
      </Modal>

      {/* SSE进度显示 */}
      <SSELoadingOverlay
        loading={isGenerating}
        progress={progress}
        message={progressMessage}
      />
    </div>
  );
}
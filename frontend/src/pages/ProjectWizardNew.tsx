import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Form, Input, InputNumber, Select, Button, Card,
  Row, Col, Typography, Space, message, Radio, theme
} from 'antd';
import {
  RocketOutlined, ArrowLeftOutlined, CheckCircleOutlined
} from '@ant-design/icons';
import { AIProjectGenerator, type GenerationConfig } from '../components/AIProjectGenerator';
import type { WizardBasicInfo } from '../types';
import { useTranslation } from 'react-i18next';
import {
  DEFAULT_LANGUAGE,
  DEFAULT_NARRATIVE_PERSPECTIVE,
  GENRE_OPTIONS,
  LANGUAGE_OPTIONS,
  NARRATIVE_PERSPECTIVE_OPTIONS,
  normalizePerspective,
} from '../constants/projectOptions';

const { TextArea } = Input;
const { Title, Paragraph } = Typography;

export default function ProjectWizardNew() {
  const { t } = useTranslation('projectWizard');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [form] = Form.useForm();
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const { token } = theme.useToken();

  // 状态管理
  const [currentStep, setCurrentStep] = useState<'form' | 'generating'>('form');
  const [generationConfig, setGenerationConfig] = useState<GenerationConfig | null>(null);
  const [resumeProjectId, setResumeProjectId] = useState<string | null>(null);
  const requestedProjectId = searchParams.get('project_id');

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // 检查URL参数,如果有project_id则恢复生成
  useEffect(() => {
    if (!requestedProjectId) return;

    const projectId = requestedProjectId;

    const controller = new AbortController();
    const startTimer = window.setTimeout(() => {
      if (controller.signal.aborted) return;

      setResumeProjectId(projectId);
      void handleResumeGeneration(projectId, controller.signal);
    }, 0);

    return () => {
      window.clearTimeout(startTimer);
      controller.abort();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [requestedProjectId]);

  // 恢复未完成项目的生成
  const handleResumeGeneration = async (projectId: string, signal?: AbortSignal) => {
    try {
      const response = await fetch(`/api/projects/${projectId}`, {
        credentials: 'include',
        signal,
      });
      if (!response.ok) {
        throw new Error(t('falhaAoObterAsInformacoes'));
      }
      const project = await response.json();

      const config: GenerationConfig = {
        title: project.title,
        description: project.description || '',
        theme: project.theme || '',
        genre: project.genre || '',
        narrative_perspective: normalizePerspective(project.narrative_perspective),
        language: project.language || DEFAULT_LANGUAGE,
        target_words: project.target_words || 100000,
        chapter_count: 3,
        character_count: project.character_count || 5,
      };

      setGenerationConfig(config);
      setCurrentStep('generating');
    } catch (error) {
      if (
        typeof error === 'object'
        && error !== null
        && 'name' in error
        && error.name === 'AbortError'
      ) {
        return;
      }

      console.error(t('falhaAoRetomarAGeracao'), error);
      message.error(t('falhaAoRetomarAGeracao2'));
      navigate('/');
    }
  };

  // 开始生成流程
  const handleAutoGenerate = async (values: WizardBasicInfo) => {
    const config: GenerationConfig = {
      title: values.title,
      description: values.description,
      theme: values.theme,
      genre: values.genre,
      narrative_perspective: values.narrative_perspective,
      language: values.language || DEFAULT_LANGUAGE,
      target_words: values.target_words || 100000,
      chapter_count: 3, // 默认生成3章大纲
      character_count: values.character_count || 5,
      outline_mode: values.outline_mode || 'one-to-many', // 添加大纲模式
    };

    setGenerationConfig(config);
    setCurrentStep('generating');
  };

  // 生成完成回调
  const handleComplete = (projectId: string) => {
    console.log(t('projetoCriado'), projectId);
  };

  // 返回表单页面
  const handleBack = () => {
    setCurrentStep('form');
    setGenerationConfig(null);
  };

  // 渲染表单页面
  const renderForm = () => (
    <Card>
      <Title level={isMobile ? 4 : 3} style={{ marginBottom: 24 }}>{t('criarNovoProjeto')}
      </Title>
      <Paragraph type="secondary" style={{ marginBottom: 32 }}>{t('depoisDePreencherAsInformacoes')}
      </Paragraph>

      <Form
        form={form}
        layout="vertical"
        onFinish={handleAutoGenerate}
        initialValues={{
          genre: [GENRE_OPTIONS[0]],
          chapter_count: 30,
          narrative_perspective: DEFAULT_NARRATIVE_PERSPECTIVE,
          language: DEFAULT_LANGUAGE,
          character_count: 5,
          target_words: 100000,
          outline_mode: 'one-to-one', // 默认为传统模式（1-1）
        }}
      >
        <Form.Item
          label={t('titulo')}
          name="title"
          rules={[{ required: true, message: t('digiteOTitulo') }]}
        >
          <Input placeholder={t('digiteOTituloDoSeu')} size="large" />
        </Form.Item>

        <Form.Item
          label={t('sinopse')}
          name="description"
          rules={[{ required: true, message: t('digiteASinopse') }]}
        >
          <TextArea
            rows={3}
            placeholder={t('apresenteOSeuLivroEm')}
            showCount
          />
        </Form.Item>

        <Form.Item
          label={t('tema')}
          name="theme"
          rules={[{ required: true, message: t('digiteOTema') }]}
        >
          <TextArea
            rows={4}
            placeholder={t('descrevaOTemaDoSeu')}
            showCount
          />
        </Form.Item>

        <Form.Item
          label={t('genero')}
          name="genre"
          rules={[{ required: true, message: t('selecioneOGeneroDoLivro') }]}
        >
          <Select
            mode="tags"
            placeholder={t('selecioneOuDigiteEtiquetasDe')}
            size="large"
            tokenSeparators={[',']}
            maxTagCount={5}
          >
            {GENRE_OPTIONS.map((genre) => (
              <Select.Option key={genre} value={genre}>{genre}</Select.Option>
            ))}
          </Select>
        </Form.Item>

        <Form.Item
          label={t('idiomaDoConteudo')}
          name="language"
          rules={[{ required: true, message: t('selecioneOIdiomaDoConteudo') }]}
          tooltip={t('idiomaDoConteudoDica')}
        >
          <Select size="large" options={LANGUAGE_OPTIONS} />
        </Form.Item>

        <Form.Item
          label={t('modoOutlineCapitulos')}
          name="outline_mode"
          rules={[{ required: true, message: t('selecioneOModoOutlineCapitulos') }]}
          tooltip={t('naoPodeSerAlteradoDepois')}
        >
          <Radio.Group size="large">
            <Row gutter={16}>
              <Col xs={24} sm={12}>
                <Card
                  hoverable
                  style={{
                    // borderColor: form.getFieldValue('outline_mode') === 'one-to-one' ? token.colorPrimary : token.colorBorder,
                    borderWidth: 2,
                    height: '100%',
                  }}
                  onClick={() => form.setFieldValue('outline_mode', 'one-to-one')}
                >
                  <Radio value="one-to-one" style={{ width: '100%' }}>
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                        <CheckCircleOutlined style={{ marginRight: 8, color: token.colorSuccess }} />{t('modoTradicional11')}
                      </div>
                      <div style={{ fontSize: 12, color: token.colorTextSecondary }}>{t('cadaItemDoOutlineCorresponde')}
                      </div>
                      <div style={{ fontSize: 11, color: token.colorTextTertiary }}>{t('indicadoParaEnredosSimplesCriacao')}
                      </div>
                    </Space>
                  </Radio>
                </Card>
              </Col>

              <Col xs={24} sm={12}>
                <Card
                  hoverable
                  style={{
                    // borderColor: form.getFieldValue('outline_mode') === 'one-to-many' ? token.colorPrimary : token.colorBorder,
                    borderWidth: 2,
                    height: '100%',
                  }}
                  onClick={() => form.setFieldValue('outline_mode', 'one-to-many')}
                >
                  <Radio value="one-to-many" style={{ width: '100%' }}>
                    <Space direction="vertical" size={4} style={{ width: '100%' }}>
                      <div style={{ fontSize: 16, fontWeight: 'bold' }}>
                        <CheckCircleOutlined style={{ marginRight: 8, color: token.colorSuccess }} />{t('modoDetalhado1NRecomendado')}
                      </div>
                      <div style={{ fontSize: 12, color: token.colorTextSecondary }}>{t('cadaItemDoOutlinePode')}
                      </div>
                      <div style={{ fontSize: 11, color: token.colorTextTertiary }}>{t('indicadoParaEnredosComplexosObras')}
                      </div>
                    </Space>
                  </Radio>
                </Card>
              </Col>
            </Row>
          </Radio.Group>
        </Form.Item>

        <Row gutter={16}>
          <Col xs={24} sm={12}>
            <Form.Item
              label={t('perspectivaNarrativa')}
              name="narrative_perspective"
              rules={[{ required: true, message: t('selecioneAPerspectivaNarrativa') }]}
            >
              <Select size="large" placeholder={t('selecioneAPerspectivaNarrativaDo')}>
                {NARRATIVE_PERSPECTIVE_OPTIONS.map((option) => (
                  <Select.Option key={option.value} value={option.value}>{option.label}</Select.Option>
                ))}
              </Select>
            </Form.Item>
          </Col>
          <Col xs={24} sm={12}>
            <Form.Item
              label={t('quantidadeDePersonagens')}
              name="character_count"
              rules={[{ required: true, message: t('digiteAQuantidadeDePersonagens') }]}
            >
              <InputNumber
                min={3}
                max={20}
                style={{ width: '100%' }}
                size="large"
                addonAfter={t('personagens')}
                placeholder={t('quantidadeDePersonagensGeradosPela')}
              />
            </Form.Item>
          </Col>
        </Row>

        <Form.Item
          label={t('metaDePalavras')}
          name="target_words"
          rules={[{ required: true, message: t('digiteAMetaDePalavras') }]}
        >
          <InputNumber
            min={10000}
            style={{ width: '100%' }}
            size="large"
            addonAfter={t('palavras')}
            placeholder={t('metaDePalavrasDoLivro')}
          />
        </Form.Item>

        <Form.Item>
          <Space direction="vertical" style={{ width: '100%' }} size={12}>
            <Button
              type="primary"
              htmlType="submit"
              size="large"
              block
              icon={<RocketOutlined />}
            >{t('comecarACriarOProjeto')}
            </Button>
            <Button
              size="large"
              block
              onClick={() => navigate('/')}
            >{t('voltarAoInicio')}
            </Button>
          </Space>
        </Form.Item>
      </Form>
    </Card>
  );

  return (
    <div style={{
      minHeight: '100dvh',
      background: token.colorBgBase,
    }}>
      {/* 顶部标题栏 - 固定不滚动 */}
      <div style={{
        position: 'sticky',
        top: 0,
        zIndex: 100,
        background: token.colorPrimary,
        boxShadow: `0 6px 20px color-mix(in srgb, ${token.colorPrimary} 30%, transparent)`,
      }}>
        <div style={{
          maxWidth: 1200,
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          padding: isMobile ? '12px 16px' : '16px 24px',
        }}>
          <Button
            icon={<ArrowLeftOutlined />}
            onClick={() => navigate('/')}
            size={isMobile ? 'middle' : 'large'}
            disabled={currentStep === 'generating'}
            style={{
              background: `color-mix(in srgb, ${token.colorWhite} 20%, transparent)`,
              borderColor: `color-mix(in srgb, ${token.colorWhite} 30%, transparent)`,
              color: token.colorWhite,
            }}
          >
            {isMobile ? t('voltar') : t('voltarAoInicio')}
          </Button>

          <Title level={isMobile ? 4 : 2} style={{
            margin: 0,
            color: token.colorWhite,
            textShadow: '0 2px 4px color-mix(in srgb, var(--ant-color-black) 18%, transparent)',
          }}>
            <RocketOutlined style={{ marginRight: 8 }} />{t('assistenteDeCriacaoDeProjeto')}
          </Title>

          <div style={{ width: isMobile ? 60 : 120 }}></div>
        </div>
      </div>

      {/* 内容区域 */}
      <div style={{
        maxWidth: 800,
        margin: '0 auto',
        padding: isMobile ? '8px 12px 12px' : '12px 20px 16px',
      }}>
        {currentStep === 'form' && renderForm()}
        {currentStep === 'generating' && generationConfig && (
          <AIProjectGenerator
            config={generationConfig}
            storagePrefix="wizard"
            onComplete={handleComplete}
            onBack={handleBack}
            isMobile={isMobile}
            resumeProjectId={resumeProjectId || undefined}
          />
        )}
      </div>
    </div>
  );
}

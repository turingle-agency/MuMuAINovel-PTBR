import { useCallback, useEffect, useMemo, useState } from 'react';
import {
  Button,
  Card,
  Col,
  Empty,
  Flex,
  Input,
  InputNumber,
  List,
  Row,
  Space,
  Spin,
  Statistic,
  Switch,
  Tag,
  Typography,
  Upload,
  message,
  theme,
} from 'antd';
import {
  DatabaseOutlined,
  DeleteOutlined,
  InboxOutlined,
  ReloadOutlined,
  SearchOutlined,
} from '@ant-design/icons';
import { useParams } from 'react-router-dom';
import type { UploadProps } from 'antd';
import { knowledgeApi } from '../services/api';
import type { KnowledgeBase, KnowledgeDocument, KnowledgeSearchHit } from '../types';
import './KnowledgeBase.css';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

const { Dragger } = Upload;
const { Text, Paragraph, Title } = Typography;

const statusMap: Record<string, { label: string; color: string }> = {
  pending: { label: i18n.t('knowledgeBase:aguardandoProcessamento'), color: 'default' },
  parsing: { label: i18n.t('knowledgeBase:analisando'), color: 'processing' },
  embedding: { label: i18n.t('knowledgeBase:gerandoVetores'), color: 'processing' },
  ready: { label: i18n.t('knowledgeBase:concluido'), color: 'success' },
  failed: { label: i18n.t('knowledgeBase:falhaNoProcessamento'), color: 'error' },
};

const parseHeadingPath = (value: unknown): string => {
  if (Array.isArray(value)) return value.map(String).filter(Boolean).join(' / ');
  if (!value) return '';
  try {
    const parsed = JSON.parse(String(value));
    return Array.isArray(parsed) ? parsed.map(String).filter(Boolean).join(' / ') : String(value);
  } catch {
    return String(value);
  }
};

export default function KnowledgeBasePage() {
  const { t } = useTranslation('knowledgeBase');
  const { projectId } = useParams<{ projectId: string }>();
  const { token } = theme.useToken();
  const [base, setBase] = useState<KnowledgeBase | null>(null);
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [query, setQuery] = useState('');
  const [hits, setHits] = useState<KnowledgeSearchHit[]>([]);
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [retrievalEnabled, setRetrievalEnabled] = useState(true);
  const [topK, setTopK] = useState(8);
  const [minScore, setMinScore] = useState(0.25);
  const [maxContextChars, setMaxContextChars] = useState(6000);
  const [savingSettings, setSavingSettings] = useState(false);

  const load = useCallback(async () => {
    if (!projectId) return;
    setLoading(true);
    try {
      const bases = await knowledgeApi.listBases(projectId);
      let current = bases.items[0];
      if (!current) {
        current = (await knowledgeApi.createBase(projectId, {
          name: t('baseConhecimentoProjeto'),
          description: t('guardaMateriaisReferenciaDocumentos'),
        })).item;
      }
      setBase(current);
      setRetrievalEnabled(current.settings?.retrieval_enabled ?? true);
      setTopK(current.settings?.top_k ?? 8);
      setMinScore(current.settings?.min_score ?? 0.25);
      setMaxContextChars(current.settings?.max_context_chars ?? 6000);
      setDocuments((await knowledgeApi.listDocuments(current.id)).items);
    } catch (error) {
      console.error('Falha ao carregar a base de conhecimento', error);
      message.error(t('falhaCarregarBaseConhecimento'));
    } finally {
      setLoading(false);
    }
  }, [projectId, t]);

  useEffect(() => { void load(); }, [load]);

  useEffect(() => {
    if (!documents.some((item) => ['pending', 'parsing', 'embedding'].includes(item.status))) return;
    const timer = window.setInterval(() => { void load(); }, 2500);
    return () => window.clearInterval(timer);
  }, [documents, load]);

  const uploadProps: UploadProps = useMemo(() => ({
    multiple: true,
    accept: '.txt,.md,.markdown,.json',
    showUploadList: false,
    beforeUpload: async (file) => {
      if (!base) return false;
      try {
        await knowledgeApi.uploadDocument(base.id, file);
        message.success(t('foiAdicionadoFilaIndexacao', { name: file.name }));
        await load();
      } catch (error) {
        console.error('Falha ao enviar o documento para a base de conhecimento', error);
        message.error(error instanceof Error ? error.message : t('falhaEnvioVerifiqueFormato'));
      }
      return false;
    },
  }), [base, load, t]);

  const saveRetrievalSettings = async () => {
    if (!base) return;
    setSavingSettings(true);
    try {
      const response = await knowledgeApi.updateBase(base.id, {
        settings: {
          retrieval_enabled: retrievalEnabled,
          top_k: topK,
          min_score: minScore,
          max_context_chars: maxContextChars,
        },
      });
      setBase(response.item);
      message.success(t('parametrosBuscaSalvos'));
    } catch (error) {
      console.error('Falha ao salvar os parâmetros de busca', error);
      message.error(t('falhaSalvarParametrosBusca'));
    } finally {
      setSavingSettings(false);
    }
  };

  const handleSearch = async () => {
    if (!base || !query.trim()) return;
    setSearching(true);
    try {
      setHits((await knowledgeApi.search(base.id, { query: query.trim(), top_k: topK, min_score: minScore })).items);
    } catch (error) {
      console.error('Falha ao buscar na base de conhecimento', error);
      message.error(t('falhaBuscaTenteNovamente'));
    } finally {
      setSearching(false);
    }
  };

  const remove = async (document: KnowledgeDocument) => {
    try {
      await knowledgeApi.deleteDocument(document.id);
      message.success(t('documentoExcluido'));
      await load();
    } catch (error) {
      console.error('Falha ao excluir o documento da base de conhecimento', error);
      message.error(t('falhaExcluirTenteNovamente'));
    }
  };

  const reindex = async (document: KnowledgeDocument) => {
    try {
      await knowledgeApi.reindexDocument(document.id);
      message.success(t('reenviadoFilaIndexacao'));
      await load();
    } catch (error) {
      console.error('Falha ao reconstruir o índice da base de conhecimento', error);
      message.error(t('falhaReconstruirIndiceTente'));
    }
  };

  if (loading && !base) {
    return <Spin size="large" style={{ display: 'block', margin: '80px auto' }} />;
  }

  return (
    <div className="knowledge-base-page">
      <div
        style={{
          backgroundColor: token.colorBgContainer,
          borderBottom: `1px solid ${token.colorBorderSecondary}`,
          flexShrink: 0,
        }}
      >
        <Flex justify="space-between" align="flex-start" gap={16} wrap="wrap">
          <Flex align="center" gap={12} style={{ minWidth: 0 }}>
            <DatabaseOutlined style={{ fontSize: 26, color: token.colorPrimary, flexShrink: 0 }} />
            <div style={{ minWidth: 0 }}>
              <Title level={2} style={{ margin: 0, lineHeight: 1.2 }}>
                {base?.name || t('baseConhecimentoLocal')}
              </Title>
              <Text type="secondary">
                {t('envieMateriaisReferenciaProjeto')}
              </Text>
            </div>
          </Flex>
          <Button icon={<ReloadOutlined />} loading={loading} onClick={() => void load()}>
            {t('atualizar')}
          </Button>
        </Flex>
      </div>

      <div className="knowledge-base-main">
        {base && (
          <Card size="small" className="knowledge-base-summary">
            <Row gutter={[16, 12]}>
              <Col xs={12} sm={8}>
                <Statistic title={t('numeroDeDocumentos')} value={base.document_count} suffix={t('docs')} />
              </Col>
              <Col xs={12} sm={8}>
                <Statistic title={t('blocosDeTexto')} value={base.chunk_count} suffix={t('blocos')} />
              </Col>
              <Col xs={24} sm={8}>
                <Statistic title={t('metodoDeIndexacao')} value={t('vetorLocal')} valueStyle={{ fontSize: 20, color: token.colorPrimary }} />
              </Col>
            </Row>
          </Card>
        )}

        <div className="knowledge-base-panels">
          <div className="knowledge-base-panel">
            <Card
              className="knowledge-base-panel-card"
              title={<Space><InboxOutlined />{t('gerenciamentoDeDocumentos')}<Tag>{documents.length}</Tag></Space>}
              extra={<Button type="text" icon={<ReloadOutlined />} loading={loading} onClick={() => void load()} />}
            >
              <Dragger {...uploadProps} style={{ marginBottom: 18 }}>
                <p className="ant-upload-drag-icon"><InboxOutlined /></p>
                <p className="ant-upload-text">{t('cliqueOuArrasteArquivos')}</p>
                <p className="ant-upload-hint">{t('aceitaEnvioLoteTamanho')}</p>
              </Dragger>
              <List
                className="knowledge-base-document-list"
                dataSource={documents}
                split
                locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('aindaNaoHaDocumentos')} /> }}
                renderItem={(document) => {
                  const status = statusMap[document.status] || statusMap.pending;
                  return (
                    <List.Item
                      actions={[
                        document.status === 'failed' || document.status === 'ready'
                          ? <Button key="reindex" type="link" size="small" onClick={() => void reindex(document)}>{t('reconstruirIndice')}</Button>
                          : null,
                        <Button key="delete" type="text" danger icon={<DeleteOutlined />} onClick={() => void remove(document)} />,
                      ].filter(Boolean)}
                    >
                      <List.Item.Meta
                        title={<Space wrap>{document.title}<Tag color={status.color}>{status.label}</Tag></Space>}
                        description={(
                          <Space direction="vertical" size={0}>
                            <Text type="secondary">{document.original_filename}</Text>
                            <Text type="secondary">
                              {t('blocosTextoCaracteres', { chunk_count: document.chunk_count, extracted_char_count: document.extracted_char_count.toLocaleString() })}
                            </Text>
                            {document.error_message && <Text type="danger">{document.error_message}</Text>}
                          </Space>
                        )}
                      />
                    </List.Item>
                  );
                }}
              />
            </Card>
          </div>

          <div className="knowledge-base-panel">
            <Card
              className="knowledge-base-panel-card"
              title={<Space><SearchOutlined />{t('buscaDeConhecimento')}</Space>}
            >
              <Flex gap={8} wrap="wrap" align="center" style={{ marginBottom: 12 }}>
                <Text type="secondary">{t('injecaoAutomatica')}</Text>
                <Switch size="small" checked={retrievalEnabled} onChange={setRetrievalEnabled} />
                <Text type="secondary">{t('quantidadeRecuperada')}</Text>
                <InputNumber min={1} max={30} value={topK} onChange={(value) => setTopK(value ?? 8)} />
                <Text type="secondary">{t('similaridadeMinima')}</Text>
                <InputNumber min={0} max={1} step={0.05} precision={2} value={minScore} onChange={(value) => setMinScore(value ?? 0.25)} />
                <Text type="secondary">{t('limiteDeContexto')}</Text>
                <InputNumber min={1000} max={20000} step={500} value={maxContextChars} onChange={(value) => setMaxContextChars(value ?? 6000)} />
                <Button size="small" loading={savingSettings} onClick={() => void saveRetrievalSettings()}>{t('salvarParametros')}</Button>
              </Flex>
              <Input.Search
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                onSearch={() => void handleSearch()}
                loading={searching}
                enterButton={t('buscar')}
                placeholder={t('exQuaisRegrasProtagonista')}
                size="large"
              />
              <List
                className="knowledge-base-search-list"
                itemLayout="vertical"
                dataSource={hits}
                locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={query ? t('nenhumResultadoCorrespondente') : t('digitePerguntaBuscar')} /> }}
                renderItem={(hit) => {
                  const metadata = hit.metadata || {};
                  const heading = parseHeadingPath(metadata.heading_path);
                  return (
                    <List.Item style={{ paddingInline: 0 }}>
                      <div
                        style={{
                          width: '100%',
                          padding: 14,
                          background: token.colorFillAlter,
                          border: `1px solid ${token.colorBorderSecondary}`,
                          borderRadius: token.borderRadius,
                        }}
                      >
                        <Flex gap={8} wrap="wrap" align="center" style={{ marginBottom: 8 }}>
                          <Tag color="blue">{t('similaridade', { valor: (hit.score * 100).toFixed(0) })}</Tag>
                          <Text strong>{metadata.original_filename || metadata.title || t('documentoBaseConhecimento')}</Text>
                          {heading && <Text type="secondary">{heading}</Text>}
                        </Flex>
                        <Paragraph style={{ marginBottom: 0, whiteSpace: 'pre-wrap' }}>{hit.content}</Paragraph>
                      </div>
                    </List.Item>
                  );
                }}
              />
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

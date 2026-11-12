import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Button,
  Card,
  Col,
  Collapse,
  Empty,
  Input,
  InputNumber,
  List,
  message,
  Popconfirm,
  Progress,
  Row,
  Select,
  Space,
  Spin,
  Steps,
  Tag,
  Typography,
  Upload,
  theme,
} from 'antd';
import type { UploadFile } from 'antd/es/upload/interface';
import { InboxOutlined, PlayCircleOutlined, ReloadOutlined, StopOutlined, WarningOutlined, RedoOutlined } from '@ant-design/icons';
import { bookImportApi } from '../services/api';
import type {
  BookImportApplyPayload,
  BookImportExtractMode,
  BookImportPreview,
  BookImportStepFailure,
  BookImportTask,
} from '../types';
import { useTranslation } from 'react-i18next';
import i18n from '../i18n';

const { Text, Title } = Typography;
const { Dragger } = Upload;
const { TextArea } = Input;

const BOOK_IMPORT_CACHE_KEY = 'book_import_page_cache_v1';

type BookImportPageCache = {
  taskId: string | null;
  taskStatus: BookImportTask | null;
  preview: BookImportPreview | null;
  applyProgress: number;
  applyMessage: string;
  applyError: string | null;
  isApplyComplete: boolean;
  extractMode: BookImportExtractMode;
  tailChapterCount: number;
  cachedAt: number;
};

function loadBookImportCache(): BookImportPageCache | null {
  try {
    const raw = sessionStorage.getItem(BOOK_IMPORT_CACHE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as BookImportPageCache;
  } catch (error) {
    console.warn(i18n.t('bookImport:falhaLerCachePagina'), error);
    return null;
  }
}

function saveBookImportCache(cache: BookImportPageCache) {
  try {
    sessionStorage.setItem(BOOK_IMPORT_CACHE_KEY, JSON.stringify(cache));
  } catch (error) {
    const isQuotaExceeded =
      error instanceof DOMException &&
      (error.name === 'QuotaExceededError' || error.name === 'NS_ERROR_DOM_QUOTA_REACHED');

    if (isQuotaExceeded) {
      // 发生容量溢出时降级为轻量缓存（不保存预览正文），避免持续报错
      try {
        const lightweightCache: BookImportPageCache = {
          ...cache,
          preview: null,
        };
        sessionStorage.setItem(BOOK_IMPORT_CACHE_KEY, JSON.stringify(lightweightCache));
        return;
      } catch (fallbackError) {
        console.warn(i18n.t('bookImport:falhaGravarCacheLeve'), fallbackError);
        try {
          sessionStorage.removeItem(BOOK_IMPORT_CACHE_KEY);
        } catch {
          // ignore
        }
      }
    }

    console.warn(i18n.t('bookImport:falhaGravarCachePagina'), error);
  }
}

function clearBookImportCache() {
  try {
    sessionStorage.removeItem(BOOK_IMPORT_CACHE_KEY);
  } catch (error) {
    console.warn(i18n.t('bookImport:falhaLimparCachePagina'), error);
  }
}

function isNotFoundError(error: unknown): boolean {
  if (!error || typeof error !== 'object') return false;
  const maybeError = error as { response?: { status?: number } };
  return maybeError.response?.status === 404;
}

export default function BookImport() {
  const { t } = useTranslation('bookImport');
  const navigate = useNavigate();
  const { token } = theme.useToken();
  const isMobile = window.innerWidth <= 768;
  const [file, setFile] = useState<File | null>(null);
  const [extractMode, setExtractMode] = useState<BookImportExtractMode>('tail');
  const [tailChapterCount, setTailChapterCount] = useState(10);

  const [taskId, setTaskId] = useState<string | null>(null);
  const [taskStatus, setTaskStatus] = useState<BookImportTask | null>(null);
  const [preview, setPreview] = useState<BookImportPreview | null>(null);

  const [creatingTask, setCreatingTask] = useState(false);
  const [loadingPreview, setLoadingPreview] = useState(false);
  const [applying, setApplying] = useState(false);
  const [applyProgress, setApplyProgress] = useState(0);
  const [applyMessage, setApplyMessage] = useState('');
  const [applyError, setApplyError] = useState<string | null>(null);
  const [isApplyComplete, setIsApplyComplete] = useState(false);
  const [cacheReady, setCacheReady] = useState(false);

  // 步骤级失败和重试相关状态
  const [failedSteps, setFailedSteps] = useState<BookImportStepFailure[]>([]);
  const [retrying, setRetrying] = useState(false);
  const [retryProgress, setRetryProgress] = useState(0);
  const [retryMessage, setRetryMessage] = useState('');
  const importedProjectId = useRef<string | null>(null);

  const isTaskTerminal = useMemo(() => {
    return !!taskStatus && ['completed', 'failed', 'cancelled'].includes(taskStatus.status);
  }, [taskStatus]);

  const currentStep = useMemo(() => {
    if (!taskId) return 0;
    if (taskStatus && ['pending', 'running'].includes(taskStatus.status)) return 1;
    if (applying || isApplyComplete) return 3; // 新增生成导入步骤
    if (preview) return 2;
    return 1;
  }, [taskId, taskStatus, preview, applying, isApplyComplete]);

  const canRestart = useMemo(() => {
    return Boolean(
      file ||
      taskId ||
      taskStatus ||
      preview ||
      applyProgress > 0 ||
      applyMessage ||
      applyError ||
      isApplyComplete ||
      failedSteps.length > 0 ||
      retrying
    );
  }, [
    file,
    taskId,
    taskStatus,
    preview,
    applyProgress,
    applyMessage,
    applyError,
    isApplyComplete,
    failedSteps,
    retrying,
  ]);

  const normalizedTailChapterCount = useMemo(
    () => Math.max(5, Math.ceil(tailChapterCount / 5) * 5),
    [tailChapterCount]
  );
  const effectiveExtractMode = useMemo<BookImportExtractMode>(
    () => (normalizedTailChapterCount > 50 ? 'full' : extractMode),
    [extractMode, normalizedTailChapterCount]
  );
  const rangeLocked = Boolean(taskId || taskStatus || preview || creatingTask || applying || retrying);

  const stepItems = [
    { title: t('enviarArquivo') },
    { title: t('analisando') },
    { title: t('revisarPrevia') },
    { title: t('gerarImportar') },
  ];
  const currentStepText = stepItems[currentStep]?.title || t('enviarArquivo');

  useEffect(() => {
    const cache = loadBookImportCache();
    if (cache) {
      const cacheAgeMs = typeof cache.cachedAt === 'number'
        ? Date.now() - cache.cachedAt
        : Number.POSITIVE_INFINITY;

      // 超过6小时的缓存直接视为失效，避免后端重启后继续使用旧taskId
      if (cacheAgeMs > 6 * 60 * 60 * 1000) {
        clearBookImportCache();
      } else {
        setTaskId(cache.taskId);
        setTaskStatus(cache.taskStatus);
        setPreview(cache.preview);
        setApplyProgress(cache.applyProgress);
        setApplyError(cache.applyError);
        setIsApplyComplete(cache.isApplyComplete);
        setExtractMode(cache.extractMode ?? 'tail');
        setTailChapterCount(cache.tailChapterCount ?? 10);
        setApplyMessage(
          cache.applyMessage || (cache.applyProgress > 0 && !cache.isApplyComplete
            ? t('cachePaginaRestauradoClique')
            : '')
        );
        message.info(t('cachePaginaImportacaoRestaurado'));
      }
    }
    setCacheReady(true);
  }, [t]);

  useEffect(() => {
    if (!cacheReady) return;

    // 导入完成后必须清理缓存，避免后续回到页面时恢复到旧任务状态
    if (isApplyComplete) {
      clearBookImportCache();
      return;
    }

    const hasCacheData = Boolean(
      taskId ||
      taskStatus ||
      preview ||
      applyError ||
      applyProgress > 0 ||
      applyMessage
    );

    if (!hasCacheData) {
      clearBookImportCache();
      return;
    }

    saveBookImportCache({
      taskId,
      taskStatus,
      // preview 含完整章节正文，体积大，容易触发 sessionStorage 配额限制
      // 页面恢复时可根据 taskId + taskStatus 重新拉取 preview
      preview: null,
      applyProgress,
      applyMessage,
      applyError,
      isApplyComplete,
      extractMode,
      tailChapterCount,
      cachedAt: Date.now(),
    });
  }, [
    cacheReady,
    taskId,
    taskStatus,
    preview,
    applyProgress,
    applyMessage,
    applyError,
    isApplyComplete,
    extractMode,
    tailChapterCount,
  ]);

  useEffect(() => {
    if (!taskId) return;
    if (isTaskTerminal) return;

    const timer = setInterval(async () => {
      try {
        const status = await bookImportApi.getTaskStatus(taskId);
        setTaskStatus(status);
      } catch (error) {
        console.error(t('falhaConsultarStatusTarefa'), error);
        if (isNotFoundError(error)) {
          clearBookImportCache();
          setTaskId(null);
          setTaskStatus(null);
          setPreview(null);
          setApplyProgress(0);
          setApplyMessage('');
          setApplyError(null);
          setIsApplyComplete(false);
          message.warning(t('tarefaImportacaoExpirouPossivelmente'));
        }
      }
    }, 1500);

    return () => clearInterval(timer);
  }, [taskId, isTaskTerminal, t]);

  useEffect(() => {
    const fetchPreview = async () => {
      if (!taskId || !taskStatus) return;
      if (taskStatus.status !== 'completed' || preview) return;

      try {
        setLoadingPreview(true);
        const data = await bookImportApi.getPreview(taskId);
        setPreview(data);
      } catch (error) {
        console.error(t('falhaObterPrevia'), error);
        if (isNotFoundError(error)) {
          clearBookImportCache();
          setTaskId(null);
          setTaskStatus(null);
          setPreview(null);
          setApplyProgress(0);
          setApplyMessage('');
          setApplyError(null);
          setIsApplyComplete(false);
          message.warning(t('previaTarefaNaoExiste'));
        } else {
          message.error(t('falhaObterPreviaToast'));
        }
      } finally {
        setLoadingPreview(false);
      }
    };

    fetchPreview();
  }, [taskId, taskStatus, preview, t]);

  const startTask = async () => {
    if (!file) {
      message.warning(t('selecionePrimeiroArquivoTxt'));
      return;
    }

    try {
      setCreatingTask(true);
      setPreview(null);
      setTaskStatus(null);

      setExtractMode(effectiveExtractMode);
      setTailChapterCount(normalizedTailChapterCount);

      const response = await bookImportApi.createTask({
        file,
        extract_mode: effectiveExtractMode,
        tail_chapter_count: normalizedTailChapterCount,
      });

      setTaskId(response.task_id);
      message.success(t('tarefaImportacaoCriada'));
    } catch (error) {
      console.error(t('falhaCriarTarefa'), error);
      message.error(t('falhaCriarTarefaImportacao'));
    } finally {
      setCreatingTask(false);
    }
  };

  const refreshStatus = async () => {
    if (!taskId) return;
    try {
      const status = await bookImportApi.getTaskStatus(taskId);
      setTaskStatus(status);
    } catch (error) {
      console.error(t('falhaAtualizarStatus'), error);
      if (isNotFoundError(error)) {
        clearBookImportCache();
        setTaskId(null);
        setTaskStatus(null);
        setPreview(null);
        setApplyProgress(0);
        setApplyMessage('');
        setApplyError(null);
        setIsApplyComplete(false);
        message.warning(t('tarefaNaoExisteCache'));
      }
    }
  };

  const cancelTask = async () => {
    if (!taskId) return;
    try {
      await bookImportApi.cancelTask(taskId);
      message.success(t('tarefaCancelada'));
      await refreshStatus();
    } catch (error) {
      console.error(t('falhaCancelarTarefa'), error);
      message.error(t('falhaCancelarTarefaToast'));
    }
  };

  const applyImport = async () => {
    if (!taskId || !preview) return;

    const payload: BookImportApplyPayload = {
      project_suggestion: preview.project_suggestion,
      chapters: preview.chapters,
      outlines: preview.outlines,
      import_mode: 'append',
    };

    try {
      setApplying(true);
      setApplyProgress(0);
      setApplyMessage(t('preparandoImportacao'));
      setApplyError(null);
      setIsApplyComplete(false);
      setFailedSteps([]);

      await bookImportApi.applyImportStream(
        taskId,
        payload,
        {
          onProgress: (msg, prog, status) => {
            // 检查是否是步骤失败的特殊消息
            if (status === 'step_failures') {
              try {
                const parsed = JSON.parse(msg);
                if (parsed.failed_steps && Array.isArray(parsed.failed_steps)) {
                  setFailedSteps(parsed.failed_steps as BookImportStepFailure[]);
                }
              } catch {
                // 不是JSON，忽略
              }
              return;
            }
            setApplyProgress(prog);
            setApplyMessage(msg);
          },
          onResult: (result) => {
            importedProjectId.current = result.project_id;
            const generatedCareers = result.statistics?.generated_careers ?? 0;
            const generatedEntities = result.statistics?.generated_entities ?? 0;

            // 检查最终是否有失败步骤
            setIsApplyComplete(true);

            // 如果没有失败步骤才自动跳转
            // 注意：这里需要延迟一帧来等待 failedSteps 的更新
            setTimeout(() => {
              setFailedSteps(prev => {
                if (prev.length === 0) {
                  message.success(t('importacaoConcluidaCarreiraS', { generatedCareers, generatedEntities }));
                  clearBookImportCache();
                  setTimeout(() => {
                    navigate(`/project/${result.project_id}/chapters`);
                  }, 1000);
                } else {
                  message.warning(t('importacaoConcluidaMasEtapa', { length: prev.length }));
                }
                return prev;
              });
            }, 100);
          },
          onError: (error) => {
            console.error(t('erroDuranteImportacao'), error);
            setApplyError(t('falhaImportacao', { error }));
            message.error(t('falhaImportacao', { error }));
            setApplying(false);
          },
          onComplete: () => {
            setApplyProgress(100);
            setApplyMessage(t('importacaoConcluida'));
          }
        }
      );
    } catch (error) {
      console.error(t('falhaConfirmarImportacao'), error);
      setApplyError(t('falhaConfirmarImportacaoNao'));
      message.error(t('falhaConfirmarImportacaoToast'));
      setApplying(false);
    }
  };

  const retryFailedSteps = useCallback(async () => {
    if (!taskId || failedSteps.length === 0) return;

    const stepsToRetry = failedSteps.map(f => f.step_name);

    try {
      setRetrying(true);
      setRetryProgress(0);
      setRetryMessage(t('tentandoNovamenteEtapasGeracao'));

      await bookImportApi.retryFailedStepsStream(
        taskId,
        stepsToRetry,
        {
          onProgress: (msg, prog, status) => {
            if (status === 'step_failures') {
              try {
                const parsed = JSON.parse(msg);
                if (parsed.failed_steps && Array.isArray(parsed.failed_steps)) {
                  setFailedSteps(parsed.failed_steps as BookImportStepFailure[]);
                }
              } catch {
                // 不是JSON，忽略
              }
              return;
            }
            setRetryProgress(prog);
            setRetryMessage(msg);
          },
          onResult: (result) => {
            if (result.still_failed && result.still_failed.length > 0) {
              setFailedSteps(result.still_failed);
              message.warning(t('novaTentativaConcluidaMas', { length: result.still_failed.length }));
            } else {
              setFailedSteps([]);
              message.success(t('todasEtapasForamRefeitas'));
              clearBookImportCache();
              const projectId = result.project_id || importedProjectId.current;
              if (projectId) {
                setTimeout(() => {
                  navigate(`/project/${projectId}/chapters`);
                }, 1000);
              }
            }
          },
          onError: (error) => {
            console.error(t('falhaNovaTentativa'), error);
            message.error(t('falhaNovaTentativaComErro', { error }));
          },
          onComplete: () => {
            setRetrying(false);
            setRetryProgress(100);
            setRetryMessage(t('novaTentativaConcluida'));
          }
        }
      );
    } catch (error) {
      console.error(t('falhaRequisicaoNovaTentativa'), error);
      message.error(t('falhaRequisicaoNovaTentativaNao'));
      setRetrying(false);
    }
  }, [taskId, failedSteps, navigate, t]);

  const skipFailedSteps = useCallback(() => {
    setFailedSteps([]);
    clearBookImportCache();
    const projectId = importedProjectId.current;
    if (projectId) {
      message.info(t('etapasFalhaIgnoradasAbrindo'));
      navigate(`/project/${projectId}/chapters`);
    }
  }, [navigate, t]);

  const restartImport = useCallback(() => {
    clearBookImportCache();
    importedProjectId.current = null;

    setFile(null);
    setTaskId(null);
    setTaskStatus(null);
    setPreview(null);

    setCreatingTask(false);
    setLoadingPreview(false);
    setApplying(false);
    setApplyProgress(0);
    setApplyMessage('');
    setApplyError(null);
    setIsApplyComplete(false);

    setFailedSteps([]);
    setRetrying(false);
    setRetryProgress(0);
    setRetryMessage('');
    setExtractMode('tail');
    setTailChapterCount(10);

    message.success(t('reiniciadoEnvieTxtNovamente'));
  }, [t]);

  const updateChapter = (index: number, patch: Partial<BookImportPreview['chapters'][number]>) => {
    setPreview(prev => {
      if (!prev) return prev;
      const next = [...prev.chapters];
      next[index] = { ...next[index], ...patch };
      return { ...prev, chapters: next };
    });
  };

  return (
    <div
      style={{
        minHeight: '90vh',
        overflow: 'auto',
        background: `linear-gradient(180deg, ${token.colorBgLayout} 0%, ${token.colorFillSecondary} 100%)`,
        padding: isMobile ? '20px 16px 70px' : '24px 24px 70px',
      }}
    >
      <div style={{ maxWidth: 1400, margin: '0 auto', width: '100%' }}>
        <Card
          variant="borderless"
          style={{
            background: `linear-gradient(135deg, ${token.colorPrimary} 0%, ${token.colorPrimaryHover} 100%)`,
            borderRadius: isMobile ? 16 : 20,
            boxShadow: token.boxShadowSecondary,
            marginBottom: isMobile ? 14 : 16,
            border: 'none',
            position: 'relative',
            overflow: 'hidden',
          }}
        >
          <div style={{ position: 'absolute', top: -48, right: -48, width: 160, height: 160, borderRadius: '50%', background: token.colorWhite, opacity: 0.08, pointerEvents: 'none' }} />
          <div style={{ position: 'absolute', bottom: -40, left: '26%', width: 110, height: 110, borderRadius: '50%', background: token.colorWhite, opacity: 0.05, pointerEvents: 'none' }} />

          <Row align="middle" justify="space-between" gutter={[16, 16]} style={{ position: 'relative', zIndex: 1 }}>
            <Col xs={24} sm={12}>
              <Space direction="vertical" size={4}>
                <Title level={isMobile ? 3 : 2} style={{ margin: 0, color: token.colorWhite, textShadow: `0 2px 4px ${token.colorBgMask}` }}>
                  <InboxOutlined style={{ color: token.colorWhite, opacity: 0.9, marginRight: 8 }} />
                  {t('importarLivro')}
                </Title>
                <Text style={{ fontSize: isMobile ? 12 : 14, color: token.colorTextLightSolid, opacity: 0.85, marginLeft: isMobile ? 40 : 48 }}>
                  {t('envieTxtAnalisaLo')}
                </Text>
              </Space>
            </Col>
            <Col xs={24} sm={12}>
              <Space
                size={12}
                style={{
                  width: '100%',
                  display: 'flex',
                  justifyContent: isMobile ? 'flex-start' : 'flex-end',
                }}
              >
                <Tag
                  style={{
                    marginInlineEnd: 0,
                    background: token.colorWhite,
                    border: `1px solid ${token.colorWhite}`,
                    color: token.colorPrimary,
                    fontWeight: 600,
                    borderRadius: 8,
                    paddingInline: 10,
                  }}
                >
                  {t('progressoAtual')}{currentStepText}
                </Tag>
                <Popconfirm
                  title={t('reiniciarProcesso')}
                  description={t('issoLimparaTarefaImportacao')}
                  onConfirm={restartImport}
                  okText={t('reiniciar')}
                  cancelText={t('cancelar')}
                  disabled={!canRestart}
                >
                  <Button
                    danger
                    type="primary"
                    icon={<ReloadOutlined />}
                    disabled={!canRestart}
                    style={{ boxShadow: '0 6px 16px rgba(0, 0, 0, 0.2)', borderRadius: 10 }}
                  >
                    {t('reiniciar')}
                  </Button>
                </Popconfirm>
              </Space>
            </Col>
          </Row>

          <Card
            variant="borderless"
            style={{
              marginTop: isMobile ? 14 : 18,
              borderRadius: 12,
              background: token.colorBgContainer,
              border: `1px solid ${token.colorBorderSecondary}`,
              boxShadow: token.boxShadow,
            }}
            styles={{ body: { padding: isMobile ? '10px 12px' : '12px 16px' } }}
          >
            <Steps current={currentStep} size={isMobile ? 'small' : 'default'} items={stepItems} />
          </Card>
        </Card>

      {currentStep === 0 && (
      <Card title={t('enviarTxtIniciarAnalise')} style={{ marginBottom: 16 }}>
        <Space direction="vertical" style={{ width: '100%' }} size={16}>
          <Dragger
            accept=".txt"
            multiple={false}
            beforeUpload={(f) => {
              setFile(f);
              return false;
            }}
            onRemove={() => {
              setFile(null);
            }}
            fileList={
              file
                ? [
                    {
                      uid: 'selected-txt',
                      name: file.name,
                      status: 'done',
                    } as UploadFile,
                  ]
                : []
            }
            style={{ padding: '8px 0' }}
          >
            <p className="ant-upload-drag-icon">
              <InboxOutlined />
            </p>
            <p className="ant-upload-text">{t('cliqueArrasteArquivoTxt')}</p>
            <p className="ant-upload-hint">{t('enquantoApenasTxtRecomendado')}</p>
          </Dragger>

          <Card size="small" title={t('intervaloAnalise')}>
            <Space direction="vertical" style={{ width: '100%' }} size={12}>
              {rangeLocked && (
                <Alert
                  type="warning"
                  showIcon
                  message={t('intervaloAnaliseTarefaAtual')}
                  description={t('tarefaImportacaoUsaIntervalo')}
                />
              )}
              <Select
                value={extractMode}
                onChange={(value) => setExtractMode(value)}
                options={[
                  { label: t('usarUltimosXCapitulos'), value: 'tail' },
                  { label: t('usarLivroInteiroEngenharia'), value: 'full' },
                ]}
                style={{ width: '100%' }}
                disabled={rangeLocked}
              />
              <InputNumber
                min={5}
                max={55}
                step={5}
                precision={0}
                value={tailChapterCount}
                disabled={rangeLocked || extractMode !== 'tail'}
                onChange={(value) => setTailChapterCount(typeof value === 'number' ? value : 10)}
                addonBefore={t('numeroCapitulosFinais')}
                style={{ width: '100%' }}
              />
              <Text type="secondary">
                {effectiveExtractMode === 'tail'
                  ? t('seraoUsadosUltimosCapitulos', { normalizedTailChapterCount })
                  : extractMode === 'tail' && tailChapterCount > 50
                    ? t('valorPassaLimiteLivroInteiro')
                    : t('seraUsadoLivroInteiro')}
              </Text>
            </Space>
          </Card>

          <Alert
            type="info"
            showIcon
            message={t('requisitosFormatoTxtAceito')}
            description={
              <div style={{ lineHeight: 1.8 }}>
                <div>{t('1ApenasArquivosTxt')}</div>
                <div>{t('2FormatoRecomendadoCapitulo')}</div>
                <div>{t('3QuebreTextoParagrafos')}</div>
                <div>{t('4BastaDeixarLinha')}</div>
                <div style={{ marginTop: 8 }}>
                  {t('exemplo')}
                  <pre style={{ margin: '8px 0 0', padding: 12, borderRadius: 8, background: token.colorFillAlter, whiteSpace: 'pre-wrap' }}>
{t('capitulo1ChegadaCidade')}
                  </pre>
                </div>
              </div>
            }
          />
          
          <Space wrap>
            <Button
              type="primary"
              icon={<PlayCircleOutlined />}
              loading={creatingTask}
              onClick={startTask}
            >
              {t('iniciarAnalise')}
            </Button>
            {taskId && (
              <Tag color="blue">{t('idTarefa')} {taskId}</Tag>
            )}
          </Space>
        </Space>
      </Card>
      )}

      {currentStep === 1 && (
      <Card title={t('statusAnalise')} style={{ marginBottom: 16 }}>
        {!taskId ? (
          <Empty description={t('nenhumaTarefaCriada')} />
        ) : (
          <div style={{ textAlign: 'center', padding: '24px 0' }}>
            <Progress
              type="circle"
              percent={taskStatus?.progress || 0}
              status={
                taskStatus?.status === 'failed' ? 'exception' :
                taskStatus?.status === 'completed' ? 'success' :
                'active'
              }
            />
            <div style={{ marginTop: 24 }}>
              <Text strong style={{ fontSize: 16 }}>
                {taskStatus?.status === 'pending' && t('aguardandoAgendamento')}
                {taskStatus?.status === 'running' && t('analisandoArquivoTxt')}
                {taskStatus?.status === 'completed' && t('analiseConcluidaGerandoPrevia')}
                {taskStatus?.status === 'failed' && t('falhaAnalise')}
                {taskStatus?.status === 'cancelled' && t('cancelada')}
              </Text>
              {taskStatus?.message && (
                <div style={{ marginTop: 8 }}>
                  <Text type="secondary">{taskStatus.message}</Text>
                </div>
              )}
            </div>

            {taskStatus?.error && (
              <Alert type="error" message={taskStatus.error} showIcon style={{ marginTop: 16, textAlign: 'left' }} />
            )}

            <Space style={{ marginTop: 24 }}>
              <Button icon={<ReloadOutlined />} onClick={refreshStatus}>{t('atualizarStatus')}</Button>
              {taskStatus && ['pending', 'running'].includes(taskStatus.status) && (
                <Button danger icon={<StopOutlined />} onClick={cancelTask}>{t('cancelarTarefa')}</Button>
              )}
            </Space>
          </div>
        )}
      </Card>
      )}

      {currentStep === 2 && (
      <>
      <Card
        title={t('revisarPrevia')}
        extra={
          <Button
            type="primary"
            loading={applying}
            disabled={!preview}
            onClick={applyImport}
          >
            {t('confirmarImportacao')}
          </Button>
        }
        style={{ marginBottom: 16 }}
      >
        <Spin spinning={loadingPreview}>
          {!preview ? (
            <Empty description={t('dadosPreviaApareceraoApos')} />
          ) : (
            <div style={{ maxHeight: '60vh', overflowY: 'auto', paddingRight: 8 }}>
              <Space direction="vertical" style={{ width: '100%' }} size={16}>
              {preview.warnings.length > 0 && (
                <Alert
                  type="warning"
                  showIcon
                  message={t('avisosDetectados')}
                  description={
                    <ul style={{ margin: 0, paddingLeft: 20 }}>
                      {preview.warnings.map((w, idx) => (
                        <li key={`${w.code}-${idx}`}>[{w.level}] {w.message}</li>
                      ))}
                    </ul>
                  }
                />
              )}

              <Card
                size="small"
                title={t('informacoesProjeto')}
              >
                <Row gutter={12}>
                  <Col xs={24} md={12}>
                    <Text>{t('titulo')}</Text>
                    <Input
                      value={preview.project_suggestion.title}
                      onChange={(e) =>
                        setPreview(prev => prev ? ({
                          ...prev,
                          project_suggestion: { ...prev.project_suggestion, title: e.target.value },
                        }) : prev)
                      }
                    />
                  </Col>
                  <Col xs={24} md={12}>
                    <Text>{t('genero')}</Text>
                    <Input
                      value={preview.project_suggestion.genre}
                      onChange={(e) =>
                        setPreview(prev => prev ? ({
                          ...prev,
                          project_suggestion: { ...prev.project_suggestion, genre: e.target.value },
                        }) : prev)
                      }
                    />
                  </Col>
                  <Col xs={24}>
                    <Text>{t('tema')}</Text>
                    <TextArea
                      rows={3}
                      value={preview.project_suggestion.theme}
                      onChange={(e) =>
                        setPreview(prev => prev ? ({
                          ...prev,
                          project_suggestion: { ...prev.project_suggestion, theme: e.target.value },
                        }) : prev)
                      }
                    />
                  </Col>
                  <Col xs={24}>
                    <Text>{t('sinopse')}</Text>
                    <TextArea
                      rows={3}
                      value={preview.project_suggestion.description}
                      onChange={(e) =>
                        setPreview(prev => prev ? ({
                          ...prev,
                          project_suggestion: { ...prev.project_suggestion, description: e.target.value },
                        }) : prev)
                      }
                    />
                  </Col>
                  <Col xs={24} md={12}>
                    <Text>{t('perspectivaNarrativa')}</Text>
                    <Select
                      style={{ width: '100%' }}
                      value={preview.project_suggestion.narrative_perspective}
                      onChange={(v) =>
                        setPreview(prev => prev ? ({
                          ...prev,
                          project_suggestion: { ...prev.project_suggestion, narrative_perspective: v },
                        }) : prev)
                      }
                      options={[
                        { value: 'primeira pessoa', label: t('primeiraPessoa') },
                        { value: 'terceira pessoa', label: t('terceiraPessoa') },
                        { value: 'onisciente', label: t('onisciente') },
                      ]}
                    />
                  </Col>
                  <Col xs={24} md={12}>
                    <Text>{t('metaPalavras')}</Text>
                    <InputNumber
                      style={{ width: '100%' }}
                      min={1000}
                      step={1000}
                      value={preview.project_suggestion.target_words}
                      onChange={(v) =>
                        setPreview(prev => prev ? ({
                          ...prev,
                          project_suggestion: {
                            ...prev.project_suggestion,
                            target_words: Number(v || 100000),
                          },
                        }) : prev)
                      }
                    />
                  </Col>
                </Row>
              </Card>

              <Card size="small" title={t('capitulos', { length: preview.chapters.length })}>
                <Collapse
                  items={preview.chapters.map((ch, idx) => ({
                    key: String(idx),
                    label: t('capitulo', { chapter_number: ch.chapter_number, title: ch.title }),
                    children: (
                      <Space direction="vertical" style={{ width: '100%' }}>
                        <Input
                          value={ch.title}
                          addonBefore={t('titulo')}
                          onChange={(e) => updateChapter(idx, { title: e.target.value })}
                        />
                        <TextArea
                          rows={2}
                          value={ch.summary}
                          placeholder={t('resumoCapitulo')}
                          onChange={(e) => updateChapter(idx, { summary: e.target.value })}
                        />
                        <TextArea
                          rows={8}
                          value={ch.content}
                          placeholder={t('textoCapitulo')}
                          onChange={(e) => updateChapter(idx, { content: e.target.value })}
                        />
                      </Space>
                    ),
                  }))}
                />
              </Card>

              </Space>
            </div>
          )}
        </Spin>
      </Card>

      </>
      )}

      {currentStep === 3 && (
      <Card title={t('progressoGeracaoImportacao')} style={{ marginBottom: 16 }}>
        <div style={{ textAlign: 'center', padding: '40px 20px', maxWidth: 600, margin: '0 auto' }}>
          <Typography.Title level={4} style={{ marginBottom: 32 }}>
            {retrying ? t('tentandoNovamenteEtapasGeracaoFalharam') : (failedSteps.length > 0 && isApplyComplete ? t('importacaoConcluidaAlgumasEtapas') : t('gerandoImportandoConteudoSeu'))}
          </Typography.Title>
          
          <Progress
            percent={retrying ? retryProgress : applyProgress}
            status={
              applyError ? 'exception' :
              (failedSteps.length > 0 && isApplyComplete && !retrying) ? 'exception' :
              (isApplyComplete && failedSteps.length === 0) ? 'success' :
              'active'
            }
            strokeColor={{
              '0%': 'var(--color-primary)',
              '100%': failedSteps.length > 0 ? '#faad14' : 'var(--color-primary-active)',
            }}
            style={{ marginBottom: 24 }}
          />
          
          <Typography.Paragraph
            style={{
              fontSize: 16,
              marginBottom: 32,
              color: applyError ? 'var(--color-error)' :
                (failedSteps.length > 0 && isApplyComplete && !retrying) ? '#faad14' :
                'var(--color-text-secondary)'
            }}
          >
            {retrying ? retryMessage : (applyError || applyMessage)}
          </Typography.Paragraph>
          
          {applyError && (
            <Alert
              type="error"
              message={t('erroImportacao')}
              description={applyError}
              showIcon
              style={{ textAlign: 'left', marginBottom: 24 }}
            />
          )}

          {/* 步骤失败提示与重试UI */}
          {failedSteps.length > 0 && isApplyComplete && !retrying && (
            <div style={{ textAlign: 'left', marginBottom: 24 }}>
              <Alert
                type="warning"
                icon={<WarningOutlined />}
                showIcon
                message={t('etapaSGeracaoFalharam', { length: failedSteps.length })}
                description={
                  <div>
                    <Typography.Paragraph style={{ marginBottom: 12, color: 'rgba(0,0,0,0.65)' }}>
                      {t('etapasGeracaoIaAbaixo')}
                    </Typography.Paragraph>
                    <List
                      size="small"
                      bordered
                      dataSource={failedSteps}
                      renderItem={(item) => (
                        <List.Item
                          style={{ padding: '8px 12px' }}
                        >
                          <List.Item.Meta
                            title={
                              <Space>
                                <Tag color="error">{item.step_label}</Tag>
                                {(item.retry_count ?? 0) > 0 && (
                                  <Tag color="orange">{t('tentativaSRepetidaS', { retry_count: item.retry_count })}</Tag>
                                )}
                              </Space>
                            }
                            description={
                              <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                                {item.error.length > 120 ? item.error.slice(0, 120) + '...' : item.error}
                              </Typography.Text>
                            }
                          />
                        </List.Item>
                      )}
                    />
                    <Space style={{ marginTop: 16, display: 'flex', justifyContent: 'center' }}>
                      <Button
                        type="primary"
                        icon={<RedoOutlined />}
                        onClick={retryFailedSteps}
                        loading={retrying}
                      >
                        {t('tentarNovoTodasEtapas')}
                      </Button>
                      <Button onClick={skipFailedSteps}>
                        {t('ignorarAbrirProjeto')}
                      </Button>
                    </Space>
                  </div>
                }
                style={{ marginBottom: 16 }}
              />
            </div>
          )}

          {/* 重试进行中 */}
          {retrying && (
            <div style={{ marginBottom: 24 }}>
              <Spin spinning={retrying}>
                <Alert
                  type="info"
                  showIcon
                  message={t('tentandoNovamente')}
                  description={retryMessage}
                  style={{ textAlign: 'left' }}
                />
              </Spin>
            </div>
          )}
          
          {!failedSteps.length && !retrying && (
            <div style={{
              background: 'var(--color-bg-layout)',
              padding: 16,
              borderRadius: 8,
              textAlign: 'left',
              marginTop: 32
            }}>
              <Typography.Text type="secondary" style={{ fontSize: 13 }}>
                {t('duranteImportacaoIaCompleta')}<br />
                {t('cenarioTempoLugaresAtmosfera')}<br />
                {t('sistemaCarreirasPrincipalSecundarias')}<br />
                {t('personagensPrincipaisOrganizacoesRelacionadas')}<br />
                {isApplyComplete ? t('todasEtapasForamConcluidas') : t('aguardeVoceSeraRedirecionado')}
              </Typography.Text>
            </div>
          )}
        </div>
      </Card>
      )}

      </div>
    </div>
  );
}
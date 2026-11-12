import React, { useMemo, useState } from 'react';
import { Modal, Button, Card, Statistic, Row, Col, message, theme } from 'antd';
import { CheckOutlined, CloseOutlined, SwapOutlined } from '@ant-design/icons';
import ReactDiffViewer from 'react-diff-viewer-continued';
import { useThemeMode } from '../theme/useThemeMode';
import { useTranslation } from 'react-i18next';

interface ChapterContentComparisonProps {
  visible: boolean;
  onClose: () => void;
  chapterId: string;
  chapterTitle: string;
  originalContent: string;
  newContent: string;
  wordCount: number;
  onApply: () => void;
  onDiscard: () => void;
}

const ChapterContentComparison: React.FC<ChapterContentComparisonProps> = ({
  visible,
  onClose,
  chapterId,
  chapterTitle,
  originalContent,
  newContent,
  wordCount,
  onApply,
  onDiscard
}) => {
  const { t } = useTranslation('chapterContentComparison');
  const { token } = theme.useToken();
  const { resolvedMode } = useThemeMode();
  const [applying, setApplying] = useState(false);
  const [viewMode, setViewMode] = useState<'split' | 'unified'>('split');
  const [modal, contextHolder] = Modal.useModal();

  const originalWordCount = originalContent.length;
  const wordCountDiff = wordCount - originalWordCount;
  const wordCountDiffPercent = ((wordCountDiff / originalWordCount) * 100).toFixed(1);
  const isDarkMode = resolvedMode === 'dark';
  const diffViewerStyles = useMemo(() => ({
    variables: {
      light: {
        diffViewerBackground: token.colorBgContainer,
        diffViewerColor: token.colorText,
        diffViewerTitleBackground: token.colorBgElevated,
        diffViewerTitleColor: token.colorTextHeading,
        addedBackground: token.colorSuccessBg,
        addedColor: token.colorText,
        removedBackground: token.colorErrorBg,
        removedColor: token.colorText,
        wordAddedBackground: token.colorSuccessBorder,
        wordRemovedBackground: token.colorErrorBorder,
        addedGutterBackground: token.colorSuccessBg,
        removedGutterBackground: token.colorErrorBg,
        gutterBackground: token.colorFillQuaternary,
        gutterBackgroundDark: token.colorFillTertiary,
        highlightBackground: token.colorWarningBg,
        highlightGutterBackground: token.colorWarningBorder,
      },
      dark: {
        diffViewerBackground: token.colorBgContainer,
        diffViewerColor: token.colorText,
        diffViewerTitleBackground: token.colorBgElevated,
        diffViewerTitleColor: token.colorTextHeading,
        addedBackground: 'rgba(82, 196, 26, 0.16)',
        addedColor: token.colorText,
        removedBackground: 'rgba(255, 77, 79, 0.16)',
        removedColor: token.colorText,
        wordAddedBackground: 'rgba(82, 196, 26, 0.3)',
        wordRemovedBackground: 'rgba(255, 77, 79, 0.3)',
        addedGutterBackground: 'rgba(82, 196, 26, 0.12)',
        removedGutterBackground: 'rgba(255, 77, 79, 0.12)',
        gutterBackground: token.colorFillQuaternary,
        gutterBackgroundDark: token.colorFillSecondary,
        highlightBackground: 'rgba(250, 173, 20, 0.18)',
        highlightGutterBackground: 'rgba(250, 173, 20, 0.28)',
      },
    },
    line: {
      padding: '10px 2px',
      fontSize: '14px',
      lineHeight: '20px',
      whiteSpace: 'pre-wrap' as const,
      wordBreak: 'break-word' as const,
    },
  }), [token]);

  const handleApply = async () => {
    setApplying(true);
    try {
      const response = await fetch(`/api/chapters/${chapterId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          content: newContent
        })
      });

      if (!response.ok) {
        throw new Error(t('falhaAplicarNovoConteudo'));
      }

      message.success(t('novoConteudoAplicado'));

      // 先调用 onApply 通知父组件刷新
      onApply();

      // 延迟触发章节分析，给父组件时间刷新
      setTimeout(async () => {
        try {
          const analysisResponse = await fetch(`/api/chapters/${chapterId}/analyze`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
            }
          });

          if (analysisResponse.ok) {
            message.success(t('analiseCapituloFoiIniciada'));
          } else {
            message.warning(t('falhaIniciarAnaliseCapitulo'));
          }
        } catch (analysisError) {
          console.error('Falha ao iniciar a análise:', analysisError);
          message.warning(t('falhaIniciarAnaliseCapitulo'));
        }
      }, 500);

      onClose();
    } catch (error: unknown) {
      const err = error as Error;
      message.error(err.message || t('falhaAoAplicar'));
    } finally {
      setApplying(false);
    }
  };

  const handleDiscard = () => {
    modal.confirm({
      title: t('confirmarDescarte'),
      content: t('temCertezaDesejaDescartar'),
      centered: true,
      okText: t('descartar'),
      cancelText: t('cancelar'),
      okButtonProps: { danger: true },
      onOk: () => {
        onDiscard();
        onClose();
        message.info(t('novoConteudoDescartado'));
      }
    });
  };

  return (
    <>
      {contextHolder}
      <Modal
      title={t('comparacaoDeConteudo', { chapterTitle })}
      open={visible}
      onCancel={onClose}
      width="95%"
      centered
      style={{ maxWidth: 1600 }}
      footer={[
        <Button
          key="discard"
          danger
          icon={<CloseOutlined />}
          onClick={handleDiscard}
        >
          {t('descartarNovoConteudo')}
        </Button>,
        <Button
          key="toggle"
          icon={<SwapOutlined />}
          onClick={() => setViewMode(viewMode === 'split' ? 'unified' : 'split')}
        >
          {t('alternarVisualizacao')}
        </Button>,
        <Button
          key="apply"
          type="primary"
          icon={<CheckOutlined />}
          loading={applying}
          onClick={handleApply}
        >
          {t('aplicarNovoConteudo')}
        </Button>
      ]}
    >
      {/* 统计信息 */}
      <Card size="small" style={{ marginBottom: 16 }}>
        <Row gutter={16}>
          <Col span={6}>
            <Statistic
              title={t('palavrasConteudoOriginal')}
              value={originalWordCount}
              suffix={t('palavras')}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title={t('palavrasNovoConteudo')}
              value={wordCount}
              suffix={t('palavras')}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title={t('variacaoDePalavras')}
              value={wordCountDiff}
              suffix={t('palavras')}
              valueStyle={{ color: wordCountDiff > 0 ? 'var(--color-success)' : 'var(--color-error)' }}
              prefix={wordCountDiff > 0 ? '+' : ''}
            />
          </Col>
          <Col span={6}>
            <Statistic
              title={t('proporcaoDaVariacao')}
              value={wordCountDiffPercent}
              suffix="%"
              valueStyle={{ color: Math.abs(parseFloat(wordCountDiffPercent)) < 10 ? 'var(--color-primary)' : 'var(--color-warning)' }}
              prefix={wordCountDiff > 0 ? '+' : ''}
            />
          </Col>
        </Row>
      </Card>

      {/* 内容对比 */}
      <div style={{
        maxHeight: 'calc(90vh - 300px)',
        overflow: 'auto',
        border: `1px solid ${token.colorBorder}`,
        borderRadius: 8,
        background: token.colorBgContainer
      }}>
        <ReactDiffViewer
          oldValue={originalContent}
          newValue={newContent}
          splitView={viewMode === 'split'}
          leftTitle={t('conteudoOriginal')}
          rightTitle={t('novoConteudo')}
          showDiffOnly={false}
          useDarkTheme={isDarkMode}
          styles={diffViewerStyles}
        />
      </div>
      </Modal>
    </>
  );
};

export default ChapterContentComparison;
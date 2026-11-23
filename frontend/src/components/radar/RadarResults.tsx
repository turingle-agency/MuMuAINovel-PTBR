import { useEffect, useState } from 'react';
import { Alert, Button, Descriptions, Drawer, Empty, List, Pagination, Space, Spin, Table, Tag, Typography } from 'antd';
import type { TableColumnsType } from 'antd';
import { useTranslation } from 'react-i18next';
import { radarApi } from '../../services/radarApi';
import type { EvidenceItem, Page, ResearchDetail, ResearchListItem, SourceResult } from '../../types/radar';
import { calendarDate, canCreateBrief, dateTime, money, number, safeLink, shouldPoll } from '../../utils/radarPresentation';

const { Text, Title, Paragraph } = Typography;
const COLORS = { pending: 'default', running: 'processing', complete: 'success', partial: 'warning', failed: 'error' };

interface ResultActions {
  onOpen: (id: string) => void;
  onBrief: (row: ResearchListItem) => void;
}

export function RadarResults({ rows, loading, weekly, onOpen, onBrief }: ResultActions & {
  rows: ResearchListItem[];
  loading: boolean;
  weekly: boolean;
}) {
  const { t } = useTranslation('radar');
  const columns: TableColumnsType<ResearchListItem> = [
    { title: t('topic'), key: 'topic', width: 195, render: (_, row) => (
      <Space direction="vertical" size={2}>
        <Button type="link" style={{ padding: 0, height: 'auto', whiteSpace: 'normal', textAlign: 'start' }}
          onClick={() => onOpen(row.id)}>{row.topic}</Button>
        <Space size={4} wrap>
          <Tag color={COLORS[row.status]}>{t(`status.${row.status}`)}</Tag>
          {row.mode && <Text type="secondary">{t(`modes.${row.mode}`)}</Text>}
        </Space>
        {row.legacy && <Text type="secondary">{t('legacy')}</Text>}
      </Space>
    ) },
    { title: t('market'), dataIndex: 'country', width: 60, render: value => value || '—' },
    { title: t('productType'), dataIndex: 'product_type', width: 105, render: value => value ? t(`types.${value}`, { defaultValue: value }) : '—' },
    { title: t('score'), key: 'score', width: 125, render: (_, row) => row.score !== null
      ? <Text strong>{number(row.score)}</Text>
      : <Text type="secondary">{shouldPoll(row.status) ? '—' : t('insufficient')}</Text> },
    { title: t('direction'), dataIndex: 'direction_points', width: 95, render: (value: number | null) =>
      value !== null && value > 0 ? `+${number(value)}` : number(value) },
    { title: t('amazonPrice'), key: 'amazon', width: 125, render: (_, row) =>
      row.amazon_average !== null && row.currency ? (
        <Space direction="vertical" size={0}>
          <Text>{money(row.amazon_average, row.currency)}</Text>
          <Text type="secondary">{t('sample', { count: row.amazon_count })}</Text>
        </Space>
      ) : t('notAvailable') },
    { title: t('competition'), key: 'competition', width: 125, render: (_, row) => row.product_type === 'fiction' ? (
      <Space direction="vertical" size={0}>
        <Text>{row.kindle_category ?? t('notAvailable')}</Text>
        {row.kindle_best_rank !== null && <Text type="secondary">{t('rank', { rank: row.kindle_best_rank })}</Text>}
      </Space>
    ) : row.meta_ads_count !== null ? t('ads', { count: row.meta_ads_count }) : t('notAvailable') },
    { title: t('social'), key: 'social', width: 170, render: (_, row) => {
      const signals = Object.entries(row.source_statuses).filter(([name]) => ['youtube', 'agent_reach', 'firecrawl'].includes(name));
      return signals.length ? <Space wrap>{signals.map(([name, status]) => (
        <Tag key={name} color={status === 'ok' ? 'success' : status === 'partial' ? 'warning' : 'default'}>
          {t(`sourcesByName.${name}`)} · {t(`sourceStatus.${status}`)}
        </Tag>
      ))}</Space> : t('notAvailable');
    } },
    { title: t('actions'), key: 'actions', width: 202, render: (_, row) => (
      <Space>
        <Button onClick={() => onOpen(row.id)}>{t('history')}</Button>
        <Button type="primary" disabled={!canCreateBrief(row)}
          onClick={event => { event.stopPropagation(); onBrief(row); }}>{t('createBrief')}</Button>
      </Space>
    ) },
  ];
  const renderTable = (items: ResearchListItem[]) => (
    <Table rowKey="id" size="middle" loading={loading} columns={columns} dataSource={items}
      pagination={false} scroll={{ x: 1202 }}
      onRow={row => ({ onClick: () => onOpen(row.id) })}
      locale={{ emptyText: <Empty image={Empty.PRESENTED_IMAGE_SIMPLE} description={t('noResults')} /> }} />
  );
  if (!weekly || !rows.length) return renderTable(rows);
  const scored = rows.filter(row => row.score !== null);
  const unscored = rows.filter(row => row.score === null);
  return <Space direction="vertical" size="large" style={{ width: '100%' }}>
    {!!scored.length && <section><Title level={5}>{t('withScore')}</Title>{renderTable(scored)}</section>}
    {!!unscored.length && <section><Title level={5}>{t('withoutScore')}</Title>{renderTable(unscored)}</section>}
  </Space>;
}

function Evidence({ item, onSearch }: { item: EvidenceItem; onSearch: (topic: string) => void }) {
  const { t } = useTranslation('radar');
  const link = safeLink(item.url);
  const d = item.data;
  const related = d.related_query;
  return <List.Item>
    <Space direction="vertical" size={2}>
      <Text strong>{item.label}</Text>
      {item.observed_date && <Text type="secondary">{calendarDate(item.observed_date)}</Text>}
      {d.excerpt && <Text>{d.excerpt}</Text>}
      {d.asin && <Text type="secondary">ASIN {d.asin}{d.category && ` · ${d.category}`}</Text>}
      {d.rank !== null && <Text>{t('rank', { rank: d.rank })}</Text>}
      {d.search_position !== null && <Text>{t('searchPosition', { position: d.search_position })}</Text>}
      {d.price !== null && d.currency && d.price_kind === 'purchase' && <Text>{money(d.price, d.currency)}</Text>}
      {d.started_at && <Text>{calendarDate(d.started_at)}</Text>}
      {d.value !== null && <Text>{number(d.value)}</Text>}
      {link && <a href={link} target="_blank" rel="noreferrer">{t('readSource')}</a>}
      {related && <Button size="small" onClick={() => onSearch(related)}>{t('useRelated')}</Button>}
    </Space>
  </List.Item>;
}

function orderedItems(source: SourceResult): EvidenceItem[] {
  if (source.source === 'meta') return source.items
    .filter(item => item.kind === 'ad' && item.data.active === true && item.data.commercial === true)
    .sort((a, b) => (a.data.started_at ?? '9999').localeCompare(b.data.started_at ?? '9999'));
  if (source.source === 'amazon') return source.items
    .filter(item => item.kind === 'book' && item.data.format === 'kindle')
    .sort((a, b) => (a.data.rank ?? Infinity) - (b.data.rank ?? Infinity));
  return source.items;
}

export type RadarSelection = { kind: 'research' | 'brief'; id: string };

export function RadarDetailDrawer({ selection, onClose, onOpen, onBrief, onSearch }: ResultActions & {
  selection: RadarSelection | null;
  onClose: () => void;
  onSearch: (topic: string) => void;
}) {
  const { t } = useTranslation('radar');
  const [result, setResult] = useState<{ id: string; kind: string; value: ResearchDetail } | null>(null);
  const [history, setHistory] = useState<{ id: string; value: Page<ResearchListItem> } | null>(null);
  const [historyPage, setHistoryPage] = useState(1);
  const [error, setError] = useState<string | null>(null);
  const [historyError, setHistoryError] = useState<string | null>(null);
  const id = selection?.id;
  const kind = selection?.kind;

  useEffect(() => {
    if (!id || !kind) return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    let inProgress = false;
    const load = async () => {
      try {
        const data = kind === 'research'
          ? await radarApi.detail(id, controller.signal)
          : (await radarApi.brief(id, controller.signal)).research;
        if (controller.signal.aborted) return;
        setResult({ id, kind, value: data });
        setError(null);
        inProgress = kind === 'research' && shouldPoll(data.status);
        if (inProgress) timer = setTimeout(load, 3000);
      } catch {
        if (!controller.signal.aborted) {
          setError(id);
          if (inProgress) timer = setTimeout(load, 3000);
        }
      }
    };
    void load();
    return () => { controller.abort(); clearTimeout(timer); };
  }, [id, kind]);

  useEffect(() => {
    if (!id || kind !== 'research') return;
    const controller = new AbortController();
    radarApi.history(id, { page: historyPage, page_size: 5 }, controller.signal).then(value => {
      if (!controller.signal.aborted) {
        setHistory({ id, value });
        setHistoryError(null);
      }
    }).catch(() => { if (!controller.signal.aborted) setHistoryError(id); });
    return () => controller.abort();
  }, [id, kind, historyPage]);

  const data = result && result.id === id && result.kind === kind ? result.value : undefined;
  const snapshot = data?.snapshot;
  const currentHistory = history && history.id === id ? history.value : null;
  const evidence = new Map<string, EvidenceItem>(Object.entries(snapshot?.sources ?? {}).flatMap(([source, value]) =>
    value.items.map(item => [`${source}:${item.id}`, item] as const)));
  return <Drawer open={!!selection} onClose={onClose} width="min(820px, 100vw)"
    title={kind === 'brief' ? t('openBrief') : t('details')}
    extra={data && kind === 'research' && canCreateBrief(data) &&
      <Button type="primary" onClick={() => onBrief(data)}>{t('createBrief')}</Button>}>
    {id && error === id && <Alert type="error" message={t('errorLoad')} />}
    {id && !data && error !== id && <Spin />}
    {data && <>
      <Title level={3}>{data.topic}</Title>
      <Space wrap>
        <Tag color={COLORS[data.status]}>{t(`status.${data.status}`)}</Tag>
        {data.country && <Tag>{data.country}</Tag>}
        {data.product_type && <Tag>{t(`types.${data.product_type}`, { defaultValue: data.product_type })}</Tag>}
        {data.week_key && <Tag>{data.week_key}</Tag>}
        <Text type="secondary">{dateTime(data.created_at)}</Text>
      </Space>
      {kind === 'brief' && <Alert style={{ marginTop: 16 }} showIcon type="success" message={t('ready')} />}
      {data.legacy && <Alert style={{ marginTop: 16 }} type="info" message={t('legacy')} />}
      {snapshot && <>
        <Descriptions size="small" column={{ xs: 1, sm: 2 }} style={{ marginTop: 20 }}>
          <Descriptions.Item label={t('query')}>{snapshot.input?.query ?? '—'}</Descriptions.Item>
          <Descriptions.Item label={t('language')}>{snapshot.input?.language ?? '—'}</Descriptions.Item>
          <Descriptions.Item label={t('writingLanguage')}>{snapshot.writing_language}</Descriptions.Item>
          {snapshot.input && <Descriptions.Item label={t('period')}>
            {calendarDate(snapshot.input.start_date)} – {calendarDate(snapshot.input.end_date)}
          </Descriptions.Item>}
        </Descriptions>
        {shouldPoll(data.status) && <Paragraph>{t('progress', snapshot.progress)}
          {snapshot.progress.current_source && ` · ${t(`sourcesByName.${snapshot.progress.current_source}`)}`}
        </Paragraph>}
        <Title level={4}>{t('score')} · {data.score === null ? t('insufficient') : number(data.score)}</Title>
        {data.score_delta !== null && <Paragraph>{t('delta', { value: number(data.score_delta) })}</Paragraph>}
        <Descriptions size="small" column={1}>
          {(['demand', 'competition', 'price'] as const).map(key => <Descriptions.Item
            key={key} label={t(`components.${key}`)}>
            {number(snapshot.score?.[key] ?? null)} · {snapshot.weights[key]}%
          </Descriptions.Item>)}
          {snapshot.score && <Descriptions.Item label={t('score')}>{t('formula', { version: snapshot.score.formula_version })}</Descriptions.Item>}
          <Descriptions.Item label={t('reference')}>
            {snapshot.price_reference && data.currency ? money(snapshot.price_reference, data.currency) : '—'}
          </Descriptions.Item>
          <Descriptions.Item label={t('amazonPrice')}>
            {data.amazon_average && data.currency ? money(data.amazon_average, data.currency) : '—'}
            {` · ${t('sample', { count: data.amazon_count })}`}
          </Descriptions.Item>
        </Descriptions>
        {snapshot.summary.status !== 'skipped' && <>
          <Title level={4}>{t('summary')}</Title>
          {snapshot.summary.status === 'error' && <Alert type="warning" message={snapshot.summary.detail} />}
          {snapshot.summary.status === 'ok' && !snapshot.summary.items.length && <Paragraph>{t('summaryEmpty')}</Paragraph>}
          {snapshot.summary.items.map((item, index) => <Paragraph key={index}>
            {item.text}{' '}
            {item.evidence_ids.map(identifier => {
              const source = evidence.get(identifier);
              const link = safeLink(source?.url ?? null);
              return link && <a key={identifier} style={{ marginInlineEnd: 8 }} href={link} target="_blank" rel="noreferrer">{source?.label}</a>;
            })}
          </Paragraph>)}
        </>}
        <Title level={4}>{t('evidence')}</Title>
        {!Object.keys(snapshot.sources).length && <Paragraph>{t('noEvidence')}</Paragraph>}
        {Object.entries(snapshot.sources).map(([key, source]) => <section key={key} style={{ marginBottom: 16 }}>
          <Title level={5}>{t(`sourcesByName.${key}`, { defaultValue: key })}</Title>
          <Space wrap>
            <Tag>{t(`sourceStatus.${source.status}`)}</Tag>
            {source.from_cache && <Tag>{t('cached')}</Tag>}
            <Text type="secondary">{t('collectedAt', { date: dateTime(source.collected_at) })}</Text>
            <Text type="secondary">{t('scope', { country: source.scope })}</Text>
            <Text type="secondary">{t('method', { version: source.method_version })}</Text>
          </Space>
          {[...new Set(source.limits.notes)].map(note => <div key={note}><Text type="secondary">{note}</Text></div>)}
          <List size="small" dataSource={orderedItems(source)} locale={{ emptyText: t('noEvidence') }}
            renderItem={item => <Evidence key={item.id} item={item} onSearch={onSearch} />} />
        </section>)}
      </>}
      {kind === 'research' && <section>
        <Title level={4}>{t('history')}</Title>
        {id && historyError === id && <Alert type="error" message={t('errorLoad')} />}
        <List size="small" loading={!currentHistory && historyError !== id}
          dataSource={currentHistory?.items.map(row => row.id === data.id ? data : row) ?? []}
          locale={{ emptyText: t('noHistory') }}
          renderItem={row => <List.Item key={row.id} actions={[
            <Button key="open" disabled={row.id === id} onClick={() => { setHistoryPage(1); onOpen(row.id); }}>{t('open')}</Button>,
          ]}>
            <Space wrap><Text>{dateTime(row.created_at)}</Text><Tag>{t(`status.${row.status}`)}</Tag><Text>{number(row.score)}</Text></Space>
          </List.Item>} />
        {!!currentHistory && currentHistory.total > currentHistory.page_size &&
          <Pagination current={historyPage} pageSize={currentHistory.page_size}
            total={currentHistory.total} onChange={setHistoryPage} showSizeChanger={false} />}
      </section>}
    </>}
  </Drawer>;
}

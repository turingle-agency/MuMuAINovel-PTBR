import { useEffect, useRef, useState } from 'react';
import { Alert, Button, Card, Empty, Form, Input, List, Modal, Pagination, Select, Space, Spin, Tabs, Typography, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { RadarDetailDrawer, RadarResults } from '../components/radar/RadarResults';
import type { RadarSelection } from '../components/radar/RadarResults';
import { RadarSettings } from '../components/radar/RadarSettings';
import { radarApi } from '../services/radarApi';
import type { BriefItem, Page, RadarSettingsView, ResearchFilters, ResearchListItem, ResearchRequest } from '../types/radar';
import { dateTime, shouldPoll } from '../utils/radarPresentation';

type SearchFields = Omit<ResearchRequest, 'request_id'>;
type RadarTab = 'researches' | 'briefs' | 'settings';
const SIZE = 20;
const FULL = { width: '100%' };

function requestId() {
  const bytes = crypto.getRandomValues(new Uint8Array(16));
  bytes[6] = (bytes[6] & 0x0f) | 0x40;
  bytes[8] = (bytes[8] & 0x3f) | 0x80;
  const hex = Array.from(bytes, value => value.toString(16).padStart(2, '0')).join('');
  return [hex.slice(0, 8), hex.slice(8, 12), hex.slice(12, 16), hex.slice(16, 20), hex.slice(20)].join('-');
}

export default function NicheRadar() {
  const { t } = useTranslation('radar');
  const [notifications, context] = message.useMessage();
  const [searchForm] = Form.useForm<SearchFields>();
  const selectedCountry = Form.useWatch('country', searchForm);
  const [tab, setTab] = useState<RadarTab>('researches');
  const [config, setConfig] = useState<RadarSettingsView | null>(null);
  const [configError, setConfigError] = useState(false);
  const [filters, setFilters] = useState<ResearchFilters>({ page: 1, page_size: SIZE });
  const [results, setResults] = useState<Page<ResearchListItem> | null>(null);
  const [loading, setLoading] = useState(true);
  const [resultError, setResultError] = useState(false);
  const [version, setVersion] = useState(0);
  const [briefs, setBriefs] = useState<Page<BriefItem> | null>(null);
  const [briefPage, setBriefPage] = useState(1);
  const [briefError, setBriefError] = useState(false);
  const [selection, setSelection] = useState<RadarSelection | null>(null);
  const [candidate, setCandidate] = useState<ResearchListItem | null>(null);
  const [savingBrief, setSavingBrief] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const lastRequest = useRef<ResearchRequest | null>(null);
  const activeProfiles = config?.profiles.filter(profile => profile.active) ?? [];
  const typeOptions = (['lowticket', 'fiction'] as const).map(value => ({ value, label: t(`types.${value}`) }));
  const weekMode = filters.mode === 'weekly' || !!filters.week_key;

  useEffect(() => {
    const controller = new AbortController();
    radarApi.settings(controller.signal).then(data => {
      if (!controller.signal.aborted) setConfig(data);
    }).catch(() => { if (!controller.signal.aborted) setConfigError(true); });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    if (!config || tab !== 'researches') return;
    const current = searchForm.getFieldValue('country');
    if (!config.profiles.some(profile => profile.active && profile.country === current)) {
      searchForm.setFieldValue('country', config.profiles.find(profile => profile.active)?.country);
    }
  }, [config, searchForm, tab]);

  useEffect(() => {
    if (tab !== 'researches') return;
    const controller = new AbortController();
    radarApi.researches(filters, controller.signal).then(data => {
      if (!controller.signal.aborted) {
        setResults(data);
        setResultError(false);
      }
    }).catch(() => {
      if (!controller.signal.aborted) setResultError(true);
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    return () => controller.abort();
  }, [filters, tab, version]);

  const pendingIds = (results?.items ?? []).filter(row => !row.legacy && shouldPoll(row.status))
    .map(row => row.id).sort().join(',');
  useEffect(() => {
    if (!pendingIds || loading || tab !== 'researches') return;
    const controller = new AbortController();
    let timer: ReturnType<typeof setTimeout>;
    const poll = async () => {
      const updates = await Promise.allSettled(pendingIds.split(',').map(id => radarApi.detail(id, controller.signal)));
      if (controller.signal.aborted) return;
      const changed = updates.flatMap(update => update.status === 'fulfilled' ? [update.value] : []);
      setResults(current => current && {
        ...current, items: current.items.map(row => changed.find(update => update.id === row.id) ?? row),
      });
      if (changed.some(update => !shouldPoll(update.status))) setVersion(value => value + 1);
      else timer = setTimeout(poll, 3000);
    };
    timer = setTimeout(poll, 3000);
    return () => { controller.abort(); clearTimeout(timer); };
  }, [pendingIds, filters, loading, tab]);

  useEffect(() => {
    if (tab !== 'briefs') return;
    const controller = new AbortController();
    radarApi.briefs({ page: briefPage, page_size: SIZE }, controller.signal).then(data => {
      if (!controller.signal.aborted) { setBriefs(data); setBriefError(false); }
    }).catch(() => { if (!controller.signal.aborted) setBriefError(true); });
    return () => controller.abort();
  }, [briefPage, tab, version]);

  const openResearch = (id: string) => setSelection({ kind: 'research', id });
  const submit = async (values: SearchFields) => {
    const normalized = { ...values, topic: values.topic.trim() };
    const previous = lastRequest.current;
    const payload = previous && previous.topic === normalized.topic && previous.country === normalized.country &&
      previous.product_type === normalized.product_type ? previous : { ...normalized, request_id: requestId() };
    lastRequest.current = payload;
    setSubmitting(true);
    try {
      const result = await radarApi.submit(payload);
      lastRequest.current = null;
      setVersion(value => value + 1);
      openResearch(result.id);
      void notifications.success(t('queued'));
    } catch {
      void notifications.error(t('errorSubmit'));
    } finally {
      setSubmitting(false);
    }
  };

  const create = async () => {
    if (!candidate) return;
    setSavingBrief(true);
    try {
      const brief = await radarApi.createBrief(candidate.id);
      setCandidate(null);
      setSelection({ kind: 'brief', id: brief.id });
      setVersion(value => value + 1);
      void notifications.success(t('savedBrief'));
    } catch {
      void notifications.error(t('errorBrief'));
    } finally {
      setSavingBrief(false);
    }
  };

  const currentCoverage = config?.coverage[selectedCountry ?? activeProfiles[0]?.country];
  const hasCollection = (['firecrawl', 'youtube'] as const).some(
    source => currentCoverage?.[source].status === 'ready',
  );

  return <div style={{ padding: '20px clamp(12px, 3vw, 32px)', maxWidth: 1600, margin: '0 auto' }}>
    {context}
    {configError && <Alert type="error" showIcon message={t('errorLoad')} />}
    <Tabs activeKey={tab} onChange={key => {
      setSelection(null);
      setTab(key as RadarTab);
    }} destroyOnHidden items={[
      { key: 'researches', label: t('researches'), children: <Space direction="vertical" size="large" style={FULL}>
        {config && (!activeProfiles.length || !hasCollection) && <Alert type="info" showIcon
          message={t(activeProfiles.length ? 'noSources' : 'noMarkets')}
          action={<Button size="small" onClick={() => setTab('settings')}>{t('settings')}</Button>} />}
        <Card size="small">
          <Form name="radar-search" form={searchForm} layout="vertical" onFinish={submit}
            initialValues={{ product_type: 'lowticket' }}>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 12, alignItems: 'center' }}>
              <Form.Item label={t('topic')} name="topic" style={{ flex: '1 1 240px' }}
                rules={[{ required: true, whitespace: true, message: t('required') }]}>
                <Input showCount maxLength={300} />
              </Form.Item>
              <Form.Item label={t('market')} name="country" rules={[{ required: true, message: t('required') }]}>
                <Select style={{ width: 105 }} options={activeProfiles.map(profile => ({ value: profile.country }))} />
              </Form.Item>
              <Form.Item label={t('productType')} name="product_type">
                <Select style={{ width: 150 }} options={typeOptions} />
              </Form.Item>
              <Button type="primary" htmlType="submit" disabled={!activeProfiles.length} loading={submitting}>{t('search')}</Button>
            </div>
          </Form>
        </Card>
        <Form name="radar-filters" layout="vertical" onFinish={(values: ResearchFilters) => {
          setLoading(true);
          setFilters({ ...values, week_key: values.week_key?.trim() || undefined, page: 1, page_size: SIZE });
        }}>
          <Space wrap align="end">
            <Form.Item label={t('productType')} name="product_type">
              <Select allowClear placeholder={t('all')} style={{ width: 133 }} options={typeOptions} />
            </Form.Item>
            <Form.Item label={t('market')} name="country">
              <Select allowClear placeholder={t('all')} style={{ width: 100 }}
                options={config?.profiles.map(profile => ({ value: profile.country }))} />
            </Form.Item>
            <Form.Item label={t('modeLabel')} name="mode">
              <Select allowClear placeholder={t('all')} style={{ width: 112 }}
                options={(['manual', 'weekly'] as const).map(value => ({ value, label: t(`modes.${value}`) }))} />
            </Form.Item>
            <Form.Item label={t('week')} name="week_key" rules={[{
              pattern: /^\d{4}-W(0[1-9]|[1-4]\d|5[0-3])$/, message: t('invalidWeek'),
            }]}>
              <Input allowClear placeholder={t('weekPlaceholder')} style={{ width: 132 }} />
            </Form.Item>
            <Button htmlType="submit" style={{ marginBottom: 24 }}>{t('apply')}</Button>
          </Space>
        </Form>
        {resultError && <Alert type="error" message={t('errorLoad')} />}
        <RadarResults rows={results?.items ?? []} loading={loading} weekly={weekMode}
          onOpen={openResearch} onBrief={setCandidate} />
        {!!results && results.total > results.page_size && <Pagination current={filters.page}
          total={results.total} pageSize={results.page_size} showSizeChanger={false}
          onChange={page => { setLoading(true); setFilters(current => ({ ...current, page })); }} />}
      </Space> },
      { key: 'briefs', label: t('briefs'), children: <>
        {briefError && <Alert type="error" message={t('errorLoad')} />}
        <List bordered loading={!briefs && !briefError} dataSource={briefs?.items ?? []}
          locale={{ emptyText: <Empty description={t('noBriefs')} /> }}
          renderItem={brief => <List.Item key={brief.id} actions={[
            <Button key="open" onClick={() => setSelection({ kind: 'brief', id: brief.id })}>{t('openBrief')}</Button>,
          ]}>
            <List.Item.Meta title={brief.research.topic}
              description={`${brief.research.country ?? '—'} · ${dateTime(brief.created_at)} · ${t('ready')}`} />
          </List.Item>} />
        {!!briefs && briefs.total > briefs.page_size && <Pagination current={briefPage} total={briefs.total}
          pageSize={briefs.page_size} onChange={setBriefPage} showSizeChanger={false} />}
      </> },
      { key: 'settings', label: t('settings'), children: config ? <RadarSettings config={config} onSaved={setConfig} />
        : !configError && <Spin /> },
    ]} />
    <RadarDetailDrawer key={selection ? `${selection.kind}:${selection.id}` : 'closed'} selection={selection}
      onClose={() => setSelection(null)} onOpen={openResearch} onBrief={setCandidate}
      onSearch={topic => { setTab('researches'); setSelection(null); searchForm.setFieldValue('topic', topic); }} />
    <Modal open={!!candidate} title={t('confirmBrief')} okText={t('createBrief')} confirmLoading={savingBrief}
      cancelText={t('common:cancelar', { defaultValue: 'Cancelar' })} onOk={() => void create()}
      onCancel={() => { if (!savingBrief) setCandidate(null); }}>
      {candidate && <Typography.Text>
        {candidate.topic} · {candidate.country} · {dateTime(candidate.created_at)}
      </Typography.Text>}
    </Modal>
  </div>;
}

import { useEffect, useState } from 'react';
import { Alert, Button, Card, Checkbox, Collapse, Descriptions, Form, Input, InputNumber, Select, Space, Switch, Tag, Typography, message } from 'antd';
import { useTranslation } from 'react-i18next';
import { radarApi } from '../../services/radarApi';
import type { BudgetView, MarketProfile, RadarConfig, RadarSettingsView, SecretSource, SourceCheck, SourceName } from '../../types/radar';
import { money } from '../../utils/radarPresentation';

const SOURCES: SourceName[] = ['firecrawl', 'youtube', 'trends', 'amazon', 'meta', 'agent_reach', 'apify'];
const SECRETS: SecretSource[] = ['firecrawl', 'youtube', 'meta', 'apify'];
const TYPES = ['lowticket', 'fiction'] as const;
const FULL = { width: '100%' };
const OPTIONAL_PRICE = { min: '0.000001', stringMode: true, style: FULL } as const;

type MarketForm = Omit<MarketProfile, 'kindle_categories'> & {
  categories: Array<{ topic: string; category: string }>;
};
interface SettingsForm extends Omit<RadarConfig, 'profiles'> {
  profiles: MarketForm[];
  secrets?: Partial<Record<SecretSource, { value?: string; remove?: boolean }>>;
}

function formValues(config: RadarSettingsView): SettingsForm {
  return {
    weights: config.weights, schedule: config.schedule, budget: config.budget,
    profiles: config.profiles.map(({ kindle_categories, ...profile }) => ({
      ...profile, categories: Object.entries(kindle_categories).map(([topic, category]) => ({ topic, category })),
    })),
  };
}

export function RadarSettings({ config, onSaved }: {
  config: RadarSettingsView;
  onSaved: (config: RadarSettingsView) => void;
}) {
  const { t } = useTranslation('radar');
  const [form] = Form.useForm<SettingsForm>();
  const [notifications, context] = message.useMessage();
  const [saving, setSaving] = useState(false);
  const [budget, setBudget] = useState<BudgetView | null>(null);
  const [checks, setChecks] = useState<Partial<Record<SourceName, SourceCheck>>>({});
  const [checking, setChecking] = useState<SourceName | null>(null);
  const [budgetError, setBudgetError] = useState(false);
  const typeOptions = TYPES.map(value => ({ value, label: t(`types.${value}`) }));
  const required = [{ required: true, message: t('required') }];

  useEffect(() => {
    const controller = new AbortController();
    radarApi.budget(controller.signal).then(value => {
      if (!controller.signal.aborted) { setBudget(value); setBudgetError(false); }
    }).catch(() => { if (!controller.signal.aborted) setBudgetError(true); });
    return () => controller.abort();
  }, [config.budget.monthly_limit_usd]);

  const save = async (values: SettingsForm) => {
    const weights = values.weights;
    if (weights.demand + weights.competition + weights.price !== 100) {
      void notifications.error(t('invalidWeights'));
      return;
    }
    const secrets: Partial<Record<SecretSource, string | null>> = {};
    SECRETS.forEach(source => {
      const edit = values.secrets?.[source];
      if (edit?.remove) secrets[source] = null;
      else if (edit?.value) secrets[source] = edit.value.trim();
    });
    setSaving(true);
    try {
      const stored = await radarApi.saveSettings({
        weights, schedule: values.schedule, budget: { ...config.budget, ...values.budget }, secrets,
        profiles: values.profiles.map(({ categories, price_references, ...profile }) => ({
          ...profile,
          kindle_categories: Object.fromEntries((categories ?? []).map(({ topic, category }) => [topic, category])),
          price_references: Object.fromEntries(Object.entries(price_references ?? {}).filter(([, value]) => value)),
        })),
      });
      form.resetFields();
      form.setFieldsValue(formValues(stored));
      setChecks({});
      onSaved(stored);
      void notifications.success(t('savedSettings'));
    } catch {
      void notifications.error(t('errorSave'));
    } finally {
      setSaving(false);
    }
  };

  const check = async (source: SourceName) => {
    setChecking(source);
    try {
      const response = await radarApi.checkSource(source);
      setChecks(current => ({ ...current, [source]: response }));
    } catch {
      void notifications.error(t('errorLoad'));
    } finally {
      setChecking(null);
    }
  };

  return <Form form={form} layout="vertical" initialValues={formValues(config)} onFinish={save}>
    {context}
    <Space direction="vertical" size="large" style={FULL}>
      <Card title={t('markets')} size="small">
        <Form.List name="profiles">{fields => <Collapse size="small" items={fields.map((field, index) => {
          const country = config.profiles[index].country;
          return {
            key: field.key, label: country,
            children: <>
              <Form.Item name={[field.name, 'country']} hidden><Input /></Form.Item>
              <Space wrap align="start">
                <Form.Item label={t('activeMarket')} name={[field.name, 'active']} valuePropName="checked"><Switch /></Form.Item>
                <Form.Item label={t('language')} name={[field.name, 'language']} rules={required}><Input /></Form.Item>
                <Form.Item label={t('currency')} name={[field.name, 'currency']} rules={required}><Input maxLength={3} /></Form.Item>
              </Space>
              <Form.Item label={t('sources')} name={[field.name, 'sources']}>
                <Select mode="multiple" options={SOURCES.map(value => ({ value, label: t(`sourcesByName.${value}`) }))} />
              </Form.Item>
              <Typography.Text strong>{t('coverage')}</Typography.Text>
              <Descriptions column={1} size="small" style={{ marginTop: 8 }}>
                {SOURCES.map(source => {
                  const coverage = config.coverage[country][source];
                  return <Descriptions.Item key={source} label={t(`sourcesByName.${source}`)}>
                    <Space wrap><Tag>{t(`coverageStatus.${coverage.status}`)}</Tag>{coverage.detail}</Space>
                  </Descriptions.Item>;
                })}
              </Descriptions>
              <Typography.Text strong>{t('reference')}</Typography.Text>
              <Space wrap align="start" style={{ marginTop: 8 }}>
                {TYPES.map(type => <Form.Item key={type} label={t(`types.${type}`)}
                  name={[field.name, 'price_references', type]}><InputNumber {...OPTIONAL_PRICE} /></Form.Item>)}
              </Space>
              <div><Typography.Text strong>{t('kindleCategories')}</Typography.Text></div>
              <Form.List name={[field.name, 'categories']}>{(categories, { add, remove }) => <>
                {categories.map(category => <Space key={category.key} wrap align="center" style={{ marginTop: 8 }}>
                  <Form.Item label={t('topic')} name={[category.name, 'topic']} rules={required}><Input /></Form.Item>
                  <Form.Item label={t('category')} name={[category.name, 'category']} rules={required}><Input /></Form.Item>
                  <Button onClick={() => remove(category.name)}>{t('removeCategory')}</Button>
                </Space>)}
                <div><Button type="dashed" size="small" onClick={() => add()} style={{ marginTop: 8 }}>
                  {t('addCategory')}
                </Button></div>
              </>}</Form.List>
            </>,
          };
        })} />}</Form.List>
      </Card>
      <Card title={t('weights')} size="small">
        <Space wrap>
          {(['demand', 'competition', 'price'] as const).map(key => <Form.Item key={key} label={t(`components.${key}`)}
            name={['weights', key]} rules={required}><InputNumber min={0} max={100} precision={0} /></Form.Item>)}
        </Space>
      </Card>
      <Card title={t('schedule')} size="small">
        <Typography.Paragraph type="secondary">{t('scheduleTiming')}</Typography.Paragraph>
        <Space wrap>
          <Form.Item name={['schedule', 'enabled']} label={t('scheduleEnabled')} valuePropName="checked"><Switch /></Form.Item>
          <Form.Item name={['schedule', 'timezone']} label={t('timezone')} rules={required}><Input /></Form.Item>
        </Space>
        <Form.List name={['schedule', 'entries']}>{(entries, { add, remove }) => <>
          {entries.map(entry => <div key={entry.key}><Space wrap align="center">
            <Form.Item label={t('topic')} name={[entry.name, 'topic']} rules={required}><Input maxLength={300} /></Form.Item>
            <Form.Item label={t('market')} name={[entry.name, 'country']} rules={required}>
              <Select style={{ width: 94 }} options={config.profiles.map(profile => ({ value: profile.country }))} />
            </Form.Item>
            <Form.Item label={t('productType')} name={[entry.name, 'product_type']} rules={required}>
              <Select style={{ minWidth: 144 }} options={typeOptions} />
            </Form.Item>
            <Button onClick={() => remove(entry.name)}>{t('removeEntry')}</Button>
          </Space></div>)}
          <Button type="dashed" disabled={entries.length >= 12}
            onClick={() => add({ country: 'BR', product_type: 'lowticket' })}>{t('addEntry')}</Button>
        </>}</Form.List>
      </Card>
      <Card title={t('credentials')} size="small">
        {!config.encryption_available && <Alert type="warning" showIcon message={t('encryptionUnavailable')} />}
        {SECRETS.map(source => {
          const credential = config.credentials[source];
          const status = credential.usable ? 'stored' : credential.present ? 'storedUnavailable' : 'missingSecret';
          return <div key={source} style={{ marginTop: 12 }}>
            <Space wrap><Typography.Text strong>{t(`sourcesByName.${source}`)}</Typography.Text><Tag>{t(status)}</Tag></Space>
            <div><Space wrap align="baseline">
              <Form.Item name={['secrets', source, 'value']} label={t('secretPlaceholder')}>
                <Input.Password disabled={!config.encryption_available} autoComplete="new-password" maxLength={1024} />
              </Form.Item>
              {credential.present && <Form.Item name={['secrets', source, 'remove']} valuePropName="checked">
                <Checkbox>{t('removeSecret')}</Checkbox>
              </Form.Item>}
            </Space></div>
          </div>;
        })}
        <Space direction="vertical" style={FULL}>
          {SOURCES.map(source => <div key={source}><Space wrap>
            <Button disabled={checking !== null} loading={checking === source} onClick={() => void check(source)}>
              {t('diagnose')} · {t(`sourcesByName.${source}`)}
            </Button>
            {checks[source] && <>
              <Typography.Text>{checks[source].detail}</Typography.Text>
              {checks[source].last_status && <Tag>
                {t('lastResult')} · {t(`sourceStatus.${checks[source].last_status}`)}
              </Tag>}
            </>}
          </Space></div>)}
        </Space>
      </Card>
      <Card title={t('budget')} size="small">
        <Form.Item label={t('monthlyLimit')} name={['budget', 'monthly_limit_usd']} rules={required}>
          <InputNumber min="0.000001" max="999999" stringMode />
        </Form.Item>
        {budgetError && <Alert type="error" message={t('errorLoad')} />}
        {budget && <>
          <Descriptions size="small" column={{ xs: 1, sm: 3 }}>
            {(['committed', 'charged', 'reserved'] as const).map(key => <Descriptions.Item key={key} label={t(key)}>
              {money(budget[`${key}_microusd`] / 1_000_000, 'USD')}
            </Descriptions.Item>)}
          </Descriptions>
          <Typography.Text type="secondary">{budget.month} UTC · {t('budgetPending', { count: budget.pending_count })}</Typography.Text>
          {budget.blocked && <Alert type="warning" message={t('budgetBlocked')} />}
        </>}
      </Card>
      <Button type="primary" htmlType="submit" loading={saving}>{t('save')}</Button>
    </Space>
  </Form>;
}

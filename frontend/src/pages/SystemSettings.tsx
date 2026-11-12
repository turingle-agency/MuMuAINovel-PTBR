import { useEffect, useState } from 'react';
import { Alert, Button, Card, Col, Form, Input, InputNumber, Row, Select, Space, Spin, Switch, Tabs, Typography, message, theme } from 'antd';
import { CheckCircleOutlined, MailOutlined, ReloadOutlined, SaveOutlined, SendOutlined, SettingOutlined } from '@ant-design/icons';
import { authApi, settingsApi } from '../services/api';
import type { SystemSMTPSettings, SystemSMTPSettingsUpdate, User } from '../types';
import { useTranslation } from 'react-i18next';

const { Title, Text, Paragraph } = Typography;
const { Option } = Select;

const qqDefaults: Pick<SystemSMTPSettings, 'smtp_provider' | 'smtp_host' | 'smtp_port' | 'smtp_use_ssl' | 'smtp_use_tls'> = {
  smtp_provider: 'qq',
  smtp_host: 'smtp.qq.com',
  smtp_port: 465,
  smtp_use_ssl: true,
  smtp_use_tls: false,
};

export default function SystemSettingsPage() {
  const { t } = useTranslation('systemSettings');
  const { token } = theme.useToken();
  const [form] = Form.useForm<SystemSMTPSettingsUpdate>();
  const [currentUser, setCurrentUser] = useState<User | null>(null);
  const [initialLoading, setInitialLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testTargetEmail, setTestTargetEmail] = useState('');

  const pageBackground = `linear-gradient(180deg, ${token.colorBgLayout} 0%, ${token.colorFillSecondary} 100%)`;
  const headerBackground = `linear-gradient(135deg, ${token.colorPrimary} 0%, ${token.colorPrimaryHover} 100%)`;
  const footerSafeOffset = 88;

  const loadData = async () => {
    setInitialLoading(true);
    try {
      const [user, smtpSettings] = await Promise.all([
        authApi.getCurrentUser(),
        settingsApi.getSystemSMTPSettings(),
      ]);
      setCurrentUser(user);
      form.setFieldsValue(smtpSettings);
    } catch (error) {
      console.error(t('falhaAoCarregarAsConfiguracoes'), error);
      message.error(t('falhaAoCarregarAsConfiguracoes2'));
    } finally {
      setInitialLoading(false);
    }
  };

  useEffect(() => {
    loadData();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleProviderChange = (value: string) => {
    if (value === 'qq') {
      form.setFieldsValue(qqDefaults);
    }
  };

  const handleSave = async (values: SystemSMTPSettingsUpdate) => {
    setSaving(true);
    try {
      const payload = values.smtp_provider === 'qq'
        ? {
            ...values,
            ...qqDefaults,
            smtp_username: values.smtp_username,
            smtp_password: values.smtp_password,
            smtp_from_email: values.smtp_from_email,
            smtp_from_name: values.smtp_from_name,
            email_auth_enabled: values.email_auth_enabled,
            email_register_enabled: values.email_register_enabled,
            verification_code_ttl_minutes: values.verification_code_ttl_minutes,
            verification_resend_interval_seconds: values.verification_resend_interval_seconds,
          }
        : values;
      const result = await settingsApi.updateSystemSMTPSettings(payload);
      form.setFieldsValue(result);
      message.success(t('configuracoesDeSmtpDoSistema'));
    } catch (error) {
      console.error(t('falhaAoSalvarAsConfiguracoes'), error);
      message.error(t('falhaAoSalvarAsConfiguracoes2'));
    } finally {
      setSaving(false);
    }
  };

  const handleTest = async () => {
    const toEmail = testTargetEmail.trim();
    if (!toEmail) {
      message.warning(t('informePrimeiroOEMail'));
      return;
    }

    setTesting(true);
    try {
      const result = await settingsApi.testSystemSMTPSettings({ to_email: toEmail });
      if (result.success) {
        message.success(result.message);
      } else {
        message.error(result.message || t('falhaNoTesteDeSmtp'));
      }
    } catch (error) {
      console.error(t('falhaAoTestarAConfiguracao'), error);
      message.error(t('falhaAoTestarAConfiguracao2'));
    } finally {
      setTesting(false);
    }
  };

  if (initialLoading) {
    return (
      <div style={{ minHeight: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center', background: token.colorBgLayout }}>
        <Spin size="large" />
      </div>
    );
  }

  if (!currentUser?.is_admin) {
    return (
      <div style={{ padding: 24 }}>
        <Alert type="error" showIcon message={t('semPermissaoDeAcesso')} description={t('somenteAdministradoresPodemAcessarAs')} />
      </div>
    );
  }

  return (
    <div
      style={{
        minHeight: `calc(100vh - ${footerSafeOffset}px)`,
        boxSizing: 'border-box',
        background: pageBackground,
        padding: 24,
        paddingBottom: footerSafeOffset,
      }}
    >
      <div style={{ maxWidth: 1400, margin: '0 auto', width: '100%' }}>
      <Card
        bordered={false}
        style={{
          marginBottom: 24,
          borderRadius: 20,
          overflow: 'hidden',
          boxShadow: `0 12px 32px ${token.colorFillSecondary}`,
        }}
        bodyStyle={{ padding: 0 }}
      >
        <div style={{ background: headerBackground, padding: '28px 32px', color: '#fff' }}>
          <Space direction="vertical" size={6}>
            <Space>
              <SettingOutlined />
              <Title level={3} style={{ color: '#fff', margin: 0 }}>{t('configuracoesDoSistema')}</Title>
            </Space>
            <Paragraph style={{ color: 'rgba(255,255,255,0.88)', margin: 0 }}>{t('visivelApenasParaAdministradoresUsado')}
            </Paragraph>
          </Space>
        </div>
      </Card>

      <Tabs
        defaultActiveKey="smtp"
        items={[
          {
            key: 'smtp',
            label: (
              <Space>
                <MailOutlined />{t('configuracaoDeSmtp')}
              </Space>
            ),
            children: (
              <Form form={form} layout="vertical" onFinish={handleSave}>
                <Row gutter={24}>
                  <Col xs={24} xl={16}>
                    <Card title={t('configuracaoDoServicoDeE')} bordered={false} style={{ borderRadius: 16 }}>
                      <Alert
                        type="info"
                        showIcon
                        style={{ marginBottom: 20 }}
                        message={t('comoConfigurarOQqMail')}
                        description={t('aoEscolherOQqMail')}
                      />

                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_provider" label={t('provedorDeEMail')} rules={[{ required: true, message: t('selecioneOProvedorDeE') }]}>
                            <Select onChange={handleProviderChange}>
                              <Option value="qq">{t('qqMail')}</Option>
                              <Option value="custom">{t('smtpPersonalizado')}</Option>
                            </Select>
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_host" label={t('servidorSmtp')} rules={[{ required: true, message: t('informeOServidorSmtp') }]}>
                            <Input placeholder={t('porExemploSmtpQqCom')} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_port" label={t('portaSmtp')} rules={[{ required: true, message: t('informeAPortaSmtp') }]}>
                            <InputNumber style={{ width: '100%' }} min={1} max={65535} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_username" label={t('usuarioSmtp')} rules={[{ required: true, message: t('informeOUsuarioSmtp') }]}>
                            <Input placeholder={t('enderecoDeEMailCompleto')} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_password" label={t('senhaSmtpCodigoDeAutorizacao')} rules={[{ required: true, message: t('informeOCodigoDeAutorizacao') }]}>
                            <Input.Password placeholder={t('paraOQqMailInforme')} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_from_email" label={t('eMailDoRemetente')}>
                            <Input placeholder={t('porPadraoPodeSerIgual')} />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_from_name" label={t('nomeDoRemetente')} rules={[{ required: true, message: t('informeONomeDoRemetente') }]}>
                            <Input placeholder="MuMuAINovel" />
                          </Form.Item>
                        </Col>
                      </Row>

                      <Row gutter={16}>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_use_ssl" label={t('ativarSsl')} valuePropName="checked">
                            <Switch />
                          </Form.Item>
                        </Col>
                        <Col xs={24} md={12}>
                          <Form.Item name="smtp_use_tls" label={t('ativarTls')} valuePropName="checked">
                            <Switch />
                          </Form.Item>
                        </Col>
                      </Row>
                    </Card>
                  </Col>

                  <Col xs={24} xl={8}>
                    <Card title={t('politicaDeCadastroECodigos')} bordered={false} style={{ borderRadius: 16, marginBottom: 24 }}>
                      <Form.Item name="email_auth_enabled" label={t('ativarAutenticacaoPorEMail')} valuePropName="checked">
                        <Switch />
                      </Form.Item>
                      <Form.Item name="email_register_enabled" label={t('ativarCadastroPorEMail')} valuePropName="checked">
                        <Switch />
                      </Form.Item>
                      <Form.Item name="verification_code_ttl_minutes" label={t('validadeDoCodigoMinutos')} rules={[{ required: true, message: t('informeAValidadeDoCodigo') }]}>
                        <InputNumber style={{ width: '100%' }} min={1} max={120} />
                      </Form.Item>
                      <Form.Item name="verification_resend_interval_seconds" label={t('intervaloParaReenviarOCodigo')} rules={[{ required: true, message: t('informeOIntervaloParaReenviar') }]}>
                        <InputNumber style={{ width: '100%' }} min={10} max={3600} />
                      </Form.Item>
                    </Card>

                    <Card title={t('acoes')} bordered={false} style={{ borderRadius: 16 }}>
                      <Space direction="vertical" style={{ width: '100%' }} size={12}>
                        <Input
                          value={testTargetEmail}
                          onChange={(e) => setTestTargetEmail(e.target.value)}
                          placeholder={t('informeOEMailDe')}
                        />
                        <Button icon={<ReloadOutlined />} onClick={loadData} block>{t('recarregar')}
                        </Button>
                        <Button icon={<SendOutlined />} loading={testing} onClick={handleTest} block>{t('enviarEMailDeTeste')}
                        </Button>
                        <Button type="primary" htmlType="submit" icon={<SaveOutlined />} loading={saving} block onClick={() => form.submit()}>{t('salvarConfiguracoesDoSistema')}
                        </Button>
                        <Alert
                          type="success"
                          showIcon
                          icon={<CheckCircleOutlined />}
                          message={t('recomendamosUsarAConfiguracaoPadrao')}
                          description={<Text type="secondary">{t('salvePrimeiroAConfiguracaoDe')}</Text>}
                        />
                      </Space>
                    </Card>
                  </Col>
                </Row>
              </Form>
            ),
          },
        ]}
      />
      </div>
    </div>
  );
}

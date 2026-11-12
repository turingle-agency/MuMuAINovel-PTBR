import { useEffect, useMemo, useState } from 'react';
import {
  Alert,
  Button,
  Card,
  Col,
  Divider,
  Form,
  Input,
  Layout,
  Row,
  Space,
  Spin,
  Tabs,
  Tag,
  Typography,
  message,
  theme,
} from 'antd';
import {
  BookOutlined,
  LockOutlined,
  MailOutlined,
  RobotOutlined,
  SafetyCertificateOutlined,
  TeamOutlined,
  ThunderboltOutlined,
  UserOutlined,
} from '@ant-design/icons';
import { authApi } from '../services/api';
import { useNavigate, useSearchParams } from 'react-router-dom';
import ThemeSwitch from '../components/ThemeSwitch';
import { useTranslation } from 'react-i18next';

const { Title, Paragraph, Text } = Typography;

interface AuthConfig {
  local_auth_enabled: boolean;
  email_auth_enabled: boolean;
  email_register_enabled: boolean;
}

interface LocalLoginValues {
  username: string;
  password: string;
}

interface EmailLoginValues {
  email: string;
  code: string;
}

interface EmailRegisterValues {
  email: string;
  code: string;
  password: string;
  confirmPassword: string;
  display_name?: string;
}

interface ResetPasswordValues {
  email: string;
  code: string;
  new_password: string;
  confirmNewPassword: string;
}

export default function Login() {
  const { t } = useTranslation('login');
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [loading, setLoading] = useState(false);
  const [checking, setChecking] = useState(true);
  const [authConfig, setAuthConfig] = useState<AuthConfig>({
    local_auth_enabled: false,
    email_auth_enabled: false,
    email_register_enabled: false,
  });
  const [localForm] = Form.useForm<LocalLoginValues>();
  const [emailLoginForm] = Form.useForm<EmailLoginValues>();
  const [emailRegisterForm] = Form.useForm<EmailRegisterValues>();
  const [resetPasswordForm] = Form.useForm<ResetPasswordValues>();
  const { token } = theme.useToken();
  const alphaColor = (color: string, alpha: number) => `color-mix(in srgb, ${color} ${(alpha * 100).toFixed(0)}%, transparent)`;
  const primaryButtonShadow = `0 8px 20px ${alphaColor(token.colorPrimary, 0.28)}`;
  const [loginCodeSending, setLoginCodeSending] = useState(false);
  const [registerCodeSending, setRegisterCodeSending] = useState(false);
  const [resetCodeSending, setResetCodeSending] = useState(false);
  const [loginCountdown, setLoginCountdown] = useState(0);
  const [registerCountdown, setRegisterCountdown] = useState(0);
  const [resetCountdown, setResetCountdown] = useState(0);
  const [showResetPassword, setShowResetPassword] = useState(false);

  const localAuthEnabled = authConfig.local_auth_enabled;
  const emailAuthEnabled = authConfig.email_auth_enabled;
  const emailRegisterEnabled = authConfig.email_register_enabled;

  useEffect(() => {
    const timers = [
      { value: loginCountdown, setter: setLoginCountdown },
      { value: registerCountdown, setter: setRegisterCountdown },
      { value: resetCountdown, setter: setResetCountdown },
    ].map(({ value, setter }) => {
      if (value <= 0) {
        return null;
      }

      return window.setInterval(() => {
        setter((prev) => {
          if (prev <= 1) {
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    });

    return () => {
      timers.forEach((timer) => {
        if (timer) {
          window.clearInterval(timer);
        }
      });
    };
  }, [loginCountdown, registerCountdown, resetCountdown]);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        await authApi.getCurrentUser();
        const redirect = searchParams.get('redirect') || '/';
        navigate(redirect);
      } catch {
        try {
          const config = await authApi.getAuthConfig();
          setAuthConfig(config);
        } catch (error) {
          console.error(t('falhaAoObterAConfiguracao'), error);
          setAuthConfig({
            local_auth_enabled: false,
            email_auth_enabled: false,
            email_register_enabled: false,
          });
        }
        setChecking(false);
      }
    };
    checkAuth();
  }, [navigate, searchParams, t]);

  const handleLoginSuccess = () => {
    message.success(t('loginRealizadoComSucesso'));

    const redirect = searchParams.get('redirect') || '/';
    navigate(redirect);
  };

  const handleLocalLogin = async (values: LocalLoginValues) => {
    try {
      setLoading(true);
      const response = await authApi.localLogin(values.username, values.password);
      if (response.success) {
        handleLoginSuccess();
      }
    } catch (error) {
      console.error(t('falhaNoLoginLocal'), error);
    } finally {
      setLoading(false);
    }
  };

  const handleEmailLogin = async (values: EmailLoginValues) => {
    try {
      setLoading(true);
      const response = await authApi.emailLogin({
        email: values.email,
        code: values.code,
      });
      if (response.success) {
        handleLoginSuccess();
      }
    } catch (error) {
      console.error(t('falhaNoLoginPorCodigo'), error);
    } finally {
      setLoading(false);
    }
  };

  const sendLoginCode = async () => {
    try {
      const values = await emailLoginForm.validateFields(['email']);
      setLoginCodeSending(true);
      const result = await authApi.sendEmailCode({ email: values.email, scene: 'login' });
      message.success(result.message || t('codigoDeVerificacaoEnviado'));
      setLoginCountdown(result.resend_interval_seconds || 60);
    } catch (error) {
      console.error(t('falhaAoEnviarOCodigo'), error);
    } finally {
      setLoginCodeSending(false);
    }
  };

  const sendRegisterCode = async () => {
    try {
      const values = await emailRegisterForm.validateFields(['email']);
      setRegisterCodeSending(true);
      const result = await authApi.sendEmailCode({ email: values.email, scene: 'register' });
      message.success(result.message || t('codigoDeVerificacaoEnviado'));
      setRegisterCountdown(result.resend_interval_seconds || 60);
    } catch (error) {
      console.error(t('falhaAoEnviarOCodigo2'), error);
    } finally {
      setRegisterCodeSending(false);
    }
  };

  const sendResetCode = async () => {
    try {
      const values = await resetPasswordForm.validateFields(['email']);
      setResetCodeSending(true);
      const result = await authApi.sendEmailCode({ email: values.email, scene: 'reset_password' });
      message.success(result.message || t('codigoDeVerificacaoEnviado'));
      setResetCountdown(result.resend_interval_seconds || 60);
    } catch (error) {
      console.error(t('falhaAoEnviarOCodigo3'), error);
    } finally {
      setResetCodeSending(false);
    }
  };

  const handleEmailRegister = async (values: EmailRegisterValues) => {
    try {
      setLoading(true);
      const response = await authApi.emailRegister({
        email: values.email,
        code: values.code,
        password: values.password,
        display_name: values.display_name?.trim() || undefined,
      });
      if (response.success) {
        message.success(t('cadastroConcluidoLoginFeitoAutomaticamen'));
        emailRegisterForm.resetFields(['code', 'password', 'confirmPassword']);
        setRegisterCountdown(0);
        handleLoginSuccess();
      }
    } catch (error) {
      console.error(t('falhaNoCadastroPorE'), error);
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async (values: ResetPasswordValues) => {
    try {
      setLoading(true);
      const result = await authApi.resetEmailPassword({
        email: values.email,
        code: values.code,
        new_password: values.new_password,
      });
      message.success(result.message || t('senhaRedefinidaComSucesso'));
      resetPasswordForm.resetFields(['code', 'new_password', 'confirmNewPassword']);
      setResetCountdown(0);
      setShowResetPassword(false);
    } catch (error) {
      console.error(t('falhaAoRedefinirASenha'), error);
    } finally {
      setLoading(false);
    }
  };

  const loginTips = useMemo(() => {
    const tips = [
    ];

    if (localAuthEnabled) {
      tips.unshift(t('contaPadraoDoLoginLocal'));
    }

    if (emailAuthEnabled) {
      tips.push(t('usuariosCadastradosPorEMail'));
    }

    return tips;
  }, [emailAuthEnabled, localAuthEnabled, t]);

  const featureItems = [
    {
      icon: <RobotOutlined />,
      title: t('variosModelosDeIaEm'),
      description: t('compativelComOpenaiGeminiClaude'),
    },
    {
      icon: <ThunderboltOutlined />,
      title: t('assistenteGuiadoInteligente'),
      description: t('geraAutomaticamenteOutlinePersonagensE'),
    },
    {
      icon: <TeamOutlined />,
      title: t('gestaoDePersonagensEOrganizacoes'),
      description: t('relacoesEntrePersonagensEEstruturas'),
    },
    {
      icon: <BookOutlined />,
      title: t('cicloCompletoDeCriacaoDe'),
      description: t('geracaoEdicaoReescritaERevisao'),
    },
  ];

  const renderLocalLogin = () => (
    <>
      <Form
        form={localForm}
        layout="vertical"
        onFinish={handleLocalLogin}
        size="large"
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="username"
          label={t('contaDeAdministrador')}
          rules={[{ required: true, message: t('informeAContaDeAdministrador') }]}
        >
          <Input
            prefix={<UserOutlined style={{ color: token.colorTextTertiary }} />}
            placeholder={t('informeAContaDeAdministrador')}
            autoComplete="username"
            style={{ height: 46, borderRadius: 12 }}
          />
        </Form.Item>
        <Form.Item
          name="password"
          label={t('chaveDeAcesso')}
          rules={[{ required: true, message: t('informeAChaveDeAcesso') }]}
        >
          <Input.Password
            prefix={<LockOutlined style={{ color: token.colorTextTertiary }} />}
            placeholder={t('informeAChaveDeAcesso')}
            autoComplete="current-password"
            style={{ height: 46, borderRadius: 12 }}
          />
        </Form.Item>
        <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            style={{
              height: 46,
              fontSize: 16,
              fontWeight: 600,
              background: `linear-gradient(90deg, ${token.colorPrimary} 0%, ${alphaColor(token.colorPrimary, 0.86)} 100%)`,
              border: 'none',
              borderRadius: '12px',
              boxShadow: primaryButtonShadow,
            }}
          >{t('entrar')}
          </Button>
        </Form.Item>
      </Form>

    </>
  );

  const renderEmailLogin = () => {
    if (showResetPassword) {
      return (
        <div style={{ marginTop: 16 }}>
          <Space direction="vertical" size={12} style={{ width: '100%' }}>
            <Space style={{ width: '100%', justifyContent: 'space-between' }}>
              <Title level={5} style={{ margin: 0 }}>{t('esqueciASenhaRedefinirSenha')}</Title>
              <Button type="link" style={{ paddingInline: 0 }} onClick={() => setShowResetPassword(false)}>{t('voltarAoLoginPorCodigo')}
              </Button>
            </Space>

            <Card size="small" bordered={false} style={{ borderRadius: 12, background: token.colorFillAlter }}>
              <Form
                form={resetPasswordForm}
                layout="vertical"
                onFinish={handleResetPassword}
                size="middle"
              >
                <Form.Item
                  name="email"
                  label={t('eMailCadastrado')}
                  rules={[
                    { required: true, message: t('informeOEMailCadastrado') },
                    { type: 'email', message: t('informeUmEnderecoDeE') },
                  ]}
                >
                  <Input prefix={<MailOutlined />} placeholder={t('informeOEMailCadastrado')} />
                </Form.Item>
                <Form.Item label={t('codigoDeRedefinicao')} required style={{ marginBottom: 12 }}>
                  <Space.Compact style={{ width: '100%' }}>
                    <Form.Item
                      name="code"
                      noStyle
                      rules={[
                        { required: true, message: t('informeOCodigoDeRedefinicao') },
                        { len: 6, message: t('oCodigoDeveTer6') },
                      ]}
                    >
                      <Input placeholder={t('informeOCodigoDeRedefinicao')} maxLength={6} />
                    </Form.Item>
                    <Button
                      onClick={sendResetCode}
                      loading={resetCodeSending}
                      disabled={resetCountdown > 0}
                    >
                      {resetCountdown > 0 ? t('reenviarEmS', { resetCountdown }) : t('enviarCodigo')}
                    </Button>
                  </Space.Compact>
                </Form.Item>
                <Form.Item
                  name="new_password"
                  label={t('novaSenha')}
                  rules={[
                    { required: true, message: t('informeANovaSenha') },
                    { min: 6, message: t('aSenhaDeveTerPelo') },
                  ]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder={t('informeANovaSenha')} />
                </Form.Item>
                <Form.Item
                  name="confirmNewPassword"
                  label={t('confirmarNovaSenha')}
                  dependencies={['new_password']}
                  rules={[
                    { required: true, message: t('informeANovaSenhaNovamente') },
                    ({ getFieldValue }) => ({
                      validator(_, value) {
                        if (!value || getFieldValue('new_password') === value) {
                          return Promise.resolve();
                        }
                        return Promise.reject(new Error(t('asNovasSenhasDigitadasNao')));
                      },
                    }),
                  ]}
                >
                  <Input.Password prefix={<LockOutlined />} placeholder={t('informeANovaSenhaNovamente')} />
                </Form.Item>
                <Button type="default" htmlType="submit" loading={loading} block>{t('redefinirSenha')}
                </Button>
              </Form>
            </Card>
          </Space>
        </div>
      );
    }

    return (
      <Form
        form={emailLoginForm}
        layout="vertical"
        onFinish={handleEmailLogin}
        size="large"
        style={{ marginTop: 16 }}
      >
        <Form.Item
          name="email"
          label={t('enderecoDeEMail')}
          rules={[
            { required: true, message: t('informeOEnderecoDeE') },
            { type: 'email', message: t('informeUmEnderecoDeE') },
          ]}
        >
          <Input
            prefix={<MailOutlined style={{ color: token.colorTextTertiary }} />}
            placeholder={t('informeOEMailCadastrado')}
            autoComplete="email"
            style={{ height: 46, borderRadius: 12 }}
          />
        </Form.Item>

        <Form.Item label={t('codigoDeLogin')} required style={{ marginBottom: 24 }}>
          <Space.Compact style={{ width: '100%' }}>
            <Form.Item
              name="code"
              noStyle
              rules={[
                { required: true, message: t('informeOCodigoDeLogin2') },
                { len: 6, message: t('oCodigoDeveTer6') },
              ]}
            >
              <Input
                prefix={<SafetyCertificateOutlined style={{ color: token.colorTextTertiary }} />}
                placeholder={t('informeOCodigoDeLogin')}
                maxLength={6}
                style={{ height: 46, borderRadius: '12px 0 0 12px' }}
              />
            </Form.Item>
            <Button
              style={{ height: 46 }}
              onClick={sendLoginCode}
              loading={loginCodeSending}
              disabled={loginCountdown > 0}
            >
              {loginCountdown > 0 ? t('reenviarEmS2', { loginCountdown }) : t('enviarCodigo')}
            </Button>
          </Space.Compact>
        </Form.Item>

        <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
          <Button
            type="primary"
            htmlType="submit"
            loading={loading}
            block
            style={{
              height: 46,
              fontSize: 16,
              fontWeight: 600,
              background: `linear-gradient(90deg, ${token.colorPrimary} 0%, ${alphaColor(token.colorPrimary, 0.86)} 100%)`,
              border: 'none',
              borderRadius: '12px',
              boxShadow: primaryButtonShadow,
            }}
          >{t('entrarComCodigo')}
          </Button>
        </Form.Item>

        <div style={{ marginTop: 12, textAlign: 'right' }}>
          <Button type="link" style={{ paddingInline: 0 }} onClick={() => setShowResetPassword(true)}>{t('esqueceuASenhaCliquePara')}
          </Button>
        </div>
      </Form>
    );
  };

  const renderEmailRegister = () => (
    <Form
      form={emailRegisterForm}
      layout="vertical"
      onFinish={handleEmailRegister}
      size="large"
      style={{ marginTop: 16 }}
    >
      <Form.Item
        name="email"
        label={t('eMailCadastrado')}
        rules={[
          { required: true, message: t('informeOEMailCadastrado') },
          { type: 'email', message: t('informeUmEnderecoDeE') },
        ]}
      >
        <Input
          prefix={<MailOutlined style={{ color: token.colorTextTertiary }} />}
          placeholder={t('informeOEMailCadastrado')}
          autoComplete="email"
          style={{ height: 46, borderRadius: 12 }}
        />
      </Form.Item>

      <Form.Item label={t('codigoDoEMail')} required style={{ marginBottom: 12 }}>
        <Space.Compact style={{ width: '100%' }}>
          <Form.Item
            name="code"
            noStyle
            rules={[
              { required: true, message: t('informeOCodigoEnviadoPor') },
              { len: 6, message: t('oCodigoDeveTer6') },
            ]}
          >
            <Input
              prefix={<SafetyCertificateOutlined style={{ color: token.colorTextTertiary }} />}
              placeholder={t('informeOCodigoDe6')}
              maxLength={6}
              style={{ height: 46, borderRadius: '12px 0 0 12px' }}
            />
          </Form.Item>
          <Button
            style={{ height: 46 }}
            onClick={sendRegisterCode}
            loading={registerCodeSending}
            disabled={registerCountdown > 0}
          >
            {registerCountdown > 0 ? t('reenviarEmS3', { registerCountdown }) : t('enviarCodigo')}
          </Button>
        </Space.Compact>
      </Form.Item>

      <Form.Item
        name="display_name"
        label={t('apelido')}
        rules={[{ max: 50, message: t('oApelidoNaoPodeTer') }]}
      >
        <Input
          prefix={<UserOutlined style={{ color: token.colorTextTertiary }} />}
          placeholder={t('opcionalPorPadraoUsaO')}
          autoComplete="nickname"
          style={{ height: 46, borderRadius: 12 }}
        />
      </Form.Item>

      <Form.Item
        name="password"
        label={t('senhaDeLogin')}
        rules={[
          { required: true, message: t('informeASenhaDeLogin') },
          { min: 6, message: t('aSenhaDeveTerPelo') },
        ]}
      >
        <Input.Password
          prefix={<LockOutlined style={{ color: token.colorTextTertiary }} />}
          placeholder={t('informeASenhaDeLogin')}
          autoComplete="new-password"
          style={{ height: 46, borderRadius: 12 }}
        />
      </Form.Item>

      <Form.Item
        name="confirmPassword"
        label={t('confirmarSenha')}
        dependencies={['password']}
        rules={[
          { required: true, message: t('informeASenhaDeLogin2') },
          ({ getFieldValue }) => ({
            validator(_, value) {
              if (!value || getFieldValue('password') === value) {
                return Promise.resolve();
              }
              return Promise.reject(new Error(t('asSenhasDigitadasNaoCoincidem')));
            },
          }),
        ]}
      >
        <Input.Password
          prefix={<LockOutlined style={{ color: token.colorTextTertiary }} />}
          placeholder={t('informeASenhaDeLogin2')}
          autoComplete="new-password"
          style={{ height: 46, borderRadius: 12 }}
        />
      </Form.Item>

      <Form.Item style={{ marginBottom: 0, marginTop: 8 }}>
        <Button
          type="primary"
          htmlType="submit"
          loading={loading}
          block
          style={{
            height: 46,
            fontSize: 16,
            fontWeight: 600,
            background: `linear-gradient(90deg, ${token.colorPrimary} 0%, ${alphaColor(token.colorPrimary, 0.86)} 100%)`,
            border: 'none',
            borderRadius: '12px',
            boxShadow: primaryButtonShadow,
          }}
        >{t('cadastrarEEntrar')}
        </Button>
      </Form.Item>

      <Text type="secondary" style={{ marginTop: 12, display: 'block' }}>{t('oCodigoSeraEnviadoAo')}
      </Text>
    </Form>
  );

  const authTabs = [
    ...(localAuthEnabled
      ? [
          {
            key: 'local-login',
            label: t('loginLocal'),
            children: renderLocalLogin(),
          },
        ]
      : []),
    ...(emailAuthEnabled
      ? [
          {
            key: 'email-login',
            label: t('loginPorEMail'),
            children: renderEmailLogin(),
          },
        ]
      : []),
    ...(emailAuthEnabled && emailRegisterEnabled
      ? [
          {
            key: 'email-register',
            label: t('cadastroPorEMail'),
            children: renderEmailRegister(),
          },
        ]
      : []),
  ];

  if (checking) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          background: token.colorBgLayout,
        }}
      >
        <Spin size="large" style={{ color: token.colorPrimary }} />
      </div>
    );
  }

  return (
    <>
      <Layout style={{ minHeight: '100vh', background: token.colorBgLayout }}>
        <div
          style={{
            position: 'fixed',
            top: 20,
            right: 20,
            zIndex: 10,
            padding: '8px 10px',
            borderRadius: 12,
            background: alphaColor(token.colorBgContainer, 0.9),
            border: `1px solid ${token.colorBorderSecondary}`,
            backdropFilter: 'blur(6px)',
          }}
        >
          <ThemeSwitch size="small" />
        </div>
        <Row style={{ minHeight: '100vh' }}>
          <Col xs={0} lg={11}>
            <section
              style={{
                height: '100%',
                padding: '44px 64px 88px',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between',
                position: 'relative',
                overflow: 'hidden',
                backgroundColor: alphaColor(token.colorBgContainer, 0.78),
                backgroundImage: `linear-gradient(${alphaColor(token.colorTextSecondary, 0.06)} 1px, transparent 1px), linear-gradient(90deg, ${alphaColor(token.colorTextSecondary, 0.06)} 1px, transparent 1px)`,
                backgroundSize: '68px 68px',
              }}
            >
              <div
                style={{
                  position: 'absolute',
                  inset: 0,
                  background: `radial-gradient(circle at 25% 20%, ${alphaColor(token.colorPrimary, 0.12)} 0%, transparent 50%)`,
                  pointerEvents: 'none',
                }}
              />

              <div
                style={{
                  position: 'relative',
                  zIndex: 1,
                  display: 'flex',
                  flexDirection: 'column',
                  justifyContent: 'space-between',
                  gap: 34,
                  width: '100%',
                }}
              >
                <Space align="center" size={14}>
                  <div
                    style={{
                      width: 46,
                      height: 46,
                      borderRadius: 14,
                      background: `linear-gradient(135deg, ${token.colorPrimary} 0%, ${alphaColor(token.colorPrimary, 0.7)} 100%)`,
                      display: 'flex',
                      alignItems: 'center',
                      justifyContent: 'center',
                      boxShadow: primaryButtonShadow,
                    }}
                  >
                    <img
                      src="/logo.svg"
                      alt="MuMuAINovel"
                      style={{ width: 26, height: 26, filter: 'brightness(0) invert(1)' }}
                    />
                  </div>
                  <Title level={3} style={{ margin: 0, color: token.colorText }}>
                    MuMuAINovel
                  </Title>
                </Space>

                <Space direction="vertical" size={32} style={{ width: '100%' }}>
                  <div style={{ maxWidth: 'min(860px, 100%)' }}>
                    <Title
                      level={1}
                      style={{
                        marginBottom: 22,
                        color: token.colorText,
                        lineHeight: 1.12,
                        fontWeight: 800,
                        fontSize: 'clamp(52px, 3vw, 78px)',
                      }}
                    >{t('comBaseEmIa')}
                      <br />
                      <span
                        style={{
                          backgroundImage: `linear-gradient(90deg, ${token.colorPrimary} 0%, #d946ef 100%)`,
                          WebkitBackgroundClip: 'text',
                          backgroundClip: 'text',
                          WebkitTextFillColor: 'transparent',
                          color: token.colorPrimary,
                        }}
                      >{t('oAssistenteInteligenteDeCriacao')}
                      </span>
                    </Title>
                    <Paragraph
                      style={{
                        fontSize: 'clamp(18px, 1vw, 22px)',
                        lineHeight: 1.85,
                        color: token.colorTextSecondary,
                        marginBottom: 0,
                        maxWidth: 800,
                      }}
                    >{t('daInspiracaoAoTextoFinal')}
                    </Paragraph>
                  </div>

                  <Row gutter={[20, 20]} style={{ width: '100%', maxWidth: 'min(920px, 100%)' }}>
                    {featureItems.map((item) => (
                      <Col span={12} key={item.title}>
                        <Card
                          size="small"
                          bordered={false}
                          style={{
                            height: '100%',
                            minHeight: 120,
                            borderRadius: 16,
                            background: alphaColor(token.colorBgContainer, 0.9),
                          }}
                          bodyStyle={{ padding: 16 }}
                        >
                          <Space direction="vertical" size={8}>
                            <Space size={10} style={{ color: token.colorPrimary, fontWeight: 700, fontSize: 15 }}>
                              {item.icon}
                              <span>{item.title}</span>
                            </Space>
                            <Paragraph style={{ marginBottom: 0, color: token.colorTextSecondary, fontSize: 14, lineHeight: 1.65 }}>
                              {item.description}
                            </Paragraph>
                          </Space>
                        </Card>
                      </Col>
                    ))}
                  </Row>
                </Space>

                <Space size={[10, 14]} wrap style={{ maxWidth: 'min(860px, 100%)' }}>
                  <Tag color="blue">OpenAI</Tag>
                  <Tag color="geekblue">Gemini</Tag>
                  <Tag color="purple">Claude</Tag>
                  <Tag color="green">Docker Compose</Tag>
                  <Tag color="gold">PostgreSQL</Tag>
                </Space>
              </div>

              <Paragraph
                style={{
                  marginBottom: 0,
                  fontSize: 12,
                  color: token.colorTextTertiary,
                  position: 'relative',
                  zIndex: 1,
                  letterSpacing: 0.4,
                }}
              >
                © 2026 MuMuAINovel · GPLv3 License
              </Paragraph>
            </section>
          </Col>

          <Col xs={24} lg={13}>
            <section
              style={{
                minHeight: '100vh',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                padding: '48px min(7vw, 72px)',
                background: token.colorBgLayout,
              }}
            >
              <div style={{ width: '100%', maxWidth: 520 }}>
                <Space direction="vertical" size={4}>
                  <Title level={2} style={{ marginBottom: 0, fontWeight: 700, color: token.colorText }}>{t('bemVindoDeVolta')}
                  </Title>
                  <Paragraph style={{ marginBottom: 0, color: token.colorTextSecondary }}>{t('entreNoMumuainovelEContinue')}
                  </Paragraph>
                </Space>

                <div style={{ marginTop: 22 }}>
                  {authTabs.length > 0 ? (
                    <Tabs defaultActiveKey={authTabs[0].key} items={authTabs} />
                  ) : null}

                  {!localAuthEnabled && !emailAuthEnabled ? (
                    <Alert
                      type="warning"
                      showIcon
                      message={t('nenhumaFormaDeLoginEsta')}
                      description={t('pecaAoAdministradorParaAtivar')}
                    />
                  ) : null}

                  {emailAuthEnabled && !emailRegisterEnabled ? (
                    <Alert
                      type="info"
                      showIcon
                      style={{ marginTop: 12, borderRadius: 12 }}
                      message={t('oCadastroPorEMail')}
                      description={t('noMomentoSoEstaoDisponiveis')}
                    />
                  ) : null}

                  <Divider style={{ margin: '20px 0 14px' }} />
                  <Alert
                    type="info"
                    showIcon
                    icon={<SafetyCertificateOutlined />}
                    style={{ background: alphaColor(token.colorPrimary, 0.06), borderRadius: 12 }}
                    message={t('informacoesDeLogin')}
                    description={(
                      <ul style={{ margin: 0, paddingLeft: 18 }}>
                        {loginTips.map((tip) => (
                          <li key={tip} style={{ marginBottom: 4 }}>
                            {tip}
                          </li>
                        ))}
                      </ul>
                    )}
                  />
                </div>
              </div>
            </section>
          </Col>
        </Row>
      </Layout>
    </>
  );
}

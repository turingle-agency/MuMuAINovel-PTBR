/**
 * Informações de versão da aplicação.
 * Segue o versionamento semântico (SemVer).
 */

export const VERSION_INFO = {
  // Versão da aplicação (injetada no build via VITE_APP_VERSION)
  version: import.meta.env.VITE_APP_VERSION || '1.5.8',

  // Data do build (injetada no build pelo Vite)
  buildTime: import.meta.env.VITE_BUILD_TIME || new Date().toISOString().split('T')[0],

  // Projeto
  projectName: 'MuMuAINovel',
  projectFullName: 'MuMuAINovel PT-BR',

  // Links
  githubUrl: 'https://github.com/turingle-agency/MuMuAINovel-PTBR',

  // Licença
  license: 'GPL v3.0',
  licenseUrl: 'https://www.gnu.org/licenses/gpl-3.0.html',

  // Projeto original
  author: 'xiamuceer-j',
};

/** Versão formatada (ex.: v1.5.8). */
export const getVersionString = () => {
  return `v${VERSION_INFO.version}`;
};

/** Descrição completa da versão. */
export const getFullVersionInfo = () => {
  return `${VERSION_INFO.projectName} ${getVersionString()} - Build ${VERSION_INFO.buildTime}`;
};

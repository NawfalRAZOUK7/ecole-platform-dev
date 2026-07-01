import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import boundaries from 'eslint-plugin-boundaries';
import tseslint from 'typescript-eslint';

const architectureLintEnabled =
  process.env.ARCHITECTURE_LINT === 'true' || process.env.ARCHITECTURE_STRICT === 'true';
const architectureSeverity = process.env.ARCHITECTURE_STRICT === 'true' ? 'error' : 'warn';

export default tseslint.config(
  { ignores: ['dist', 'coverage'] },
  {
    extends: [js.configs.recommended, ...tseslint.configs.recommended],
    files: ['src/**/*.{ts,tsx}', 'e2e/**/*.ts', 'vite.config.ts', 'playwright.config.ts'],
    languageOptions: {
      ecmaVersion: 2020,
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      'react-hooks': reactHooks,
      'react-refresh': reactRefresh,
      ...(architectureLintEnabled ? { boundaries } : {}),
    },
    settings: architectureLintEnabled
      ? {
          'boundaries/elements': [
            { type: 'app', pattern: 'src/app/**' },
            { type: 'pages', pattern: 'src/pages/**' },
            { type: 'widgets', pattern: 'src/widgets/**' },
            { type: 'features', pattern: 'src/features/**' },
            { type: 'entities', pattern: 'src/entities/**' },
            { type: 'shared', pattern: 'src/shared/**' },
          ],
        }
      : {},
    rules: {
      ...reactHooks.configs.recommended.rules,
      'react-hooks/exhaustive-deps': 'off',
      'react-refresh/only-export-components': 'off',
      ...(architectureLintEnabled
        ? {
            'boundaries/dependencies': [
              architectureSeverity,
              {
                default: 'allow',
                rules: [
                  {
                    from: { type: 'shared' },
                    disallow: {
                      to: { type: ['app', 'pages', 'widgets', 'features', 'entities'] },
                    },
                  },
                  {
                    from: { type: 'entities' },
                    disallow: { to: { type: ['app', 'pages', 'widgets', 'features'] } },
                  },
                  {
                    from: { type: 'features' },
                    disallow: { to: { type: ['app', 'pages', 'widgets'] } },
                  },
                  {
                    from: { type: 'widgets' },
                    disallow: { to: { type: ['app', 'pages'] } },
                  },
                  {
                    from: { type: 'pages' },
                    disallow: { to: { type: ['pages'] } },
                  },
                ],
              },
            ],
            'no-restricted-imports': [
              architectureSeverity,
              {
                patterns: [
                  {
                    group: [
                      '@/features/*/*/api/*',
                      '@/features/*/*/model/*',
                      '@/features/*/*/ui/*',
                      '@/features/*/*/lib/*',
                      '@/features/*/api/*',
                      '@/features/*/model/*',
                      '@/features/*/ui/*',
                      '@/features/*/lib/*',
                      '@/entities/*/*/api/*',
                      '@/entities/*/*/model/*',
                      '@/entities/*/*/ui/*',
                      '@/widgets/*/ui/*',
                    ],
                    message: 'Use the module index.ts public API instead of deep imports.',
                  },
                ],
              },
            ],
          }
        : {}),
    },
  },
);

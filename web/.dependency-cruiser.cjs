module.exports = {
  forbidden: [
    {
      name: 'no-circular',
      severity: 'error',
      comment: 'Circular dependencies make FSD layer ownership ambiguous.',
      from: {},
      to: { circular: true },
    },
    {
      name: 'shared-is-foundational',
      severity: 'error',
      from: { path: '^src/shared/' },
      to: { path: '^src/(app|pages|widgets|features|entities)/' },
    },
    {
      name: 'entities-do-not-import-higher-layers',
      severity: 'error',
      from: { path: '^src/entities/' },
      to: { path: '^src/(app|pages|widgets|features)/' },
    },
    {
      name: 'features-do-not-import-higher-layers',
      severity: 'error',
      from: { path: '^src/features/' },
      to: { path: '^src/(app|pages|widgets)/' },
    },
    {
      name: 'widgets-do-not-import-higher-layers',
      severity: 'error',
      from: { path: '^src/widgets/' },
      to: { path: '^src/(app|pages)/' },
    },
    {
      name: 'pages-do-not-import-pages',
      severity: 'error',
      from: { path: '^src/pages/', pathNot: '^src/pages/index\\.ts$' },
      to: { path: '^src/pages/' },
    },
  ],
  options: {
    doNotFollow: {
      path: 'node_modules',
    },
    exclude: {
      path: '^(dist|coverage|node_modules|tests|e2e)/',
    },
    tsPreCompilationDeps: true,
    tsConfig: {
      fileName: 'tsconfig.json',
    },
    enhancedResolveOptions: {
      extensions: ['.ts', '.tsx', '.js', '.jsx', '.json'],
    },
  },
};

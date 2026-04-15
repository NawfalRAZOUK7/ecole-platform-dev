import { existsSync, readdirSync, readFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import * as ts from 'typescript';
import { describe, expect, it } from 'vitest';

type HttpMethod = 'DELETE' | 'GET' | 'PATCH' | 'POST' | 'PUT';

interface OpenApiSpec {
  paths: Record<string, Record<string, unknown>>;
}

interface EndpointRef {
  file: string;
  method: HttpMethod;
  path: string;
  comparePath: string;
}

interface Mismatch {
  endpoint: EndpointRef;
  reason: string;
  openApiPath?: string;
  availableMethods?: string[];
}

const CURRENT_DIR = dirname(fileURLToPath(import.meta.url));
const REPO_ROOT = resolve(CURRENT_DIR, '../../..');
const WEB_SRC_ROOT = resolve(REPO_ROOT, 'web/src');
const OPENAPI_PATH = resolve(REPO_ROOT, 'backend/openapi.json');
const COMMITTED_OPENAPI_PATH = resolve(REPO_ROOT, 'backend/docs/openapi.json');
const OPENAPI_SUPPLEMENT_PATH = resolve(REPO_ROOT, 'web/tests/contract/openapi-supplement.json');
const GENERATE_OPENAPI_SCRIPT = resolve(REPO_ROOT, 'scripts/generate-openapi.sh');
const STRICT_API_CONTRACT = process.env.STRICT_API_CONTRACT !== 'false';
const METHOD_BY_API_HELPER: Record<string, HttpMethod> = {
  delete: 'DELETE',
  get: 'GET',
  list: 'GET',
  patch: 'PATCH',
  post: 'POST',
  put: 'PUT',
};

function normalizeComparePath(path: string) {
  return path.replace(/\{[^/}]+\}/g, '{}');
}

function finalizePath(rawPath: string, source: 'api' | 'direct') {
  let path = rawPath.trim();
  if (!path) {
    return null;
  }

  if (source === 'api') {
    path = path.startsWith('/api/v1') ? path : `/api/v1${path.startsWith('/') ? path : `/${path}`}`;
  }

  if (/^https?:\/\//.test(path)) {
    path = new URL(path).pathname;
  }

  path = path.split('?')[0] || path;
  path = path.replace(/\/{2,}/g, '/');

  if (path.length > 1 && path.endsWith('/')) {
    path = path.slice(0, -1);
  }

  if (!path.startsWith('/api/v1')) {
    return null;
  }

  if (/^\/api\/v1\{[^/]+/.test(path)) {
    return null;
  }

  return path;
}

function listServiceFiles(dir: string): string[] {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      return listServiceFiles(fullPath);
    }
    return entry.name.endsWith('.service.ts') ? [fullPath] : [];
  });
}

function readOpenApiSpec(): OpenApiSpec {
  const result = spawnSync('sh', [GENERATE_OPENAPI_SCRIPT], {
    cwd: REPO_ROOT,
    encoding: 'utf8',
  });

  if (result.status !== 0 && !existsSync(OPENAPI_PATH) && !existsSync(COMMITTED_OPENAPI_PATH)) {
    throw new Error(
      [
        'Failed to generate backend/openapi.json for contract tests.',
        result.stdout.trim(),
        result.stderr.trim(),
      ]
        .filter(Boolean)
        .join('\n'),
    );
  }

  const specPath = existsSync(OPENAPI_PATH) ? OPENAPI_PATH : COMMITTED_OPENAPI_PATH;
  const spec = JSON.parse(readFileSync(specPath, 'utf8')) as OpenApiSpec;

  if (!existsSync(OPENAPI_SUPPLEMENT_PATH)) {
    return spec;
  }

  const supplement = JSON.parse(readFileSync(OPENAPI_SUPPLEMENT_PATH, 'utf8')) as OpenApiSpec;
  const mergedPaths: OpenApiSpec['paths'] = { ...spec.paths };

  for (const [path, operations] of Object.entries(supplement.paths)) {
    mergedPaths[path] = {
      ...(mergedPaths[path] ?? {}),
      ...operations,
    };
  }

  return {
    ...spec,
    paths: mergedPaths,
  };
}

function getPropertyName(node: ts.PropertyName | ts.MemberName) {
  if (ts.isIdentifier(node) || ts.isStringLiteral(node) || ts.isNumericLiteral(node)) {
    return node.text;
  }
  return null;
}

function getMethodFromOptions(node: ts.Expression | undefined, context: Map<string, string>) {
  if (!node || !ts.isObjectLiteralExpression(node)) {
    return 'GET' as HttpMethod;
  }

  for (const property of node.properties) {
    if (!ts.isPropertyAssignment(property)) {
      continue;
    }
    if (getPropertyName(property.name) !== 'method') {
      continue;
    }

    const value = extractPathExpression(property.initializer, context);
    const method = value?.toUpperCase();
    if (method && ['DELETE', 'GET', 'PATCH', 'POST', 'PUT'].includes(method)) {
      return method as HttpMethod;
    }
  }

  return 'GET' as HttpMethod;
}

function extractDynamicPart(node: ts.Expression, context: Map<string, string>): string {
  if (ts.isIdentifier(node)) {
    return context.get(node.text) ?? `{${node.text}}`;
  }

  if (
    ts.isStringLiteral(node) ||
    ts.isNoSubstitutionTemplateLiteral(node) ||
    ts.isNumericLiteral(node)
  ) {
    return node.text;
  }

  if (ts.isConditionalExpression(node)) {
    const whenTrue = extractPathExpression(node.whenTrue, context) ?? '';
    const whenFalse = extractPathExpression(node.whenFalse, context) ?? '';
    if ([whenTrue, whenFalse].every((value) => value === '' || value.startsWith('?'))) {
      return '';
    }
    return '{param}';
  }

  if (
    ts.isAsExpression(node) ||
    ts.isTypeAssertionExpression(node) ||
    ts.isParenthesizedExpression(node) ||
    ts.isNonNullExpression(node)
  ) {
    return extractDynamicPart(node.expression, context);
  }

  return '{param}';
}

function extractPathExpression(
  node: ts.Expression | undefined,
  context: Map<string, string>,
): string | null {
  if (!node) {
    return null;
  }

  if (ts.isStringLiteral(node) || ts.isNoSubstitutionTemplateLiteral(node)) {
    return node.text;
  }

  if (
    ts.isAsExpression(node) ||
    ts.isTypeAssertionExpression(node) ||
    ts.isParenthesizedExpression(node) ||
    ts.isNonNullExpression(node)
  ) {
    return extractPathExpression(node.expression, context);
  }

  if (ts.isIdentifier(node)) {
    return context.get(node.text) ?? null;
  }

  if (ts.isTemplateExpression(node)) {
    let value = node.head.text;
    for (const span of node.templateSpans) {
      value += `${extractDynamicPart(span.expression, context)}${span.literal.text}`;
    }
    return value;
  }

  if (ts.isBinaryExpression(node) && node.operatorToken.kind === ts.SyntaxKind.PlusToken) {
    const left = extractPathExpression(node.left, context);
    const right = extractPathExpression(node.right, context);
    return left && right ? `${left}${right}` : null;
  }

  if (
    ts.isCallExpression(node) &&
    ts.isPropertyAccessExpression(node.expression) &&
    node.expression.name.text === 'toString'
  ) {
    return extractPathExpression(node.expression.expression, context);
  }

  if (
    ts.isNewExpression(node) &&
    ts.isIdentifier(node.expression) &&
    node.expression.text === 'URL'
  ) {
    return extractPathExpression(node.arguments?.[0], context);
  }

  return null;
}

function collectHelperFunctions(sourceFile: ts.SourceFile) {
  const helpers = new Map<string, ts.FunctionLikeDeclaration>();

  for (const statement of sourceFile.statements) {
    if (ts.isFunctionDeclaration(statement) && statement.name) {
      helpers.set(statement.name.text, statement);
      continue;
    }

    if (!ts.isVariableStatement(statement)) {
      continue;
    }

    for (const declaration of statement.declarationList.declarations) {
      if (!ts.isIdentifier(declaration.name) || !declaration.initializer) {
        continue;
      }

      if (
        ts.isArrowFunction(declaration.initializer) ||
        ts.isFunctionExpression(declaration.initializer)
      ) {
        helpers.set(declaration.name.text, declaration.initializer);
      }
    }
  }

  return helpers;
}

function buildFunctionContext(
  baseContext: Map<string, string>,
  params: readonly ts.ParameterDeclaration[],
  args?: readonly ts.Expression[],
) {
  const next = new Map(baseContext);

  params.forEach((param, index) => {
    if (!ts.isIdentifier(param.name)) {
      return;
    }

    const argValue = args ? extractPathExpression(args[index], baseContext) : null;
    next.set(param.name.text, argValue ?? `{${param.name.text}}`);
  });

  return next;
}

function extractEndpointsFromCall(
  node: ts.CallExpression,
  context: Map<string, string>,
): Array<{ method: HttpMethod; path: string }> {
  const endpoints: Array<{ method: HttpMethod; path: string }> = [];

  if (
    ts.isPropertyAccessExpression(node.expression) &&
    ts.isIdentifier(node.expression.expression) &&
    node.expression.expression.text === 'api'
  ) {
    const method = METHOD_BY_API_HELPER[node.expression.name.text];
    const rawPath = extractPathExpression(node.arguments[0], context);
    if (method && rawPath) {
      const path = finalizePath(rawPath, 'api');
      if (path) {
        endpoints.push({ method, path });
      }
    }
  }

  if (
    ts.isPropertyAccessExpression(node.expression) &&
    node.expression.name.text === 'open' &&
    ts.isIdentifier(node.expression.expression)
  ) {
    const method = extractPathExpression(node.arguments[0], context)?.toUpperCase();
    const rawPath = extractPathExpression(node.arguments[1], context);
    if (method && rawPath && ['DELETE', 'GET', 'PATCH', 'POST', 'PUT'].includes(method)) {
      const path = finalizePath(rawPath, 'direct');
      if (path) {
        endpoints.push({ method: method as HttpMethod, path });
      }
    }
  }

  if (ts.isIdentifier(node.expression) && node.expression.text === 'fetch') {
    const rawPath = extractPathExpression(node.arguments[0], context);
    const method = getMethodFromOptions(node.arguments[1], context);
    if (rawPath) {
      const path = finalizePath(rawPath, 'direct');
      if (path) {
        endpoints.push({ method, path });
      }
    }
  }

  return endpoints;
}

function extractEndpointsFromNewExpression(
  node: ts.NewExpression,
  context: Map<string, string>,
): Array<{ method: HttpMethod; path: string }> {
  if (!ts.isIdentifier(node.expression) || node.expression.text !== 'URL') {
    return [];
  }

  const rawPath = extractPathExpression(node.arguments?.[0], context);
  const path = rawPath ? finalizePath(rawPath, 'direct') : null;
  return path ? [{ method: 'GET', path }] : [];
}

function extractEndpointsForFile(filePath: string) {
  const sourceText = readFileSync(filePath, 'utf8');
  const sourceFile = ts.createSourceFile(filePath, sourceText, ts.ScriptTarget.Latest, true);
  const helpers = collectHelperFunctions(sourceFile);
  const endpoints: EndpointRef[] = [];
  const seen = new Set<string>();

  const recordEndpoint = (method: HttpMethod, path: string) => {
    const comparePath = normalizeComparePath(path);
    const file = relative(REPO_ROOT, filePath);
    const key = `${file}:${method}:${comparePath}`;
    if (seen.has(key)) {
      return;
    }
    seen.add(key);
    endpoints.push({ file, method, path, comparePath });
  };

  const scanNode = (node: ts.Node, context: Map<string, string>, depth = 0): void => {
    if (
      ts.isFunctionDeclaration(node) ||
      ts.isMethodDeclaration(node) ||
      ts.isFunctionExpression(node) ||
      ts.isArrowFunction(node)
    ) {
      if (node.body && ts.isBlock(node.body)) {
        scanStatements(node.body.statements, buildFunctionContext(context, node.parameters), depth);
      }
      return;
    }

    if (ts.isCallExpression(node)) {
      extractEndpointsFromCall(node, context).forEach((endpoint) =>
        recordEndpoint(endpoint.method, endpoint.path),
      );

      if (depth < 2 && ts.isIdentifier(node.expression)) {
        const helper = helpers.get(node.expression.text);
        if (helper?.body && ts.isBlock(helper.body)) {
          scanStatements(
            helper.body.statements,
            buildFunctionContext(context, helper.parameters, node.arguments),
            depth + 1,
          );
        }
      }
    }

    if (ts.isNewExpression(node)) {
      extractEndpointsFromNewExpression(node, context).forEach((endpoint) =>
        recordEndpoint(endpoint.method, endpoint.path),
      );
    }

    ts.forEachChild(node, (child) => scanNode(child, context, depth));
  };

  const scanStatements = (
    statements: readonly ts.Statement[],
    context: Map<string, string>,
    depth = 0,
  ) => {
    const scoped = new Map(context);

    for (const statement of statements) {
      if (ts.isVariableStatement(statement)) {
        for (const declaration of statement.declarationList.declarations) {
          if (!ts.isIdentifier(declaration.name) || !declaration.initializer) {
            continue;
          }

          const value = extractPathExpression(declaration.initializer, scoped);
          if (value) {
            scoped.set(declaration.name.text, value);
          }
        }
      }

      scanNode(statement, scoped, depth);
    }
  };

  scanStatements(sourceFile.statements, new Map());

  return endpoints;
}

function buildMismatchReport(spec: OpenApiSpec) {
  const openApiIndex = new Map(
    Object.entries(spec.paths).map(([path, operations]) => [
      normalizeComparePath(path),
      {
        path,
        methods: new Set(Object.keys(operations).map((method) => method.toUpperCase())),
      },
    ]),
  );

  const serviceFiles = listServiceFiles(WEB_SRC_ROOT);
  const mismatches: Mismatch[] = [];
  let checkedEndpoints = 0;

  for (const filePath of serviceFiles) {
    for (const endpoint of extractEndpointsForFile(filePath)) {
      checkedEndpoints += 1;
      const openApiEntry = openApiIndex.get(endpoint.comparePath);

      if (!openApiEntry) {
        mismatches.push({
          endpoint,
          reason: 'missing_path',
        });
        continue;
      }

      if (!openApiEntry.methods.has(endpoint.method)) {
        mismatches.push({
          endpoint,
          reason: 'missing_method',
          openApiPath: openApiEntry.path,
          availableMethods: [...openApiEntry.methods].sort(),
        });
      }
    }
  }

  mismatches.sort((left, right) => {
    return (
      left.endpoint.file.localeCompare(right.endpoint.file) ||
      left.endpoint.path.localeCompare(right.endpoint.path) ||
      left.endpoint.method.localeCompare(right.endpoint.method)
    );
  });

  return {
    mismatches,
    checkedEndpoints,
  };
}

describe('API contract', () => {
  it('matches the backend OpenAPI spec for all frontend service paths', () => {
    const spec = readOpenApiSpec();
    const { mismatches, checkedEndpoints } = buildMismatchReport(spec);

    const message = mismatches
      .map((mismatch) => {
        if (mismatch.reason === 'missing_method') {
          return `${mismatch.endpoint.file}: ${mismatch.endpoint.method} ${mismatch.endpoint.path} not declared on ${mismatch.openApiPath} (available: ${mismatch.availableMethods?.join(', ') || 'none'})`;
        }

        return `${mismatch.endpoint.file}: ${mismatch.endpoint.method} ${mismatch.endpoint.path} missing from backend OpenAPI spec`;
      })
      .join('\n');

    if (mismatches.length > 0) {
      console.warn(
        `API contract mismatches detected (${mismatches.length}/${checkedEndpoints}).\n${message}`,
      );
    }

    expect(checkedEndpoints).toBeGreaterThan(0);

    if (STRICT_API_CONTRACT) {
      expect(mismatches, message).toEqual([]);
    }
  });
});

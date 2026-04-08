import { readdirSync, readFileSync } from 'node:fs';
import { dirname, join, relative, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const WEB_ROOT = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const FEATURES_ROOT = resolve(WEB_ROOT, 'src/features');
const METHOD_BY_API_HELPER = new Set(['delete', 'get', 'list', 'patch', 'post', 'put']);
const HTTP_METHODS = new Set(['DELETE', 'GET', 'PATCH', 'POST', 'PUT']);

function listServiceFiles(dir) {
  return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
    const fullPath = join(dir, entry.name);
    if (entry.isDirectory()) {
      return listServiceFiles(fullPath);
    }
    return entry.name.endsWith('.service.ts') ? [fullPath] : [];
  });
}

function finalizePath(rawPath, source) {
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

  return path.startsWith('/api/v1') ? path : null;
}

function extractPathExpression(node, context) {
  if (!node) {
    return null;
  }

  if (
    ts.isStringLiteral(node) ||
    ts.isNoSubstitutionTemplateLiteral(node) ||
    ts.isNumericLiteral(node)
  ) {
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
      const dynamicValue = ts.isIdentifier(span.expression)
        ? context.get(span.expression.text) ?? `{${span.expression.text}}`
        : '{param}';
      value += `${dynamicValue}${span.literal.text}`;
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

  if (ts.isConditionalExpression(node)) {
    const whenTrue = extractPathExpression(node.whenTrue, context) ?? '';
    const whenFalse = extractPathExpression(node.whenFalse, context) ?? '';
    if ([whenTrue, whenFalse].every((value) => value === '' || value.startsWith('?'))) {
      return '';
    }
    return '{param}';
  }

  return null;
}

function collectHelperFunctions(sourceFile) {
  const helpers = new Map();

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

function getMethodFromOptions(node, context) {
  if (!node || !ts.isObjectLiteralExpression(node)) {
    return 'GET';
  }

  for (const property of node.properties) {
    if (!ts.isPropertyAssignment(property)) {
      continue;
    }

    const name =
      ts.isIdentifier(property.name) || ts.isStringLiteral(property.name) ? property.name.text : '';
    if (name !== 'method') {
      continue;
    }

    const method = extractPathExpression(property.initializer, context)?.toUpperCase();
    if (method && HTTP_METHODS.has(method)) {
      return method;
    }
  }

  return 'GET';
}

function buildFunctionContext(baseContext, params, args) {
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

function extractEndpointsForFile(filePath) {
  const sourceText = readFileSync(filePath, 'utf8');
  const sourceFile = ts.createSourceFile(filePath, sourceText, ts.ScriptTarget.Latest, true);
  const helpers = collectHelperFunctions(sourceFile);
  const endpoints = [];

  const recordEndpoint = (method, rawPath, source) => {
    const path = finalizePath(rawPath, source);
    if (!path) {
      return;
    }
    endpoints.push({
      file: relative(WEB_ROOT, filePath),
      method,
      path,
    });
  };

  const scanNode = (node, context, depth = 0) => {
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
      if (
        ts.isPropertyAccessExpression(node.expression) &&
        ts.isIdentifier(node.expression.expression) &&
        node.expression.expression.text === 'api' &&
        METHOD_BY_API_HELPER.has(node.expression.name.text)
      ) {
        const rawPath = extractPathExpression(node.arguments[0], context);
        if (rawPath) {
          recordEndpoint(node.expression.name.text.toUpperCase(), rawPath, 'api');
        }
      }

      if (
        ts.isIdentifier(node.expression) &&
        node.expression.text === 'fetch' &&
        node.arguments[0]
      ) {
        const rawPath = extractPathExpression(node.arguments[0], context);
        if (rawPath) {
          recordEndpoint(getMethodFromOptions(node.arguments[1], context), rawPath, 'direct');
        }
      }

      if (
        depth < 2 &&
        ts.isIdentifier(node.expression) &&
        helpers.has(node.expression.text)
      ) {
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

    if (
      ts.isNewExpression(node) &&
      ts.isIdentifier(node.expression) &&
      node.expression.text === 'URL'
    ) {
      const rawPath = extractPathExpression(node.arguments?.[0], context);
      if (rawPath) {
        recordEndpoint('GET', rawPath, 'direct');
      }
    }

    if (
      ts.isCallExpression(node) &&
      ts.isPropertyAccessExpression(node.expression) &&
      ts.isIdentifier(node.expression.expression) &&
      node.expression.name.text === 'open'
    ) {
      const method = extractPathExpression(node.arguments[0], context)?.toUpperCase();
      const rawPath = extractPathExpression(node.arguments[1], context);
      if (method && rawPath) {
        recordEndpoint(method, rawPath, 'direct');
      }
    }

    ts.forEachChild(node, (child) => scanNode(child, context, depth));
  };

  const scanStatements = (statements, context, depth = 0) => {
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

const files = listServiceFiles(FEATURES_ROOT);
const endpoints = files.flatMap((filePath) => extractEndpointsForFile(filePath));
const uniqueEndpoints = new Set(endpoints.map((endpoint) => `${endpoint.method} ${endpoint.path}`));

console.log(`Service files scanned: ${files.length}`);
console.log(`API call sites found: ${endpoints.length}`);
console.log(`Unique endpoint signatures: ${uniqueEndpoints.size}`);
console.log(`Target >= 250: ${endpoints.length >= 250 ? 'PASS' : 'FAIL'}`);

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'type-enum': [
      2,
      'always',
      [
        'feat',
        'fix',
        'docs',
        'style',
        'refactor',
        'test',
        'chore',
        'perf',
        'ci',
        'revert',
        'build'
      ]
    ],
    'scope-enum': [
      2,
      'always',
      [
        'model-registry',
        'frontend',
        'prompt-engine',
        'guardrails',
        'workflow',
        'infra',
        'deps',
        'release',
        'security'
      ]
    ],
    'subject-case': [2, 'always', 'sentence-case'],
    'subject-max-length': [2, 'always', 100],
    'body-max-line-length': [2, 'always', 100]
  }
};

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    'scope-enum': [
      2,
      'always',
      ['frontend', 'backend', 'ai', 'devops', 'infra', 'docs', 'deps'],
    ],
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature
        'fix',      // Bug fix
        'docs',     // Documentation
        'style',    // Formatting (no code logic change)
        'refactor', // Refactoring
        'perf',     // Performance improvement
        'test',     // Adding tests
        'chore',    // Tooling, configs, build
        'ci',       // CI/CD changes
        'revert',   // Revert a commit
      ],
    ],
  },
};

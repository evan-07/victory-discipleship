module.exports = {
    testEnvironment: 'jsdom',
    collectCoverage: true,
    coverageDirectory: 'coverage',
    collectCoverageFrom: [
        'frontend/**/*.js',
        '!frontend/tests/**',
        '!**/node_modules/**'
    ],
    testMatch: [
        '**/frontend/tests/**/*.test.js'
    ],
    coverageReporters: ['lcov', 'text']
};

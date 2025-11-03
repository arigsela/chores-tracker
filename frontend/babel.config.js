module.exports = function (api) {
  api.cache(true);
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        'module-resolver',
        {
          root: ['./src'],
          alias: {
            // Path aliases matching tsconfig.json
            '@': './src',
            '@components': './src/components',
            '@screens': './src/screens',
            '@api': './src/api',
            '@navigation': './src/navigation',
            '@state': './src/state',
            '@utils': './src/utils',
            '@types': './src/types',
          },
          extensions: [
            '.js',
            '.jsx',
            '.ts',
            '.tsx',
            '.json',
          ],
        },
      ],
    ],
  };
};

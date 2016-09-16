'use strict';

const path = require('path'),
      webpack = require('webpack'),
      fileExists = require('file-exists'),
      ExtractTextPlugin = require('extract-text-webpack-plugin'),
      DjangoBundleTracker = require('webpack-bundle-tracker'),
      CopyPlugin = require('copy-webpack-plugin'),
      CleanPlugin = require('clean-webpack-plugin');

const DEV_HOST = process.env.DEV_HOST || 'localhost',
      DEV_PORT = parseInt(process.env.DEV_PORT || 3000),
      WEB_PORT = parseInt(process.env.WEB_PORT || 8000),
      PRODUCTION = process.env.NODE_ENV === 'production',
      DEV_SERVER = require.main.filename.indexOf('webpack-dev-server') !== -1;

const TARGET = PRODUCTION ? 'prod' : 'devel';

let config = {
  context: __dirname,

  entry: {
    'dz-admin': './dz/assets/admin',
    'dz-news-content': './dz/assets/news-content'
  },

  output: {
    path: path.resolve(__dirname, 'assets', TARGET),
    filename: '[name].js',
    chunkFilename: '_[name]-[id].js',
    publicPath: DEV_SERVER ? `http://${DEV_HOST}:${DEV_PORT}/`: `/static/${TARGET}/`,
    pathinfo: !PRODUCTION
  },

  devServer: {
    proxy: {
      '/static/*': {
        target: `http://${DEV_HOST}:${WEB_PORT}/`
      }
    },
    host: DEV_HOST,
    port: DEV_PORT,
    inline: true
  },

  devtool: PRODUCTION ? null : 'cheap-inline-module-source-map',

  module: {
    loaders: [
      {
        test: /\.js$/,
        loader: 'babel?presets[]=es2015',
        exclude: /node_modules\//
      },
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract([
                  'string-replace?search=url\\(\\.\\./img/&replace=url_FixWhiteNoice(../img/&flags=g',
                  'css?sourceMap'
                ])
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract('css?sourceMap!sass?sourceMap')
      },
      {
        test: /\.(png|gif)$/,
        loader: 'url?name=[name].[hash:4].[ext]&limit=3100'
      }
    ]
  },

  externals: {
    jquery: 'django.jQuery'  // global django jquery
  },

  plugins: [

    // must be the first
    new DjangoBundleTracker({
      path: __dirname,
      filename: `stats-${TARGET}.json`
    }),

    // don't publish if compilation fails
    new webpack.NoErrorsPlugin(),

    // keep hashes consistent between builds
    new webpack.optimize.OccurenceOrderPlugin(),

    // global django jquery
    new webpack.ProvidePlugin({ $: 'jquery' }),

    // resolve absent css images with fallback 1x1
    new webpack.NormalModuleReplacementPlugin(
      /^(\.\.\/img\/.*\.(png|gif|jpg)|\.\/css\/pie\.htc)$/, (result) => {
        if (/news-content\/css$/.test(result.context) &&
            !fileExists(path.resolve(result.context, result.request))) {
          // console.log('absent: ' + path.resolve(result.context, result.request));
          result.request = `file?name=1x1.png!../img/1x1.png`;
        }
    }),

    new ExtractTextPlugin('[name].css', { allChunks: true }),

    new CopyPlugin([
      { from: 'dz/assets/news-content/img/bookmakers', to: 'bookmaker' }
    ]),

    new CleanPlugin([`assets/${TARGET}`])

  // production-only plugins
  ].concat(PRODUCTION ? [

    new webpack.optimize.UglifyJsPlugin({
      compressor: {warnings: false}
    })

  ] : [])
};

module.exports = config;

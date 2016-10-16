'use strict';

const path = require('path');
const webpack = require('webpack');
const autoprefixer = require('autoprefixer');
const fileExists = require('file-exists');
const ExtractTextPlugin = require('extract-text-webpack-plugin');
const DjangoBundleTracker = require('webpack-bundle-tracker');
const CopyPlugin = require('copy-webpack-plugin');
const CleanPlugin = require('clean-webpack-plugin');

const DEV_HOST = process.env.DEV_HOST || 'localhost';
const DEV_PORT = Number.parseInt(process.env.DEV_PORT || 3000, 10);
const WEB_PORT = Number.parseInt(process.env.WEB_PORT || 8000, 10);
const PRODUCTION = process.env.NODE_ENV === 'production';
const DEV_SERVER = require.main.filename.indexOf('webpack-dev-server') !== -1;

const TARGET = PRODUCTION ? 'prod' : 'devel';
const MIN_EXT = PRODUCTION ? '.min' : '';

const __DZ_COMPAT = (process.env.DZ_COMPAT || 'false').toLowerCase();
const DZ_COMPAT = ['1', 'yes', 'true'].indexOf(__DZ_COMPAT) > -1;

// Whitenoise fails if a css-referenced image does not exist.
// Below we replace such references in url() with webpack.NormalModuleReplacementPlugin,
// This pass ignores url() references inside comments, but stupid whitenoice still fails,
// since it's simple and reacts just to the url(...) sequence in css. As a workaround,
// we pass css through regexp-loader and replace url(../img/*) by url_SOMETHING.
// For simplicity we don't check for (possibly multiline) comments around url() and use
// simple fact that all replaced image links start with slash (due to output.publicPath).
const WHITENOICE_CSS_FIX = {
  match: {pattern: 'url\\(\\.\\./img/', flags: 'g'},
  replaceWith: 'url_FixWhiteNoice(../img/'
};

let babelSettings = {
  presets: ['es2015'],
  plugins: ['transform-runtime']
};

let config = {
  context: path.resolve(__dirname, 'dz', 'assets'),

  entry: {
    plus: './plus',
    grappelli: './grappelli',
    bootstrap: './bootstrap',
    newsbox: './newsbox',
    tables: './tables'
  },

  output: {
    path: path.resolve(__dirname, 'public', TARGET),
    filename: `dz-[name]${MIN_EXT}.js`,
    library: ['dz', '[name]'],
    chunkFilename: `_dz-[name]-[id]${MIN_EXT}.js`,
    publicPath: DEV_SERVER ? `http://${DEV_HOST}:${DEV_PORT}/` : `/static/${TARGET}/`,
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
    inline: true,
    hot: true
  },

  module: {
    loaders: [
      {
        test: /\.js$/,
        loader: 'babel?' + JSON.stringify(babelSettings),
        exclude: /node_modules\//
      },
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract(
          'style',
          [].concat(
            // This fix is only required in production mode, but triggers buggy behaviour
            // in extract text plugin when it is effectively disabled in dev-server mode.
            // Workaround: disable regexp-replace loader in dev-server mode.
            DEV_SERVER ? [] : ['regexp-replace?' + JSON.stringify(WHITENOICE_CSS_FIX)],
            ['css?sourceMap']
          )
        )
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract(
          'style',
          'css?sourceMap!postcss!resolve-url!sass?sourceMap'
        )
      },
      {
        test: /\.(png|gif)$/,
        loader: 'url?name=[name].[hash:6].[ext]&limit=3100'
      }
    ]
  },

  postcss: () => [
    autoprefixer({browsers: ['last 2 versions', '> 5%']})
  ],

  sassLoader: {
    data: `$dz-compat: ${DZ_COMPAT};`
  },

  externals: [
    'django.jQuery',  // global django jquery
    'grp.jQuery',     // grappelli skin' jQuery
    'jQuery'          // jQuery for django tables
  ],

  plugins: [].concat([
    // === common plugins ===

    // this one must be the first
    new DjangoBundleTracker({
      path: __dirname,
      filename: `stats-${TARGET}.json`
    }),

    // don't publish if compilation fails
    new webpack.NoErrorsPlugin(),

    // keep hashes consistent between builds
    new webpack.optimize.OccurenceOrderPlugin(),

    // resolve absent css images with fallback 1x1
    new webpack.NormalModuleReplacementPlugin(
      /^(\.\.\/img\/.*\.(png|gif|jpg)|\.\/css\/pie\.htc)$/, result => {
        if (/newsbox\/css$/.test(result.context) &&
            !fileExists(path.resolve(result.context, result.request))) {
          // console.log('absent: ' + path.resolve(result.context, result.request));
          result.request = 'file?name=1x1.png!../img/1x1.png';
        }
      }
    ),

    new webpack.DefinePlugin({
      __DEVELOPMENT__: !PRODUCTION,
      __DEV_SERVER__: DEV_SERVER,

      // In dev-server mode the style loader needs require() to do hot reload.
      // Else, the extract text plugin will render style modules empty, and we
      // use require.include() to hide style inclusions from final javascript.
      'require.styles': DEV_SERVER ? 'require' : 'require.include'
    }),

    new ExtractTextPlugin(
      `dz-[name]${MIN_EXT}.css`, {
        allChunks: true,
        disable: DEV_SERVER
      }
    ),

    new webpack.optimize.CommonsChunkPlugin({
      name: 'common',
      minChunks: 3
    }),

    new CopyPlugin([
      {from: './newsbox/img/bookmakers', to: 'bookmaker'}
    ]),

    new CleanPlugin([`public/${TARGET}`])
  ],

  // === dev-server plugins ===
  DEV_SERVER ? [
    new webpack.HotModuleReplacementPlugin()
  ] : [],

  // === production-only plugins ===
  PRODUCTION ? [

    new webpack.optimize.UglifyJsPlugin({
      compressor: {warnings: false}
    })

  ] : []

  // === end of plugins ===
  ),

  devtool: PRODUCTION ? null : 'cheap-inline-module-source-map',

  watchOptions: {aggregateTimeout: 100}
};

module.exports = config;

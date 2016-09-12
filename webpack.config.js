'use strict';

let path = require('path'),
    rimraf = require('rimraf'),
    webpack = require('webpack'),
    ExtractTextPlugin = require('extract-text-webpack-plugin'),
    DjangoBundleTracker = require('webpack-bundle-tracker');

const dev_host = process.env.DEV_HOST || 'localhost',
      dev_port = parseInt(process.env.DEV_PORT || 3000),
      web_port = parseInt(process.env.WEB_PORT || 8000),
      is_production = process.env.NODE_ENV === 'production',
      is_dev_server = require.main.filename.indexOf('webpack-dev-server') !== -1;

const bundle_dir = is_production ? 'prod' : 'devel';

let config = {
  entry: {
    'dz-admin': './dz/assets/admin',
    'dz-news-content': './dz/assets/news-content'
  },

  output: {
    path: `${__dirname}/assets/${bundle_dir}`,
    filename: '[name].js',
    publicPath: is_dev_server ? `http://${dev_host}:${dev_port}/`: `/static/${bundle_dir}/`
  },

  devServer: {
    proxy: {
      '/static/*': {
        target: `http://${dev_host}:${web_port}/`
      }
    },
    host: dev_host,
    port: dev_port,
    inline: true
  },

  devtool: is_production ? null : 'cheap-inline-module-source-map',

  module: {
    loaders: [
      {
        test: /\.js$/,
        loader: 'babel?presets[]=es2015',
        exclude: /node_modules\//
      },
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract('css?sourceMap')
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract('css?sourceMap!sass?sourceMap')
      },
      {
        include: /\/img\/bookmakers\//,
        loader: 'file?name=bookmaker-[name].[ext]'
      },
      {
        test: /\.(png|gif)$/,
        exclude: /\/img\/bookmakers\//,
        loader: 'url?name=[name].[hash:4].[ext]&limit=3100'
      }
    ]
  },

  plugins: [
    new webpack.NoErrorsPlugin(),  // don't publish if compilation fails
    {
      apply: (compiler) => {
        rimraf.sync(compiler.options.output.path);
      }
    },
    new DjangoBundleTracker({  // must be the first
      path: __dirname,
      filename: is_production ? 'stats-prod.json': 'stats-devel.json'
    }),
    new ExtractTextPlugin(
      '[name].css',
      {allChunks: true}
    )
  ]
};

if (is_production) {
  config.plugins = config.plugins.concat([
    new webpack.optimize.OccurenceOrderPlugin(),  // keep hashes consistent between builds
    new webpack.optimize.UglifyJsPlugin({
      compressor: {warnings: false}
    })
  ]);
}

module.exports = config;

'use strict';

var path = require('path'),
    base_dir = path.dirname(__dirname),
    ExtractTextPlugin = require('extract-text-webpack-plugin'),
    DjangoBundleTracker = require('webpack-bundle-tracker');

var config = {
  entry: {
    'dz-admin': [
      './dz/assets/admin.webpack.js'
    ]
  },

  output: {
    path: path.join(base_dir, 'assets'),
    filename: '[name].js',
    publicPath: '/static/'
  },

  devtool: 'source-map',

  module: {
    loaders: [
      {
        test: /\.js$/,
        loader: 'babel?presets[]=es2015',
        exclude: /node_modules/
      },
      {
        test: /\.css$/,
        loader: ExtractTextPlugin.extract('style?sourceMap', 'css?sourceMap')
      },
      {
        test: /\.scss$/,
        loader: ExtractTextPlugin.extract('style?sourceMap', 'css?sourceMap!sass?sourceMap')
      }
    ]
  },

  plugins: [
    new DjangoBundleTracker({  // must be the first
      path: path.join(base_dir, 'webpack'),
      filename: 'stats.json'
    }),
    new ExtractTextPlugin('[name].css')
  ]
};

module.exports = config;

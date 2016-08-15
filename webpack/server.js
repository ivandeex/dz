'use strict';

var path = require('path'),
    base_dir = path.dirname(__dirname),
    webpack = require('webpack'),
    WebpackDevServer = require('webpack-dev-server'),
    DjangoBundleTracker = require('webpack-bundle-tracker');

var config = require('./config.js');

var dev_host = process.env.DEV_HOST || 'localhost',
    dev_port = process.env.DEV_PORT || 3000,
    web_port = process.env.WEB_PORT || 8000;

var web_url = `http://${dev_host}:${web_port}/`,
    dev_url = `http://${dev_host}:${dev_port}/`;

for (var i in config.entry) {
  config.entry[i].unshift(`webpack-dev-server/client?${dev_url}`);
}

config.output.publicPath = dev_url;

config.plugins[0] = new DjangoBundleTracker({  // must be the first
  path: path.join(base_dir, 'webpack'),
  filename: 'stats.hotserver.json'
});

var server = new WebpackDevServer(webpack(config), {
  publicPath: config.output.publicPath,
  proxy: { '/static/*': { target: web_url } }
});

server.listen(dev_port, '0.0.0.0', function(err, result) {
  if (err)  console.log(err);
  console.log(`Listen on ${dev_url}`);
  console.log(`Proxy for ${web_url}`);
});

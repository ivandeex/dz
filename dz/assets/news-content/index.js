'use strict';

// Entry bundle is only needed by webpack-dev-server to hot-reload the page,
// so we never really call __requirements().
function __requirements(name) {
  require.ensure([], function(require) {
    // Split required images into lazy bundle by asynchronous amd:
    require('./img/bookmakers/' + name + '.png');

    require.include('./css/base.css');
    require.include('./css/custom.scss');
  }, 'bookmakers');
}

'use strict';

// Entry bundle is only needed by webpack-dev-server to hot-reload the page,
// so we never really call __requirements__().
function __requirements__(name) {
  require.include('./css/base.css');
  require.include('./css/custom.scss');

  // Split required images into lazy bundle by asynchronous amd:
  require(['./img/bookmakers/' + name], () => {});
}

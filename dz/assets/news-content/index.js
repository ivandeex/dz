'use strict';

// bundled javascript is only needed by webpack-dev-server to hot-reload the page,
// so we split required css and images into separate bundle by asynchronous require,
// but never actually load it (if-undefined).
if (undefined) {
  require([
    './css/base.css',
    './css/custom.scss',
    './img/bookmakers/' + undefined + '.png'
  ], function() {});
}

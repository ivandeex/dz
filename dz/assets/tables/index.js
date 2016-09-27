require.include('./base.scss');
require.include('./list.scss');
require.include('./results.scss');
require.include('../common/description.scss');

module.exports = require('imports?$=jQuery!./list.js');

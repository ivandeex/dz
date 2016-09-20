'use strict';
/* global $ */

$(() => {
  $('.grp-messagelist li').click(function() {
    $(this).hide('slow');
  });
});

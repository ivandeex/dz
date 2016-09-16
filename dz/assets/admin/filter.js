'use strict';

$(() => {
  $('.messagelist li').click(function() {
    $(this).hide('slow');
  });
  $('#changelist-filter').addClass('hidden');
  $('#changelist-filter > h2').click(
    () => $('#changelist-filter').toggleClass('hidden')
  );
});

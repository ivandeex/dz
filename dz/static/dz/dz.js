django.jQuery(function() {
    'use strict';
    var $ = django.jQuery;
    $('.messagelist li').click(function() { $(this).hide('slow'); })
    $('#changelist-filter').addClass('hidden');
    $('#changelist-filter > h2').click(function() {
        $('#changelist-filter').toggleClass('hidden');
    });
});

django.jQuery(function() {
    'use strict';
    var $ = django.jQuery;
    $('#changelist-filter').addClass('hidden');
    $('#changelist-filter > h2').click(function() {
        $('#changelist-filter').toggleClass('hidden');
    });
});

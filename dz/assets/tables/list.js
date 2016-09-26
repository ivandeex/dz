/* global $ */  // This comment shuts up javascript linter.

$(() => {
  // Let user select all rows at once by clicking on the row_selextor header.
  let $row_selectors = $('td.row_selector input[type="checkbox"]');
  $('th.row_selector input[type="checkbox"]').click(function() {
    $row_selectors.prop('checked', this.checked);
  });
});

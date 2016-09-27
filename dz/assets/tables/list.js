/* global $ */  // This comment shuts up javascript linter.

$(() => {
  // Let user select all rows at once by clicking on the row_selextor header.
  let $row_selectors = $('td.row_selector input[type="checkbox"]');
  $('th.row_selector input[type="checkbox"]').click(function() {
    $row_selectors.prop('checked', this.checked);
  });
});

export function showNewsboxPopup(link, name) {
  let win = window.open(
    link, name,
    'height=500,width=1000,resizable=yes,scrollbars=yes'
  );
  win.focus();
  return false;  // prevent default action
};

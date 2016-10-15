'use strict';
/* global window document */  // This comment shuts up javascript linter.

if (document.readyState === 'complete') {
  onReady();
} else {
  document.addEventListener('DOMContentLoaded', onReady);
}

function onReady() {
  // Let user select all rows at once by clicking on the row_selector header.
  let globalCheckbox = document.querySelector('th.col-row_selector [type="checkbox"]');
  if (globalCheckbox) {
    globalCheckbox.addEventListener('click', function() {
      let checkboxes = document.querySelectorAll('td > .dz-row-selector[type="checkbox"]');
      Array.prototype.forEach.call(checkboxes, function(element) {
        element.checked = globalCheckbox.checked;
      });
    });
  }
}

export function showNewsboxPopup(link, name) {
  let win = window.open(
    link, name,
    'height=500,width=1000,resizable=yes,scrollbars=yes'
  );
  win.focus();
  return false;  // prevent default action
}

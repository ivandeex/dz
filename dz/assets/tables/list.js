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

export function runRowAction(action, row_ids, confirmation_msg) {
  if (!row_ids) {
    let checkboxes = document.querySelectorAll('input.dz-row-selector:checked');
    row_ids = Array.prototype.map.call(checkboxes, el => el.value);
  } else if (!Array.isArray(row_ids)) {
    row_ids = [row_ids];
  }

  if (!row_ids.length) {
    const message = document.getElementById('dz-msg-no-rows-selected').textContent;
    window.alert(message); /* eslint no-alert: off */
    return;
  }

  if (confirmation_msg) {
    if (confirmation_msg === true) {
      confirmation_msg = document.getElementById('dz-msg-confirm-action').textContent;
      confirmation_msg = confirmation_msg.replace('[ACTION]', action);
    }
    if (!window.confirm(confirmation_msg)) { /* eslint no-alert: off */
      return;
    }
  }

  let form = document.forms['dz-row-action-form'];
  form.elements.action.value = action;
  form.elements.row_ids.value = row_ids.join(',');
  form.submit();
  return false;
}

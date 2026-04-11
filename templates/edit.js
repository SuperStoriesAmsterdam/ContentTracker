/* ── INLINE COPY EDITOR — The Content Tracker ──
   Toggle edit mode to make all text editable.
   Changes saved to localStorage automatically.
   Right-click an edited field → revert to original.
   Cmd+E / Ctrl+E toggles the editor bar. */

(function() {
  'use strict';

  const STATE_VERSION = 'v1';
  const STORAGE_KEY = 'ct-edits-' + STATE_VERSION;
  const ORIGINALS_KEY = 'ct-originals-' + STATE_VERSION;
  let editMode = false;
  let edits = JSON.parse(localStorage.getItem(STORAGE_KEY) || '{}');
  let originals = JSON.parse(localStorage.getItem(ORIGINALS_KEY) || '{}');

  /* Editable elements — all text content in the main area */
  const EDITABLE = '.ct-main h1, .ct-main h2, .ct-main h3, .ct-main p, .ct-main li, .ct-main span, .ct-main div[style*="font-weight: 700"], .ct-main div[style*="font-weight: 600"], .ct-main label, .ct-main-full h1, .ct-main-full h2, .ct-main-full h3, .ct-main-full p, .ct-main-full li, .ct-main-full span, .ct-main-full div[style*="font-weight: 700"], .ct-main-full div[style*="font-weight: 600"]';

  function createBar() {
    const bar = document.createElement('div');
    bar.id = 'edit-bar';
    bar.style.cssText = 'position:fixed;bottom:0;left:0;right:0;background:#1d1d1d;color:#fff;padding:10px 24px;z-index:9999;font-family:Outfit,sans-serif;display:none;';
    bar.innerHTML = `
      <div style="display:flex;align-items:center;justify-content:space-between;max-width:960px;margin:0 auto">
        <span style="font-size:12px;opacity:0.5">Copy editor</span>
        <div style="display:flex;gap:8px;align-items:center">
          <span id="edit-count" style="font-size:11px;opacity:0.4"></span>
          <span id="edit-status" style="font-size:12px;opacity:0;transition:opacity 0.3s"></span>
          <button id="edit-toggle" style="background:rgba(255,255,255,0.15);color:#fff;border:none;padding:6px 16px;border-radius:9999px;font-size:12px;cursor:pointer;font-family:Outfit,sans-serif">Edit page</button>
          <button id="edit-reset" style="display:none;background:rgba(255,255,255,0.15);color:#fff;border:none;padding:6px 16px;border-radius:9999px;font-size:12px;cursor:pointer;font-family:Outfit,sans-serif">Reset all</button>
        </div>
      </div>
    `;
    document.body.appendChild(bar);

    document.getElementById('edit-toggle').addEventListener('click', toggleEdit);
    document.getElementById('edit-reset').addEventListener('click', resetEdits);

    document.addEventListener('keydown', function(e) {
      if ((e.metaKey || e.ctrlKey) && e.key === 'e') {
        e.preventDefault();
        bar.style.display = bar.style.display === 'none' ? '' : 'none';
      }
    });
  }

  function indexElements() {
    document.querySelectorAll(EDITABLE).forEach(function(el, i) {
      if (el.children.length > 0 && el.tagName !== 'LI' && el.tagName !== 'P') return;
      if (el.closest('#edit-bar')) return;
      if (el.closest('form')) return;
      if (el.closest('nav')) return;
      if (!el.textContent.trim()) return;

      if (!el.dataset.editId) {
        el.dataset.editId = 'e-' + i;
      }
      if (!originals[el.dataset.editId]) {
        originals[el.dataset.editId] = el.textContent;
      }
      if (edits[el.dataset.editId]) {
        el.textContent = edits[el.dataset.editId];
      }
    });
    localStorage.setItem(ORIGINALS_KEY, JSON.stringify(originals));
    updateCount();
  }

  function toggleEdit() {
    editMode = !editMode;
    const btn = document.getElementById('edit-toggle');
    const reset = document.getElementById('edit-reset');

    if (editMode) {
      btn.textContent = 'Stop editing';
      btn.style.background = 'white';
      btn.style.color = '#1d1d1d';
      reset.style.display = 'inline-block';
      enableEditing();
    } else {
      btn.textContent = 'Edit page';
      btn.style.background = 'rgba(255,255,255,0.15)';
      btn.style.color = 'white';
      reset.style.display = 'none';
      disableEditing();
      saveAll();
    }
  }

  function enableEditing() {
    document.querySelectorAll('[data-edit-id]').forEach(function(el) {
      el.contentEditable = 'true';
      el.style.outline = '1px dashed rgba(0,0,0,0.1)';
      el.style.outlineOffset = '2px';
      if (edits[el.dataset.editId]) {
        el.style.outline = '1px solid #4CAF50';
      }
    });
  }

  function disableEditing() {
    document.querySelectorAll('[data-edit-id]').forEach(function(el) {
      el.contentEditable = 'false';
      el.style.outline = '';
      el.style.outlineOffset = '';
      if (edits[el.dataset.editId]) {
        el.style.outline = '';
      }
    });
    removeContextMenu();
  }

  function saveAll() {
    document.querySelectorAll('[data-edit-id]').forEach(function(el) {
      var id = el.dataset.editId;
      if (el.textContent !== originals[id]) {
        edits[id] = el.textContent;
      } else {
        delete edits[id];
      }
    });
    localStorage.setItem(STORAGE_KEY, JSON.stringify(edits));
    updateCount();
    flash('Saved');
  }

  function resetEdits() {
    if (confirm('Reset ALL edits and restore original text?')) {
      localStorage.removeItem(STORAGE_KEY);
      edits = {};
      location.reload();
    }
  }

  function revertField(editId) {
    var el = document.querySelector('[data-edit-id="' + editId + '"]');
    if (el && originals[editId]) {
      el.textContent = originals[editId];
      delete edits[editId];
      localStorage.setItem(STORAGE_KEY, JSON.stringify(edits));
      updateCount();
      flash('Reverted');
    }
    removeContextMenu();
  }

  function removeContextMenu() {
    var old = document.getElementById('edit-ctx');
    if (old) old.remove();
  }

  document.addEventListener('contextmenu', function(e) {
    if (!editMode) return;
    var el = e.target.closest('[data-edit-id]');
    if (!el || !edits[el.dataset.editId]) return;

    e.preventDefault();
    removeContextMenu();

    var menu = document.createElement('div');
    menu.id = 'edit-ctx';
    menu.style.cssText = 'position:absolute;background:#1d1d1d;color:#fff;border-radius:8px;padding:4px;z-index:10000;box-shadow:0 4px 12px rgba(0,0,0,0.2);font-family:Outfit,sans-serif;';
    menu.innerHTML = '<button style="background:none;border:none;color:#fff;padding:8px 16px;cursor:pointer;font-size:12px;font-family:Outfit,sans-serif;white-space:nowrap">↩ Revert to original</button>';
    menu.style.left = e.pageX + 'px';
    menu.style.top = e.pageY + 'px';
    document.body.appendChild(menu);

    menu.querySelector('button').addEventListener('click', function() {
      revertField(el.dataset.editId);
    });
  });

  document.addEventListener('click', function(e) {
    if (!e.target.closest('#edit-ctx')) removeContextMenu();
  });

  function updateCount() {
    var n = Object.keys(edits).length;
    var el = document.getElementById('edit-count');
    if (el) el.textContent = n > 0 ? n + ' change' + (n !== 1 ? 's' : '') : '';
  }

  function flash(msg) {
    var el = document.getElementById('edit-status');
    if (!el) return;
    el.textContent = msg;
    el.style.opacity = '1';
    el.style.color = '#4CAF50';
    setTimeout(function() { el.style.opacity = '0'; }, 1500);
  }

  document.addEventListener('focusout', function(e) {
    if (editMode && e.target.dataset && e.target.dataset.editId) {
      var id = e.target.dataset.editId;
      if (e.target.textContent !== originals[id]) {
        edits[id] = e.target.textContent;
        e.target.style.outline = '1px solid #4CAF50';
      } else {
        delete edits[id];
        e.target.style.outline = '1px dashed rgba(0,0,0,0.1)';
      }
      localStorage.setItem(STORAGE_KEY, JSON.stringify(edits));
      updateCount();
      flash('Saved');
    }
  });

  document.addEventListener('DOMContentLoaded', function() {
    createBar();
    indexElements();
  });

})();

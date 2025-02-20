let clickableElements = [];
window.resizeTo(375, 1000);

document.querySelectorAll('*').forEach(el => {
   let computedStyle = window.getComputedStyle(el);
   let rect = el.getBoundingClientRect();
   let hasClickEvent = false;
   let isVisible = !(computedStyle.display === 'none');
   if (typeof getEventListeners !== 'undefined') {
      let listeners = getEventListeners(el);
      if (listeners.click && listeners.click.length > 0) hasClickEvent = true;
   }
   if (isVisible && (
       el.tagName === 'A' || 
       el.tagName === 'BUTTON' || 
       (el.tagName === 'INPUT' && (el.type === 'button' || el.type === 'submit')) || 
       el.getAttribute('role') === 'button' || 
       hasClickEvent ||
       el.tabIndex >= 0)) {
      const innerhtml = el.innerHTML;
      clickableElements.push({
         element: innerhtml,
         width: rect.width,
         height: rect.height
      });
   }
});

return clickableElements;
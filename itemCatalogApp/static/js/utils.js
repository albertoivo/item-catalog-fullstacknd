// Used to toggle the menu on small screens when clicking on the menu button
function toggleMenu() {
  let menu_mobile = document.getElementById('bar-mobile')
  if (menu_mobile.className.indexOf('show') === -1) {
        menu_mobile.className += ' show'
    } else {
        menu_mobile.className = menu_mobile.className.replace(' show', '')
    }
}
// Used to toggle the menu on small screens when clicking on the menu button
function toggleMenu() {
    var x = document.getElementById('bar-mobile')
    if (x.className.indexOf('show') == -1) {
        x.className += ' show'
    } else {
        x.className = x.className.replace(' show', '')
    }
}
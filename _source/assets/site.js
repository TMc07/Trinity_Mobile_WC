(function () {
  var button = document.querySelector('.menu');
  var nav = document.getElementById('navigation');
  if (button && nav) {
    button.addEventListener('click', function () {
      var open = button.getAttribute('aria-expanded') === 'true';
      button.setAttribute('aria-expanded', String(!open));
      nav.classList.toggle('open', !open);
    });
    nav.querySelectorAll('a').forEach(function (a) {
      a.addEventListener('click', function () {
        nav.classList.remove('open');
        button.setAttribute('aria-expanded', 'false');
      });
    });
  }
  var y = document.getElementById('year');
  if (y) y.textContent = new Date().getFullYear();
})();

document.querySelectorAll('select[data-autosubmit]').forEach(function (select) {
  select.addEventListener('change', function () {
    select.form.submit();
  });
});

document.querySelectorAll('.stars').forEach(function (box) {
  var input = box.parentElement.querySelector('input[name="rating"]');
  var stars = box.querySelectorAll('span');

  function paint(value) {
    stars.forEach(function (star) {
      star.classList.toggle('on', Number(star.dataset.n) <= value);
    });
  }

  paint(Number(box.dataset.value));
  box.addEventListener('mouseleave', function () {
    paint(Number(box.dataset.value));
  });
  stars.forEach(function (star) {
    star.addEventListener('mouseover', function () {
      paint(Number(star.dataset.n));
    });
    star.addEventListener('click', function () {
      input.value = star.dataset.n;
      box.dataset.value = star.dataset.n;
      input.form.submit();
    });
  });
});
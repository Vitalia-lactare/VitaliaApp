(function () {
  const track = document.querySelector(".hero-carousel-track");
  if (!track) return;

  const slides = Array.from(track.querySelectorAll(".hero-carousel-slide"));
  const dots = Array.from(document.querySelectorAll(".hero-carousel-dot"));
  let current = 0;
  let timer = null;

  function goTo(index) {
    slides[current].classList.remove("is-active");
    dots[current]?.classList.remove("is-active");
    current = (index + slides.length) % slides.length;
    slides[current].classList.add("is-active");
    dots[current]?.classList.add("is-active");
  }

  function restartAutoplay() {
    if (timer) clearInterval(timer);
    timer = setInterval(() => goTo(current + 1), 5000);
  }

  dots.forEach((dot, i) => {
    dot.addEventListener("click", () => {
      goTo(i);
      restartAutoplay();
    });
  });

  if (slides.length > 1) restartAutoplay();
})();

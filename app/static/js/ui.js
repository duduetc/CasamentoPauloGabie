document.addEventListener('DOMContentLoaded', () => {
  const audio = document.getElementById('site-audio');
  const toggle = document.getElementById('music-toggle');

  if (!audio || !toggle) return;

  const musicUrl = audio.dataset.musicUrl || '';
  if (musicUrl) {
    audio.src = musicUrl;
  }

  const syncButtonState = (isPlaying) => {
    toggle.classList.toggle('is-paused', !isPlaying);
    toggle.setAttribute('aria-pressed', String(isPlaying));
    toggle.setAttribute('aria-label', isPlaying ? 'Pausar música' : 'Tocar música');
  };

  toggle.addEventListener('click', async () => {
    if (!audio.src && musicUrl) {
      audio.src = musicUrl;
    }

    if (audio.paused) {
      try {
        await audio.play();
        syncButtonState(true);
      } catch (error) {
        syncButtonState(false);
      }
    } else {
      audio.pause();
      syncButtonState(false);
    }
  });

  audio.addEventListener('play', () => syncButtonState(true));
  audio.addEventListener('pause', () => syncButtonState(false));

  if (musicUrl) {
    audio.play().catch(() => syncButtonState(false));
  }
});


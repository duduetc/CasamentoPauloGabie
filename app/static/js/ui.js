document.addEventListener('DOMContentLoaded', () => {
  const audio = document.getElementById('site-audio');
  const toggle = document.getElementById('music-toggle');

  if (!audio || !toggle) return;

  const playlist = (audio.dataset.playlist || audio.dataset.musicUrl || '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean);

  let currentTrackIndex = 0;

  const syncButtonState = (isPlaying) => {
    toggle.classList.toggle('is-paused', !isPlaying);
    toggle.setAttribute('aria-pressed', String(isPlaying));
    toggle.setAttribute('aria-label', isPlaying ? 'Pausar música' : 'Tocar música');
  };

  const playTrack = async (index, { force = false } = {}) => {
    if (!playlist.length) return;

    currentTrackIndex = index % playlist.length;
    if (audio.src !== playlist[currentTrackIndex]) {
      audio.src = playlist[currentTrackIndex];
      audio.load();
    }

    try {
      await audio.play();
      syncButtonState(true);
    } catch (error) {
      syncButtonState(false);
      if (force) {
        window.addEventListener('pointerdown', () => playTrack(currentTrackIndex), { once: true });
      }
    }
  };

  toggle.addEventListener('click', async () => {
    if (!playlist.length) return;

    if (audio.paused) {
      if (!audio.src) {
        await playTrack(currentTrackIndex);
      } else {
        try {
          await audio.play();
          syncButtonState(true);
        } catch (error) {
          syncButtonState(false);
        }
      }
    } else {
      audio.pause();
      syncButtonState(false);
    }
  });

  audio.addEventListener('play', () => syncButtonState(true));
  audio.addEventListener('pause', () => syncButtonState(false));
  audio.addEventListener('ended', () => {
    if (!playlist.length) return;
    playTrack(currentTrackIndex + 1);
  });

  if (playlist.length) {
    playTrack(0, { force: true });
  }
});


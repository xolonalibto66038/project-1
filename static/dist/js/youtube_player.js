let player      = null;
let pollTimer   = null;
let seenMarked  = false;

const SEEN_THRESHOLD = 80; // percent

// ── Bootstrap the YouTube IFrame API ────────────────────────────────
const tag    = document.createElement('script');
tag.src      = 'https://www.youtube.com/iframe_api';
document.head.appendChild(tag);

window.onYouTubeIframeAPIReady = function () {
  const iframe = document.getElementById('yt-player');
  if (!iframe) return;

  player = new YT.Player('yt-player', {
    events: {
      onReady:       onPlayerReady,
      onStateChange: onPlayerStateChange,
    },
  });
};

// ── Called once the player is ready ─────────────────────────────────
function onPlayerReady(event) {
  console.log('YouTube player ready');
}

// ── Called on play / pause / end / buffer ────────────────────────────
function onPlayerStateChange(event) {
  if (event.data === YT.PlayerState.PLAYING) {
    startPolling();
  }

  if (
    event.data === YT.PlayerState.PAUSED ||
    event.data === YT.PlayerState.ENDED
  ) {
    stopPolling();
    saveProgress();
  }
}

// ── Poll every 10 s while video is playing ───────────────────────────
function startPolling() {
  if (pollTimer) return;
  pollTimer = setInterval(() => {
    if (player.getPlayerState() === YT.PlayerState.PLAYING) {
      checkProgress();
    }
  }, 10000);
}

function stopPolling() {
  clearInterval(pollTimer);
  pollTimer = null;
}

// ── Read current position and act on it ──────────────────────────────
function checkProgress() {
  if (!player || typeof player.getCurrentTime !== 'function') return;

  const current  = player.getCurrentTime();  // seconds
  const duration = player.getDuration();     // seconds
  if (!duration) return;

  const pct = (current / duration) * 100;
  console.log(`${Math.floor(current)}s / ${Math.floor(duration)}s — ${pct.toFixed(1)}%`);

  if (pct >= SEEN_THRESHOLD && !seenMarked) {
    markAsSeen();
  }
}

// ── Save progress to backend ─────────────────────────────────────────
async function saveProgress() {
  if (!player || typeof player.getCurrentTime !== 'function') return;

  const watched_seconds  = Math.floor(player.getCurrentTime());
  const duration_seconds = Math.floor(player.getDuration());
  if (!duration_seconds || !window.VIDEO_PROGRESS_URL) return;

  try {
    const res = await fetch(window.VIDEO_PROGRESS_URL, {
      method:  'POST',
      headers: {
        'X-CSRFToken':  window.CSRF_TOKEN,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ watched_seconds, duration_seconds }),
    });

    const data = await res.json();
    console.log('Progress saved:', data.percent + '%');

    // Update active playlist bar in real time
    const activeItem = document.querySelector('.playlist-item.active');
    if (activeItem) {
      const bar = activeItem.querySelector('[data-progress-bar]');
      if (bar) {
        bar.style.width = data.percent + '%';
      }
    }

    if (data.is_seen && !seenMarked) {
      markAsSeen();
    }
  } catch (err) {
    console.error('Progress save error:', err);
  }
}

// ── Mark video as seen (UI update) ───────────────────────────────────
function markAsSeen() {
  seenMarked = true;

  // Update seen button
  const seenBtn = document.getElementById('seen-btn');
  if (seenBtn && seenBtn.dataset.seen !== 'true') {
    seenBtn.dataset.seen = 'true';
    seenBtn.classList.replace('btn-outline-secondary', 'btn-success');
    seenBtn.querySelector('span').textContent = seenBtn.dataset.labelSeen || 'Seen';
  }

  // Fill active playlist progress bar to 100% green
  const activeItem = document.querySelector('.playlist-item.active');
  if (activeItem) {
    const bar = activeItem.querySelector('[data-progress-bar]');
    if (bar) {
      bar.style.width      = '100%';
      bar.style.background = '#28a745';
    }
  }
}

// ── Save on tab close / navigation ───────────────────────────────────
window.addEventListener('beforeunload', () => {
  if (!player || typeof player.getCurrentTime !== 'function') return;
  if (!window.VIDEO_PROGRESS_URL) return;

  const watched_seconds  = Math.floor(player.getCurrentTime());
  const duration_seconds = Math.floor(player.getDuration());
  if (!duration_seconds) return;

  navigator.sendBeacon(
    window.VIDEO_PROGRESS_URL,
    new Blob(
      [JSON.stringify({ watched_seconds, duration_seconds })],
      { type: 'application/json' }
    )
  );
});
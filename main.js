/* ============ 颜植季官网交互 ============ */

// 导航滚动态
const header = document.getElementById("siteHeader");
const onScroll = () => header.classList.toggle("scrolled", window.scrollY > 40);
window.addEventListener("scroll", onScroll, { passive: true });
onScroll();

// 移动端菜单
const navToggle = document.getElementById("navToggle");
const mainNav = document.getElementById("mainNav");
if (navToggle && mainNav) {
  navToggle.addEventListener("click", () => mainNav.classList.toggle("open"));
  mainNav.querySelectorAll("a").forEach((a) =>
    a.addEventListener("click", () => mainNav.classList.remove("open"))
  );
}

// 滚动入场动画
const io = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (e.isIntersecting) {
        e.target.classList.add("visible");
        io.unobserve(e.target);
      }
    });
  },
  { threshold: 0.12, rootMargin: "0px 0px -40px 0px" }
);
document.querySelectorAll(".reveal").forEach((el) => io.observe(el));

// 兜底：直接带锚点打开（如 index.html#products）或浏览器恢复滚动位置时，
// IntersectionObserver 的首次回调可能早于这次跳转，导致目标区域停在 opacity:0。
// 加载完成后再按几何位置补一次，保证深链与刷新后内容可见。
const revealInView = () => {
  document.querySelectorAll(".reveal:not(.visible)").forEach((el) => {
    const r = el.getBoundingClientRect();
    if (r.top < window.innerHeight * 0.94 && r.bottom > 0) {
      el.classList.add("visible");
      io.unobserve(el);
    }
  });
};
window.addEventListener("load", revealInView);
window.addEventListener("hashchange", () => setTimeout(revealInView, 80));

// 数字滚动
const fmt = (n) => n.toLocaleString("en-US");
const counterIO = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      if (!e.isIntersecting) return;
      const el = e.target;
      const target = parseInt(el.dataset.count, 10);
      const dur = 1600;
      const start = performance.now();
      const tick = (now) => {
        const p = Math.min((now - start) / dur, 1);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = fmt(Math.round(target * eased));
        if (p < 1) requestAnimationFrame(tick);
      };
      requestAnimationFrame(tick);
      counterIO.unobserve(el);
    });
  },
  { threshold: 0.5 }
);
document.querySelectorAll("[data-count]").forEach((el) => counterIO.observe(el));

// ---------- 视频：滚动播放 ----------
const playIO = new IntersectionObserver(
  (entries) => {
    entries.forEach((e) => {
      const v = e.target;
      if (e.isIntersecting) {
        v.play().catch(() => {});
      } else if (!v.paused) {
        v.pause();
      }
    });
  },
  { threshold: 0.4 }
);
document.querySelectorAll("video:not(#pdVideo)").forEach((v) => {
  v.muted = true;
  playIO.observe(v);
});

// ---------- 产品详情页影片（点击有声播放 / 暂停恢复按钮） ----------
const pdVideo = document.getElementById("pdVideo");
const pdFilmPlay = document.getElementById("pdFilmPlay");
if (pdVideo && pdFilmPlay) {
  const syncBtn = () => {
    const playing = !pdVideo.paused && !pdVideo.ended;
    pdFilmPlay.classList.toggle("playing", playing);
    const label = pdFilmPlay.querySelector("span");
    if (label) label.textContent = playing ? "正在播放" : "播放影片（含声音）";
  };
  pdFilmPlay.addEventListener("click", () => {
    pdVideo.muted = false;
    pdVideo.play().catch(() => {});
  });
  pdVideo.addEventListener("click", () => {
    if (!pdVideo.paused) pdVideo.pause();
  });
  pdVideo.addEventListener("play", syncBtn);
  pdVideo.addEventListener("pause", syncBtn);
  pdVideo.addEventListener("ended", syncBtn);
  new IntersectionObserver(
    (entries) => {
      entries.forEach((e) => {
        if (!e.isIntersecting && !pdVideo.paused) pdVideo.pause();
      });
    },
    { threshold: 0.15 }
  ).observe(pdVideo);
}

// ---------- 声音开关 ----------
document.querySelectorAll(".video-sound").forEach((btn) => {
  const box = btn.closest(".science-media") || btn.parentElement;
  const video = box && box.querySelector("video");
  if (!video) return;
  btn.addEventListener("click", () => {
    video.muted = !video.muted;
    btn.classList.toggle("on", !video.muted);
    btn.querySelector("span").textContent = video.muted ? "开启声音" : "关闭声音";
    if (!video.muted) video.play().catch(() => {});
  });
});

const filmsSound = document.getElementById("filmsSound");
if (filmsSound) {
  filmsSound.addEventListener("click", () => {
    const on = filmsSound.classList.toggle("on");
    filmsSound.setAttribute("aria-pressed", String(on));
    filmsSound.querySelector("span").textContent = on ? "关闭声音" : "开启声音";
    document.querySelectorAll("[data-film]").forEach((v) => {
      v.muted = !on;
      if (on) v.play().catch(() => {});
    });
  });
}

// ---------- 口令复制 ----------
document.querySelectorAll(".copy-btn").forEach((btn) => {
  btn.addEventListener("click", async () => {
    const text = btn.dataset.copy || "";
    try {
      await navigator.clipboard.writeText(text);
    } catch (err) {
      const ta = document.createElement("textarea");
      ta.value = text;
      ta.style.position = "fixed";
      ta.style.opacity = "0";
      document.body.appendChild(ta);
      ta.select();
      document.execCommand("copy");
      document.body.removeChild(ta);
    }
    const old = btn.textContent;
    btn.textContent = "已复制";
    btn.classList.add("copied");
    setTimeout(() => {
      btn.textContent = old;
      btn.classList.remove("copied");
    }, 1800);
  });
});

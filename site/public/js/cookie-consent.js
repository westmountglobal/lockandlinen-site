(function () {
  "use strict";
  var KEY = "ll_cookie_consent";
  var GA_ID = "G-CK8VTP8KF1";
  var GTAG_SRC = "https://www.googletagmanager.com/gtag/js?id=" + GA_ID;

  function getChoice() {
    try { return window.localStorage.getItem(KEY); } catch (e) { return null; }
  }
  function setChoice(value) {
    try { window.localStorage.setItem(KEY, value); } catch (e) {}
  }

  function loadAnalytics() {
    if (window.__llGtagLoaded) return;
    window.__llGtagLoaded = true;
    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag("consent", "default", {
      analytics_storage: "denied",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied",
      wait_for_update: 500
    });
    gtag("consent", "update", {
      analytics_storage: "granted",
      ad_storage: "denied",
      ad_user_data: "denied",
      ad_personalization: "denied"
    });
    var s = document.createElement("script");
    s.async = true;
    s.src = GTAG_SRC;
    s.onload = function () {
      gtag("js", new Date());
      gtag("config", GA_ID);
    };
    document.head.appendChild(s);
  }

  function revokeAnalytics() {
    if (typeof window.gtag === "function") {
      window.gtag("consent", "update", {
        analytics_storage: "denied",
        ad_storage: "denied",
        ad_user_data: "denied",
        ad_personalization: "denied"
      });
    }
  }

  function setBannerHeight(el) {
    document.body.style.setProperty("--ll-cookie-banner-h", el.offsetHeight + "px");
  }

  function pinToVisualViewport() {
    var el = document.getElementById("ll-cookie-banner");
    if (!el) return;
    var vv = window.visualViewport;
    var visible = vv ? vv.height : window.innerHeight;
    var offset = 0;
    if (vv) offset = Math.max(0, window.innerHeight - vv.height - (vv.offsetTop || 0));
    el.style.bottom = offset + "px";
    el.style.maxHeight = Math.max(160, Math.floor(visible * 0.45)) + "px";
    if (!el.hidden) setBannerHeight(el);
  }

  function hideBanner() {
    var el = document.getElementById("ll-cookie-banner");
    if (el) {
      el.hidden = true;
      el.setAttribute("hidden", "");
    }
    document.body.classList.remove("ll-cookie-open");
  }

  function showBanner() {
    ensureBanner();
    var el = document.getElementById("ll-cookie-banner");
    el.hidden = false;
    el.removeAttribute("hidden");
    document.body.classList.add("ll-cookie-open");
    pinToVisualViewport();
    if (document.activeElement && document.activeElement.id === "ll-cookie-settings") {
      var first = el.querySelector("button, a");
      if (first) first.focus();
    }
  }

  function accept() {
    setChoice("accepted");
    hideBanner();
    loadAnalytics();
  }
  function refuse() {
    setChoice("refused");
    hideBanner();
    revokeAnalytics();
  }

  function ensureBanner() {
    if (document.getElementById("ll-cookie-banner")) return;
    var wrap = document.createElement("div");
    wrap.id = "ll-cookie-banner";
    wrap.className = "ll-cookie-banner";
    wrap.setAttribute("role", "dialog");
    wrap.setAttribute("aria-modal", "false");
    wrap.setAttribute("aria-labelledby", "ll-cookie-title");
    wrap.setAttribute("aria-describedby", "ll-cookie-desc");
    wrap.tabIndex = -1;
    wrap.hidden = true;
    wrap.innerHTML =
      '<div class="ll-cookie-inner">' +
        '<p id="ll-cookie-title" class="ll-cookie-title">Témoins et analyse / Cookies and analytics</p>' +
        '<div id="ll-cookie-desc" class="ll-cookie-copy">' +
          '<p lang="fr">Nous utilisons Google Analytics uniquement pour comprendre le trafic sur ce site. Pas de publicité. Consultez la <a href="/privacy/#consent">politique de confidentialité</a>.</p>' +
          '<p lang="en">We use Google Analytics only to understand how this site is used. No advertising. See the <a href="/privacy/#consent">privacy policy</a>.</p>' +
        "</div>" +
        '<div class="ll-cookie-actions">' +
          '<button type="button" class="ll-cookie-btn" data-ll-refuse>Refuser / Refuse</button>' +
          '<button type="button" class="ll-cookie-btn" data-ll-accept>Accepter / Accept</button>' +
        "</div>" +
      "</div>";
    document.body.appendChild(wrap);
    wrap.querySelector("[data-ll-refuse]").addEventListener("click", refuse);
    wrap.querySelector("[data-ll-accept]").addEventListener("click", accept);
    wrap.addEventListener("keydown", function (e) {
      if (e.key !== "Escape") return;
      if (getChoice()) hideBanner();
    });
    window.addEventListener("resize", pinToVisualViewport);
    if (window.visualViewport) {
      window.visualViewport.addEventListener("resize", pinToVisualViewport);
      window.visualViewport.addEventListener("scroll", pinToVisualViewport);
    }
  }

  function bindFooter() {
    document.addEventListener("click", function (e) {
      var t = e.target.closest && e.target.closest("#ll-cookie-settings");
      if (!t) return;
      e.preventDefault();
      showBanner();
    });
  }

  function init() {
    ensureBanner();
    bindFooter();
    var choice = getChoice();
    if (choice === "accepted") loadAnalytics();
    else if (choice !== "refused") showBanner();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();

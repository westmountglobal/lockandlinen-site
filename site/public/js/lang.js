(function () {
  "use strict";
  // Lock & Linen language routing. No IP lookup, no server redirect.
  // 1) A manual EN|FR choice (localStorage "ll_lang") always wins.
  // 2) Otherwise, once per browser (first visit), a visitor whose top browser
  //    language starts with "fr" is sent from an English page to its /fr/ twin.
  var PREF = "ll_lang", SEEN = "ll_lang_auto_done";
  var html = document.documentElement;
  var pageLang = (html.getAttribute("lang") || "en").slice(0, 2).toLowerCase();
  function get(k) { try { return window.localStorage.getItem(k); } catch (e) { return null; } }
  function set(k, v) { try { window.localStorage.setItem(k, v); } catch (e) {} }
  function twin(lang) {
    var el = document.querySelector('link[rel="alternate"][hreflang="' + lang + '"]');
    if (!el) return null;
    var u = el.getAttribute("href").replace(/^https?:\/\/[^\/]+/, "");
    return u + (location.hash || "");
  }
  function go(lang) {
    var t = twin(lang);
    if (t && t.split("#")[0] !== location.pathname) location.replace(t);
  }
  var isBot = /bot|crawl|spider|slurp|lighthouse/i.test(navigator.userAgent || "");
  var pref = get(PREF);
  if (!isBot) {
    if (pref === "en" || pref === "fr") {
      if (pref !== pageLang) go(pref);
    } else if (!get(SEEN)) {
      set(SEEN, "1");
      var langs = (navigator.languages && navigator.languages.length) ? navigator.languages : [navigator.language || navigator.userLanguage || ""];
      var first = String(langs[0] || "").toLowerCase();
      if (pageLang === "en" && first.indexOf("fr") === 0) go("fr");
    }
  }
  // Remember a manual toggle click.
  document.addEventListener("click", function (e) {
    var a = e.target.closest && e.target.closest("[data-ll-lang]");
    if (!a) return;
    set(PREF, a.getAttribute("data-ll-lang"));
    set(SEEN, "1");
  });
})();

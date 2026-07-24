from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,500;0,600;0,700;0,800;0,900;1,700;1,800;1,900&family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#020812;--panel:#07131f;--panel2:#0a1928;--line:#17354c;--line2:#0875c9;
  --text:#f6fbff;--muted:#bfe8ff;--blue:#29a5ff;--cyan:#31c8ff;--green:#43ef6c;
  --purple:#9a4dff;--red:#ff4a38;--yellow:#ffd323;
}
*{box-sizing:border-box}
html,body,[class*="css"]{font-family:'Inter','Segoe UI',Arial,sans-serif;color:var(--text);-webkit-font-smoothing:antialiased}
body{background:var(--bg)}
.stApp{background:
  radial-gradient(circle at 18% 0%,rgba(16,99,169,.14),transparent 26%),
  radial-gradient(circle at 100% 32%,rgba(0,94,180,.11),transparent 35%),
  linear-gradient(180deg,#020812 0%,#030b15 60%,#02070e 100%)!important}
#MainMenu,footer,[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stSidebarCollapseButton"]{display:none!important}
header[data-testid="stHeader"]{height:0!important;min-height:0!important;background:transparent!important}
.block-container{max-width:1540px!important;padding:.55rem 1.45rem 1.25rem!important}
[data-testid="stVerticalBlock"]{gap:.72rem}
[data-testid="stHorizontalBlock"]{gap:.75rem}

/* Header / professional template navigation */
.dd-logo-shell{height:96px;display:flex;align-items:center;justify-content:flex-start;overflow:visible;text-decoration:none}
.dd-logo-shell img{width:min(290px,100%);height:96px;object-fit:contain;object-position:left center;filter:drop-shadow(0 0 20px rgba(34,131,255,.22));transition:filter .22s ease,transform .22s ease}
.dd-logo-shell:hover img{transform:translateY(-1px);filter:drop-shadow(0 0 14px rgba(38,171,255,.75)) drop-shadow(0 0 28px rgba(51,95,255,.28))}
.dd-top-nav{height:98px;display:flex;align-items:stretch;justify-content:center;gap:8px;overflow-x:auto;scrollbar-width:none;background:linear-gradient(180deg,rgba(5,18,31,.46),rgba(2,9,17,.10));border-bottom:1px solid rgba(40,108,157,.12)}
.dd-top-nav::-webkit-scrollbar{display:none}
.dd-nav-link{position:relative;min-width:102px;height:96px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:8px;padding:0 12px;color:#edf7ff;text-decoration:none!important;text-transform:uppercase;font-size:.72rem;font-weight:800;letter-spacing:.025em;border:1px solid transparent;border-radius:10px 10px 0 0;transition:transform .18s ease,color .18s ease,background .18s ease,border-color .18s ease,box-shadow .18s ease}
.dd-nav-icon{width:29px;height:29px;display:flex;align-items:center;justify-content:center;color:#f6fbff;transition:transform .18s ease,color .18s ease,filter .18s ease}
.dd-nav-icon svg{width:25px;height:25px;fill:none;stroke:currentColor;stroke-width:1.75;stroke-linecap:round;stroke-linejoin:round}
.dd-nav-label{white-space:nowrap}
.dd-nav-link:hover{transform:translateY(-2px);color:#78d7ff;background:radial-gradient(circle at 50% 25%,rgba(34,172,255,.20),rgba(7,30,50,.25) 50%,transparent 76%);border-color:rgba(48,174,255,.18);box-shadow:inset 0 0 24px rgba(31,151,255,.08)}
.dd-nav-link:hover .dd-nav-icon{color:#a8e5ff;transform:scale(1.08);filter:drop-shadow(0 0 5px #2fc2ff) drop-shadow(0 0 13px rgba(43,134,255,.95))}
.dd-nav-link.active{color:#b6e7ff;background:linear-gradient(180deg,rgba(18,77,124,.36),rgba(6,31,53,.18));border-color:rgba(53,168,246,.16);box-shadow:inset 0 0 28px rgba(20,131,223,.12)}
.dd-nav-link.active:after{content:'';position:absolute;left:14px;right:14px;bottom:0;height:3px;border-radius:4px;background:#35b7ff;box-shadow:0 0 8px #2aaeff,0 0 20px rgba(39,144,255,.72)}
.dd-nav-link.active .dd-nav-icon{color:#9fddff;filter:drop-shadow(0 0 6px #2fc2ff) drop-shadow(0 0 15px rgba(41,113,255,.82))}
[data-testid="stDateInput"]{display:flex;align-items:center;height:96px}
[data-testid="stDateInput"]>div{width:100%}
[data-testid="stDateInput"] input{height:48px!important;background:#07121e!important;border:1px solid #263b4f!important;border-radius:10px!important;color:#fff!important;text-transform:uppercase;font-weight:700;padding-left:44px!important}
[data-testid="stDateInput"] [data-baseweb="input"]:before{content:'▣';position:absolute;left:14px;top:13px;color:#fff;z-index:2;font-size:1rem}
[data-testid="stDateInput"] svg{color:#fff!important}

/* Global controls */
.stButton>button{min-height:38px;border:1px solid #0879c8!important;border-radius:7px!important;background:linear-gradient(180deg,#071827,#06111d)!important;color:#4cc2ff!important;font-size:.72rem!important;font-weight:800!important;text-transform:uppercase!important;letter-spacing:.03em!important;box-shadow:none!important}
.stButton>button:hover{background:#09233a!important;color:#fff!important;border-color:#39baff!important;transform:translateY(-1px)}
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input{background:#07131f!important;border-color:#234057!important;color:#fff!important}
[data-testid="stMetric"],div[data-testid="stExpander"]{background:#07131f!important;border:1px solid #1c415d!important;border-radius:9px!important}
[data-testid="stMetric"]{padding:12px 14px!important}
[data-testid="stMetricLabel"]{color:#bfe8ff!important;font-size:.68rem!important;text-transform:uppercase!important;font-weight:800!important}
[data-testid="stMetricValue"]{color:#fff!important}
[data-testid="stDataFrame"]{border:1px solid #1c415d;border-radius:8px;overflow:hidden}
hr{border-color:#183248}

/* Home section heading */
.dd-home-section-title{display:flex;align-items:center;gap:10px;margin:3px 0 4px}
.dd-home-section-title>i{font-style:normal;color:#ffd000;font-size:1.35rem;filter:drop-shadow(0 0 7px #ffb800)}
.dd-home-section-title b{display:block;font-size:1rem;line-height:1.1;text-transform:uppercase;letter-spacing:.025em}
.dd-home-section-title span{display:block;color:#bfe8ff;font-size:.7rem;margin-top:2px}

/* Six compact player cards */
.dd-picks-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:0 0 12px}
.dd-pick-card{position:relative;height:160px;overflow:hidden;border:1px solid #1b3145;border-radius:8px;background:linear-gradient(145deg,#0a1928 0%,#07111c 60%,#08131f 100%);box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}
.dd-pick-rank{position:absolute;z-index:4;left:10px;top:9px;width:25px;height:25px;display:flex;align-items:center;justify-content:center;border-radius:4px;background:#286ea8;color:#fff;font-weight:900;font-size:.76rem;box-shadow:0 0 10px rgba(26,141,255,.25)}
.dd-pick-rank.rank-1{background:linear-gradient(135deg,#9c50ee,#6120bd)}
.dd-pick-photo{position:absolute;z-index:1;left:-2px;bottom:28px;width:112px;height:128px;object-fit:contain;object-position:center bottom;filter:drop-shadow(0 5px 7px rgba(0,0,0,.65))}
.dd-pick-copy{position:absolute;z-index:2;left:112px;right:7px;top:15px}
.dd-pick-name{min-height:42px;color:#fff;font-size:.92rem;font-weight:800;line-height:1.14}
.dd-pick-team{margin-top:3px;color:#bfe8ff;font-size:.67rem}
.dd-pick-prob{margin-top:8px;font-size:1.45rem;font-weight:900;line-height:1}
.dd-pick-label{margin-top:3px;color:#24a9ff;font-size:.58rem;font-weight:800;text-transform:uppercase}
.dd-pick-footer{position:absolute;z-index:3;left:0;right:0;bottom:0;height:29px;display:flex;align-items:center;justify-content:space-around;border-top:1px solid #1a2d3d;background:rgba(3,10,17,.88);color:#bfe8ff;font-size:.64rem;text-transform:uppercase}
.dd-pick-footer b{color:#fff;margin-right:4px}
.dd-pick-card:first-child .dd-pick-footer b{color:#b461ff}
.dd-pick-card:nth-child(5) .dd-pick-footer b{color:#42e875}

/* Weather panel */
.dd-weather-shell{margin:10px 0 12px;border:1px solid #123858;border-radius:9px;overflow:hidden;background:#06111b}
.dd-weather-heading{height:53px;display:flex;align-items:center;padding:9px 14px;border-bottom:1px solid #17364e;background:linear-gradient(90deg,#081a2a,#06131f)}
.dd-weather-heading>div{display:flex;align-items:center;gap:9px}
.dd-weather-heading b{display:block;text-transform:uppercase;font-size:1rem}
.dd-weather-heading small{display:block;margin-left:7px;color:#bfe8ff;font-size:.68rem;text-transform:none;font-weight:500}
.dd-weather-cloud{color:#31afff;font-size:1.45rem}
.dd-weather-layout{display:grid;grid-template-columns:29% 50.5% 20.5%;min-height:365px}
.dd-weather-summary,.dd-field-panel,.dd-forecast-panel{position:relative;padding:12px;border-right:1px solid #17364e;background:linear-gradient(180deg,#07141f,#05101a)}
.dd-forecast-panel{border-right:0}
.dd-stadium-row{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border:1px solid #18364d;border-radius:6px;background:#07131d}
.dd-stadium-row b{display:block;font-size:1.05rem;text-transform:uppercase}.dd-stadium-row span{display:block;color:#bfe8ff;font-size:.62rem;margin-top:2px}
.dd-stadium-row em{min-width:94px;padding:6px 8px;border:1px solid #24513b;border-radius:6px;background:#082014;color:#54f178;text-align:center;font-style:normal;font-weight:900;font-size:.78rem}.dd-stadium-row em small{display:block;color:#b3c1ca;font-size:.49rem;font-weight:500;margin-top:2px}.dd-stadium-row em.poor{color:#ff5a49;border-color:#6b2d2a;background:#25100f}.dd-stadium-row em.neutral{color:#ffd323;border-color:#6b5b1d;background:#201c0b}.dd-stadium-row em.unavailable{color:#9aabba;border-color:#384958;background:#101720}
.dd-big-temp{height:82px;display:flex;align-items:center;gap:28px;padding:5px 8px;border-bottom:1px solid #19364c}
.dd-big-temp>strong{font-family:'Barlow Condensed',sans-serif;font-size:3.15rem;line-height:1;color:#fff}
.dd-big-temp>div{display:grid;grid-template-columns:44px 1fr;align-items:center}.dd-big-temp i{grid-row:1/3;font-style:normal;font-size:2.3rem}.dd-big-temp b{font-size:.76rem}.dd-big-temp span{color:#bfe8ff;font-size:.59rem;margin-top:2px}
.dd-condition-grid{display:grid;grid-template-columns:repeat(3,1fr);gap:0;padding:8px 0;border-bottom:1px solid #19364c}
.dd-condition-grid>div{min-height:55px;display:grid;grid-template-columns:24px 1fr;align-content:center;padding:5px 7px}.dd-condition-grid i{grid-row:1/4;color:#24b6ff;font-style:normal;font-size:1rem}.dd-condition-grid span{color:#31aefb;font-size:.57rem;text-transform:uppercase}.dd-condition-grid b{font-size:.68rem}.dd-condition-grid small{color:#94a4b2;font-size:.52rem}
.dd-impact-title{padding:7px 0 5px;color:#7e93a5;font-size:.59rem;text-transform:uppercase}
.dd-impact-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px}.dd-impact-grid>div{padding:6px 4px;border:1px solid #173247;border-radius:5px;background:#071620;text-align:center}.dd-impact-grid span{display:block;font-size:.5rem}.dd-impact-grid b{display:block;margin-top:3px;font-size:1rem}.dd-impact-grid .green{color:#46ed70}.dd-impact-grid .yellow{color:#ffd323}.dd-impact-grid .red{color:#ff4a38}.dd-impact-grid .blue{color:#36aaff}
.dd-field-panel{overflow:hidden;padding:8px 10px 0;background:radial-gradient(circle at 50% 55%,rgba(20,75,45,.14),transparent 38%),#06121c}
.dd-field-title{text-align:center;color:#68bfff;font-size:.85rem;text-transform:uppercase;letter-spacing:.04em}
.dd-field-svg{position:absolute;left:7%;right:2%;bottom:4px;width:91%;height:316px}
.dd-wind-box{position:absolute;z-index:3;left:12px;top:54px;width:112px;padding:10px;border:1px solid #19364d;border-radius:6px;background:rgba(5,16,25,.94)}.dd-wind-box span{display:block;color:#9eafbc;font-size:.53rem;text-transform:uppercase}.dd-wind-box b{display:block;color:#43aaff;font-size:.77rem;margin:4px 0 12px}.dd-wind-box strong{display:block;color:#43aaff;font-size:1.05rem;margin-top:3px}
.dd-zone-tag{position:absolute;z-index:4;min-width:112px;padding:7px 9px;border:1px solid var(--zone);border-radius:6px;background:rgba(4,14,23,.92);text-align:center;box-shadow:0 0 12px color-mix(in srgb,var(--zone) 20%,transparent)}.dd-zone-tag b{display:block;color:var(--zone);font-size:1.2rem}.dd-zone-tag span{display:block;color:#fff;font-size:.57rem;text-transform:uppercase}.dd-zone-tag.lf{left:12%;top:57%}.dd-zone-tag.cf{left:50%;top:14%;transform:translateX(-50%)}.dd-zone-tag.rf{right:5%;top:31%}
.dd-field-wind{position:absolute;z-index:4;left:0;right:0;bottom:3px;text-align:center;color:#99aab8;font-size:.68rem}.dd-field-wind b{color:#2ab0ff}
.dd-forecast-title{color:#68bfff;font-size:.86rem;text-transform:uppercase}.dd-game-time{margin:4px 0 10px;color:#fff;font-weight:700;font-size:.82rem}
.dd-forecast-list{border:1px solid #18364d;border-radius:6px;overflow:hidden}.dd-forecast-list>div{min-height:39px;display:flex;align-items:center;justify-content:space-between;padding:7px 10px;border-bottom:1px solid #173247;background:#07131d}.dd-forecast-list>div:last-child{border-bottom:0}.dd-forecast-list span{color:#a7b5c1;font-size:.62rem;text-transform:uppercase}.dd-forecast-list b{font-size:.7rem;text-align:right}.dd-forecast-list .impact span,.dd-forecast-list .impact b{color:#ff4a38;font-weight:900}
.dd-hourly-button{margin-top:11px;padding:9px;border:1px solid #0d79bf;border-radius:5px;color:#32b9ff;text-align:center;font-size:.61rem;text-transform:uppercase}.dd-weather-grade{margin-top:7px;color:#7d91a2;font-size:.58rem;text-align:center;text-transform:uppercase}.dd-weather-grade b{color:#fff;font-size:.72rem;margin-left:4px}

/* Bottom dashboard panels */
.dd-panel-title{display:flex;align-items:center;gap:9px;min-height:44px;padding:7px 8px}.dd-panel-title>i{font-style:normal;color:#b05cff;font-size:1.3rem}.dd-panel-title b{display:block;text-transform:uppercase;font-size:.93rem}.dd-panel-title span{display:block;color:#8799a8;font-size:.62rem;margin-top:1px}
.dd-team-cards{display:grid;grid-template-columns:repeat(5,minmax(0,1fr));gap:6px;padding:6px;border:1px solid #27164d;border-radius:8px;background:linear-gradient(90deg,rgba(64,19,109,.14),rgba(5,14,23,.95))}
.dd-team-card{overflow:hidden;border:1px solid #1b3347;border-radius:6px;background:#07131f}.dd-team-match{padding:7px 3px;text-align:center;color:#fff;font-size:.64rem;font-weight:700}.dd-team-logos{height:49px;display:flex;align-items:center;justify-content:center;gap:12px}.dd-team-logos img{width:37px;height:37px;object-fit:contain}.dd-team-logos>span{color:#9caab6;font-size:.58rem}.dd-team-logos>b{font-size:.72rem}
.dd-team-metrics{display:grid;grid-template-columns:1fr 1fr;padding:4px 3px 7px}.dd-team-metrics>div{text-align:center}.dd-team-metrics span{display:block;color:#899baa;font-size:.45rem}.dd-team-metrics b{display:block;color:var(--accent);font-size:1rem;margin-top:3px}.dd-team-metrics small{display:block;color:#9fb0bc;font-size:.52rem;margin-top:2px}.dd-view-sheet{padding:7px;border-top:1px solid #173046;background:color-mix(in srgb,var(--accent) 10%,#07131f);color:var(--accent);text-align:center;text-transform:uppercase;font-size:.56rem;font-weight:800}
.dd-small-panel-title{height:45px;display:flex;align-items:center;justify-content:space-between;padding:0 9px;border:1px solid #17344b;border-bottom:0;border-radius:8px 8px 0 0;background:#07131f}.dd-small-panel-title b{font-size:.78rem;text-transform:uppercase}.dd-small-panel-title span{color:#2baeff;font-size:.52rem;text-transform:uppercase}
.dd-games-list{border:1px solid #17344b;border-radius:0 0 8px 8px;overflow:hidden}.dd-game-row{min-height:38px;display:grid;grid-template-columns:1fr 55px 46px;align-items:center;gap:5px;padding:6px 8px;border-bottom:1px solid #162e42;background:#07131f}.dd-game-row:last-child{border-bottom:0}.dd-game-row b{font-size:.62rem}.dd-game-row span{color:#9eacb8;font-size:.52rem}.dd-game-row em{font-style:normal;font-size:.58rem;font-weight:900;text-align:right}
.st-key-quick_tools{border:1px solid #17344b;border-radius:8px;background:#07131f;overflow:hidden}.st-key-quick_tools .dd-small-panel-title{border:0;border-bottom:1px solid #17344b;border-radius:0}.st-key-quick_tools [data-testid="stButton"]{padding:0 8px}.st-key-quick_tools .stButton>button{min-height:44px!important;justify-content:flex-start!important;border:0!important;border-bottom:1px solid #162e42!important;border-radius:0!important;background:transparent!important;color:#fff!important;text-align:left!important;text-transform:none!important;font-size:.66rem!important}.st-key-quick_tools .stButton>button:hover{background:#0a1d2d!important;color:#36baff!important}
.dd-app-footer{display:grid;grid-template-columns:repeat(4,1fr) auto;align-items:center;gap:16px;margin-top:12px;padding:9px 15px;border:1px solid #17334a;border-radius:8px;background:#06111b}.dd-app-footer>div{display:grid;grid-template-columns:31px 1fr}.dd-app-footer i{grid-row:1/3;width:27px;height:27px;display:flex;align-items:center;justify-content:center;border:1px solid #22557b;border-radius:6px;color:#39b4ff;font-style:normal}.dd-app-footer b{color:#35adf8;font-size:.62rem;text-transform:uppercase}.dd-app-footer span{color:#8b9ba8;font-size:.54rem}.dd-app-footer small{color:#6e7d89;font-size:.53rem;white-space:nowrap}

/* Existing secondary pages */
.dd-hero{display:flex;align-items:flex-end;justify-content:space-between;gap:20px;margin:8px 0 12px;padding:22px;border:1px solid #1b4564;border-radius:10px;background:linear-gradient(145deg,#0a1b2b,#06111b)}
.dd-eyebrow{color:#2bb6ff;font-family:'Barlow Condensed',sans-serif;font-size:.67rem;font-weight:800;letter-spacing:.12em;text-transform:uppercase}.dd-hero-title{font-family:'Barlow Condensed',sans-serif;font-size:clamp(2rem,4vw,4rem);font-weight:900;font-style:italic;text-transform:uppercase;line-height:.95}.dd-hero-title span{color:#2fa7ff}.dd-hero-sub{max-width:760px;margin-top:9px;color:#9db0bf;font-size:.78rem}.dd-board-header{display:flex;gap:8px}.dd-board-header>div{min-width:105px;padding:10px;border:1px solid #1c4b6d;border-radius:7px;background:#07131f}.dd-board-header small{display:block;color:#7f94a6;font-size:.5rem;text-transform:uppercase}.dd-board-header b{display:block;margin-top:4px;color:#fff;font-size:.85rem}
.dd-sectionbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:14px 0 8px;padding:9px 12px;border:1px solid #1b4564;border-radius:7px;background:#07131f}.dd-sectionbar-title{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;font-size:1.1rem;font-weight:800}.dd-sectionbar-sub{color:#89a0b2;font-size:.66rem}
.dd-table-shell{overflow:auto;border:1px solid #1c4564;border-radius:8px}.dd-rank-table{width:100%;min-width:1050px;border-collapse:collapse;background:#06111b}.dd-rank-table th{padding:9px;background:#0a1928;color:#8fa8bb;font-size:.56rem;text-transform:uppercase}.dd-rank-table td{padding:8px;border-bottom:1px solid #152e42;color:#fff;font-size:.68rem}.dd-player-wrap,.dd-team-wrap{display:flex;align-items:center;gap:8px}.dd-player-wrap>img{width:40px;height:40px;object-fit:contain}.dd-team-wrap img{width:25px;height:25px}.dd-player-text strong,.dd-player-text span{display:block}.dd-player-text span{color:#bfe8ff;font-size:.55rem}.dd-rank-badge{display:inline-flex;width:24px;height:24px;align-items:center;justify-content:center;border-radius:5px;background:#1e5d91;font-weight:900}.dd-score-ring{font-weight:900}.dd-mini-stat small{margin-left:2px;color:#bfe8ff}.dd-num,.dd-odds{text-align:center}.dd-book-price{display:flex;flex-direction:column;align-items:center;color:#43ef6c}.dd-book-price small,.dd-book-price em{font-size:.47rem}.dd-spark{display:flex;align-items:flex-end;gap:2px;height:24px}.dd-spark i{display:block;width:3px;background:var(--spark)}.dd-trend-label{font-size:.48rem;text-align:center}
.dd-player-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.dd-player-card{position:relative;padding:12px;border:1px solid #1b4564;border-radius:9px;background:#07131f}.dd-player-card-score{position:absolute;right:12px;top:12px;color:var(--accent);font-size:1.5rem;font-weight:900}.dd-player-card-score small{display:block;color:#bfe8ff;font-size:.48rem;text-transform:uppercase}.dd-player-card-head{display:flex;align-items:center;gap:10px}.dd-player-card-head>img{width:64px;height:64px;object-fit:contain}.dd-player-card-name{font-weight:900}.dd-player-card-team{display:flex;align-items:center;gap:5px;color:#bfe8ff;font-size:.59rem}.dd-player-card-team img{width:20px;height:20px}.dd-card-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:10px}.dd-card-stat{padding:7px;border:1px solid #173248;border-radius:5px;text-align:center}.dd-card-stat b,.dd-card-stat span{display:block}.dd-card-stat span{color:#bfe8ff;font-size:.48rem;text-transform:uppercase}.dd-card-footer{display:flex;justify-content:space-between;margin-top:9px;color:#bfe8ff;font-size:.55rem}.dd-risk-chip{padding:2px 6px;border:1px solid var(--accent);border-radius:99px;color:var(--accent)}
.dd-cheat-grid,.dd-weather-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.dd-cheat-card,.dd-weather-card{border:1px solid #1b4564;border-radius:9px;background:#07131f;overflow:hidden}.dd-cheat-head,.dd-weather-card-head{display:flex;justify-content:space-between;padding:12px;border-bottom:1px solid #173248}.dd-cheat-row{display:grid;grid-template-columns:32px minmax(130px,1.4fr) repeat(5,.65fr);align-items:center;gap:6px;padding:8px;border-bottom:1px solid #152e42}.dd-cheat-player{display:flex;align-items:center;gap:7px}.dd-cheat-player img{width:35px;height:35px;object-fit:contain}.dd-cheat-metric{text-align:center}.dd-cheat-metric b,.dd-cheat-metric span{display:block}.dd-cheat-metric span{font-size:.48rem;color:#bfe8ff}.dd-weather-grade{color:#43ef6c;font-weight:900}.dd-weather-metrics{display:grid;grid-template-columns:repeat(4,1fr)}.dd-weather-metrics>div{padding:9px;text-align:center;border-right:1px solid #173248}.dd-weather-metrics b,.dd-weather-metrics span{display:block}.dd-weather-metrics span{font-size:.48rem;color:#bfe8ff}
.dd-profile{position:relative;min-height:390px;overflow:hidden;border:1px solid #1c5a83;border-radius:10px;background:linear-gradient(90deg,rgba(3,12,20,.94),rgba(3,12,20,.36)),var(--profile-bg);background-size:cover}.dd-profile-inner{padding:32px}.dd-profile-copy{position:relative;z-index:2}.dd-player-name{font-family:'Barlow Condensed',sans-serif;font-size:3.2rem;font-weight:900;text-transform:uppercase}.dd-profile-score{font-size:2rem;color:#38b7ff;font-weight:900}.dd-profile-score small{display:block;color:#bfe8ff;font-size:.55rem;text-transform:uppercase}.dd-headshot{position:absolute;right:2%;bottom:0;height:88%;object-fit:contain}.dd-meter{height:7px;border-radius:99px;background:#132e42}.dd-meter span{display:block;height:100%;border-radius:99px;background:#2cafff}.dd-ribbon{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.dd-ribbon span{padding:5px 8px;border:1px solid #1b5276;border-radius:99px;font-size:.56rem;text-transform:uppercase}
.dd-parlay-ticket,.dd-insight,.dd-parlay-mode,.dd-odds-upload{border:1px solid #1b4564;border-radius:9px;background:#07131f}.dd-parlay-ticket{overflow:hidden}.dd-ticket-head{padding:12px;border-bottom:1px solid #173248}.dd-ticket-leg{display:grid;grid-template-columns:45px minmax(160px,1.5fr) repeat(4,.7fr);align-items:center;gap:7px;padding:9px;border-bottom:1px solid #152e42}.dd-ticket-player{display:flex;align-items:center;gap:8px}.dd-ticket-player img{width:40px;height:40px;object-fit:contain}.dd-ticket-summary{display:grid;grid-template-columns:repeat(4,1fr);gap:8px;padding:10px}.dd-ticket-metric{text-align:center}.dd-insight,.dd-parlay-mode,.dd-odds-upload{padding:12px}


/* Clickable intelligence cards */
.dd-pick-card-link,.dd-team-card-link{display:block;color:inherit!important;text-decoration:none!important}
.dd-pick-card-link .dd-pick-card,.dd-team-card-link .dd-team-card{transition:transform .18s ease,border-color .18s ease,box-shadow .18s ease,background .18s ease}
.dd-pick-card-link:hover .dd-pick-card{transform:translateY(-3px);border-color:#2d9fdf;box-shadow:0 0 0 1px rgba(56,174,255,.16),0 10px 28px rgba(0,109,204,.18),inset 0 0 22px rgba(36,152,255,.06)}
.dd-team-card-link:hover .dd-team-card{transform:translateY(-3px);border-color:var(--accent);box-shadow:0 0 18px color-mix(in srgb,var(--accent) 38%,transparent),0 10px 25px rgba(0,0,0,.28)}
.dd-team-card-link:hover .dd-view-sheet{color:#fff;background:linear-gradient(90deg,color-mix(in srgb,var(--accent) 32%,#081525),#071421);text-shadow:0 0 8px var(--accent)}
.dd-team-card-link:focus-visible,.dd-pick-card-link:focus-visible{outline:2px solid #42c7ff;outline-offset:3px;border-radius:9px}

/* Dark neon Altair/Vega charts */
[data-testid="stVegaLiteChart"]{overflow:hidden;border:1px solid #173b58;border-radius:10px;background:linear-gradient(180deg,#071521,#04101a)!important;box-shadow:inset 0 1px 0 rgba(255,255,255,.025),0 0 24px rgba(0,117,204,.07);padding:8px}
[data-testid="stVegaLiteChart"]>div{background:transparent!important}
.vega-embed,.vega-embed>div{background:transparent!important}
.vega-actions{display:none!important}

/* Normal content radios are compact pills instead of inherited navigation cards */
div[data-testid="stRadio"]>div{display:flex;gap:8px;flex-wrap:wrap}
div[data-testid="stRadio"] label{padding:7px 12px!important;border:1px solid #24425a!important;border-radius:7px!important;background:#07131f!important}
div[data-testid="stRadio"] label:has(input:checked){border-color:#2caeff!important;background:#0b2942!important;box-shadow:0 0 12px rgba(39,172,255,.16)}
div[data-testid="stRadio"] label p{font-size:.76rem!important;font-weight:800!important;color:#dbeeff!important}

@media(max-width:1250px){
 .block-container{padding:.45rem .75rem 1rem!important}.dd-logo-shell img{width:230px}.dd-picks-grid{grid-template-columns:repeat(3,1fr)}.dd-pick-card{height:155px}.dd-weather-layout{grid-template-columns:36% 64%}.dd-forecast-panel{grid-column:1/-1;border-top:1px solid #17364e;border-right:0}.dd-forecast-list{display:grid;grid-template-columns:repeat(3,1fr)}.dd-forecast-list>div:nth-child(3n){border-right:0}.dd-team-cards{grid-template-columns:repeat(3,1fr)}.dd-app-footer{grid-template-columns:repeat(2,1fr)}.dd-app-footer small{grid-column:1/-1}}
@media(max-width:820px){
 .dd-top-nav{height:74px;justify-content:flex-start;gap:3px}.dd-nav-link{min-width:86px;height:72px;padding:0 7px;font-size:.61rem;gap:5px}.dd-nav-icon{width:24px;height:24px}.dd-nav-icon svg{width:21px;height:21px}

 .block-container{padding:.35rem .5rem 1rem!important}.dd-logo-shell{height:74px}.dd-logo-shell img{height:70px;width:195px}div[data-testid="stRadio"]{height:74px}div[data-testid="stRadio"] label{min-width:84px;min-height:72px;padding:0 7px!important}div[data-testid="stRadio"] label p{font-size:.62rem!important}div[data-testid="stRadio"] label p:before{font-size:1.25rem}[data-testid="stDateInput"]{height:74px}[data-testid="stDateInput"] input{height:42px!important;font-size:.72rem!important}.dd-picks-grid{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:5px}.dd-pick-card{min-width:245px;scroll-snap-align:start}.dd-weather-layout{grid-template-columns:1fr}.dd-weather-summary,.dd-field-panel{border-right:0;border-bottom:1px solid #17364e}.dd-field-panel{min-height:380px}.dd-forecast-panel{grid-column:auto}.dd-team-cards{display:flex;overflow-x:auto}.dd-team-card{min-width:145px}.dd-player-grid,.dd-cheat-grid,.dd-weather-grid{grid-template-columns:1fr}.dd-hero{align-items:flex-start;flex-direction:column}.dd-board-header{flex-wrap:wrap}.dd-app-footer{grid-template-columns:1fr}.dd-app-footer small{grid-column:auto}}
@media(max-width:560px){
 .dd-top-nav{height:66px}.dd-nav-link{min-width:75px;height:64px;padding:0 5px;font-size:.54rem;gap:4px}.dd-nav-icon{width:21px;height:21px}.dd-nav-icon svg{width:19px;height:19px}

 .dd-logo-shell img{width:160px}.dd-logo-shell{height:66px}div[data-testid="stRadio"]{height:66px}div[data-testid="stRadio"] label{min-width:72px;min-height:64px}div[data-testid="stRadio"] label p{font-size:.55rem!important;gap:5px!important}div[data-testid="stRadio"] label p:before{font-size:1.08rem}[data-testid="stDateInput"]{height:66px}[data-testid="stDateInput"] input{padding-left:28px!important;font-size:.62rem!important}.dd-weather-heading small{display:none}.dd-condition-grid{grid-template-columns:repeat(2,1fr)}.dd-impact-grid{grid-template-columns:repeat(2,1fr)}.dd-zone-tag{min-width:92px}.dd-zone-tag.lf{left:3%}.dd-zone-tag.rf{right:2%}.dd-field-svg{left:0;width:100%}.dd-field-panel{min-height:350px}.dd-forecast-list{grid-template-columns:1fr}.dd-team-cards{padding:5px}.dd-app-footer{display:none}.dd-card-stats{grid-template-columns:repeat(2,1fr)}}
/* =====================================================================
   V15 NEON INTELLIGENCE REBUILD
   High-contrast typography, multicolor neon data components, matchup
   sheets, game simulations, projection reasoning, and lockable parlay UI.
   ===================================================================== */
:root{
 --dd-cyan:#27c7ff;
 --dd-pink:#ff4df2;
 --dd-green:#35f29a;
 --dd-gold:#ffd83d;
 --dd-purple:#a85cff;
 --dd-red:#ff5f6d;
 --dd-ink:#020812;
 --dd-panel:#061421;
 --dd-panel-2:#081a2a;
 --dd-text:#f7fbff;
 --dd-soft:#c8efff;
}
html,body,[class*="css"]{color:var(--dd-text)!important}
.stApp{background:
 radial-gradient(circle at 9% 12%,rgba(255,77,242,.09),transparent 24%),
 radial-gradient(circle at 88% 8%,rgba(39,199,255,.11),transparent 27%),
 radial-gradient(circle at 55% 96%,rgba(53,242,154,.06),transparent 24%),
 linear-gradient(180deg,#01060d 0%,#03111d 44%,#010712 100%)!important}
.stMarkdown,.stMarkdown p,.stMarkdown li,.stCaption,.stCaptionContainer,[data-testid="stCaptionContainer"],label,[data-testid="stWidgetLabel"] p{
 color:var(--dd-soft)!important;font-weight:700!important
}
small,.dd-subtitle,.dd-meta,.dd-muted,.dd-card-footer,.dd-player-card-team,.dd-player-card-score small,.dd-profile-score small,.dd-mini-stat small,.dd-cheat-metric span,.dd-weather-metrics span,.dd-book-price small,.dd-book-price em,.dd-trend-label,.dd-player-text span,.dd-card-stat span,.dd-team-metrics span,.dd-team-metrics small,.dd-condition-grid span,.dd-impact-grid span,.dd-forecast-list span,.dd-footer-item span{
 color:var(--dd-soft)!important;font-weight:700!important
}
[data-testid="stMetricLabel"] p,[data-testid="stMetricDelta"]{color:#9ee4ff!important;font-weight:800!important}
[data-testid="stMetricValue"]{color:#fff!important;font-weight:900!important;text-shadow:0 0 10px rgba(39,199,255,.16)}
hr{border-color:rgba(39,199,255,.24)!important}

/* Section identity: rotate neon accents rather than one blue theme */
.dd-section{border-left:3px solid var(--dd-cyan);padding-left:12px}
.dd-section:nth-of-type(4n+1){border-left-color:var(--dd-pink)}
.dd-section:nth-of-type(4n+2){border-left-color:var(--dd-green)}
.dd-section:nth-of-type(4n+3){border-left-color:var(--dd-gold)}
.dd-section-kicker{color:var(--dd-cyan)!important;font-weight:900!important;letter-spacing:.12em}
.dd-section-title{color:#fff!important;font-weight:900!important}
.dd-section-subtitle{color:var(--dd-soft)!important;font-weight:800!important}

/* Top six projection cards with visible model reasoning */
.dd-picks-grid.v15{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;overflow:visible}
.dd-pick-card.v15{position:relative;height:278px;padding:0;overflow:hidden;border:1px solid rgba(39,199,255,.28);border-radius:10px;background:
 radial-gradient(circle at 50% 36%,rgba(39,199,255,.08),transparent 35%),
 linear-gradient(180deg,#071522 0%,#050e18 66%,#030912 100%);box-shadow:inset 0 0 24px rgba(0,0,0,.52)}
.dd-pick-card.v15:before{content:'';position:absolute;inset:0;pointer-events:none;background:linear-gradient(125deg,rgba(255,255,255,.05),transparent 23%,transparent 75%,rgba(39,199,255,.035))}
.dd-pick-card.v15 .dd-pick-rank{position:absolute;z-index:5;left:9px;top:9px;width:25px;height:25px;border-radius:5px;display:flex;align-items:center;justify-content:center;color:#fff;font-size:.75rem;font-weight:900;background:linear-gradient(135deg,#1e7fd4,#264a8c);box-shadow:0 0 14px rgba(39,199,255,.34)}
.dd-pick-card.v15 .rank-1{background:linear-gradient(135deg,#9f4cff,#5b20bd);box-shadow:0 0 16px rgba(168,92,255,.55)}
.dd-pick-card.v15 .dd-pick-tier{position:absolute;z-index:4;right:8px;top:9px;padding:4px 7px;border:1px solid rgba(255,216,61,.48);border-radius:99px;color:#ffe66f;font-size:.52rem;font-weight:900;letter-spacing:.08em;text-transform:uppercase;background:rgba(35,26,4,.82)}
.dd-pick-card.v15 .dd-pick-photo{position:absolute;left:50%;top:25px;transform:translateX(-50%);width:135px;height:122px;object-fit:contain;object-position:center bottom;filter:drop-shadow(0 10px 13px rgba(0,0,0,.78))}
.dd-pick-card.v15 .dd-pick-copy{position:absolute;left:0;right:0;top:139px;padding:8px 10px 43px;background:linear-gradient(180deg,rgba(4,13,23,.22),rgba(4,11,19,.98) 18%)}
.dd-pick-card.v15 .dd-pick-name{color:#fff;font-size:.9rem;font-weight:900;line-height:1.05;text-align:center;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dd-pick-card.v15 .dd-pick-team{margin-top:2px;color:#a8e8ff!important;font-size:.55rem;font-weight:800;text-align:center;text-transform:uppercase}
.dd-pick-card.v15 .dd-pick-prob-row{display:flex;align-items:flex-end;justify-content:center;gap:9px;margin:6px 0 5px}
.dd-pick-card.v15 .dd-pick-prob-row b{font-size:1.42rem;font-weight:900;line-height:1;text-shadow:0 0 12px currentColor}
.dd-pick-card.v15 .dd-pick-prob-row span{color:#ffd83d;font-size:.53rem;font-weight:900}
.dd-pick-card.v15 .dd-pick-reason{display:flex;align-items:flex-start;gap:5px;margin-top:3px;color:#e9f7ff;font-size:.49rem;font-weight:800;line-height:1.2}
.dd-pick-card.v15 .dd-pick-reason i{flex:0 0 auto;width:5px;height:5px;margin-top:2px;border-radius:50%;background:var(--dd-green);box-shadow:0 0 7px var(--dd-green)}
.dd-pick-card.v15 .dd-pick-reason.alt i{background:var(--dd-pink);box-shadow:0 0 7px var(--dd-pink)}
.dd-pick-card.v15 .dd-pick-pitcher{position:absolute;left:0;right:0;bottom:0;z-index:5;padding:5px 7px;background:linear-gradient(90deg,rgba(26,10,36,.96),rgba(5,28,38,.96));border-top:1px solid rgba(255,77,242,.25);text-align:center}
.dd-pick-card.v15 .dd-pick-pitcher strong,.dd-pick-card.v15 .dd-pick-pitcher span{display:block;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
.dd-pick-card.v15 .dd-pick-pitcher strong{color:#fff;font-size:.53rem;font-weight:900}
.dd-pick-card.v15 .dd-pick-pitcher span{color:#c8efff;font-size:.46rem;font-weight:800}
.dd-pick-card-link:hover .dd-pick-card.v15{transform:translateY(-5px);border-color:var(--dd-pink);box-shadow:0 0 0 1px rgba(255,77,242,.2),0 0 24px rgba(255,77,242,.16),0 14px 28px rgba(0,0,0,.38)}

/* Universal neon table system: no native white dataframe surfaces */
.dd-neon-table-shell{position:relative;border:1px solid rgba(39,199,255,.36);border-radius:11px;background:linear-gradient(180deg,rgba(6,20,33,.98),rgba(2,10,18,.98));box-shadow:inset 0 0 28px rgba(0,0,0,.42),0 0 24px rgba(39,199,255,.055);overflow:auto;scrollbar-color:#2da8df #06131f}
.dd-neon-grid{display:grid;min-width:900px}
.dd-neon-head{position:sticky;top:0;z-index:5;background:linear-gradient(90deg,#0b263b,#151532 42%,#082d2b);border-bottom:1px solid rgba(255,77,242,.34);box-shadow:0 8px 18px rgba(0,0,0,.30)}
.dd-neon-th{padding:10px 9px;color:#fff;font-size:.58rem;font-weight:900;text-transform:uppercase;letter-spacing:.07em}
.dd-neon-tr{display:contents}
.dd-neon-td{padding:9px;border-bottom:1px solid rgba(76,139,179,.16);color:#f3fbff;font-size:.66rem;font-weight:800;display:flex;align-items:center;min-height:50px}
.dd-neon-grid:nth-child(4n+2) .dd-neon-td{background:rgba(39,199,255,.025)}
.dd-neon-grid:nth-child(4n+3) .dd-neon-td{background:rgba(255,77,242,.018)}
.dd-neon-grid:hover .dd-neon-td{background:linear-gradient(90deg,rgba(39,199,255,.08),rgba(255,77,242,.045))}
.dd-neon-progress{width:100%}.dd-neon-progress-track{height:7px;border-radius:99px;background:#112a3b;border:1px solid rgba(255,255,255,.04);overflow:hidden;box-shadow:inset 0 2px 4px rgba(0,0,0,.45)}
.dd-neon-progress-track i{display:block;height:100%;border-radius:99px;background:linear-gradient(90deg,color-mix(in srgb,var(--bar) 70%,#fff),var(--bar));box-shadow:0 0 8px var(--bar),0 0 17px color-mix(in srgb,var(--bar) 50%,transparent)}
.dd-neon-progress b{display:block;margin-top:3px;color:#fff;font-size:.58rem;font-weight:900;text-align:right}

/* Native dataframe fallback is forced dark if a future page adds one */
[data-testid="stDataFrame"],[data-testid="stTable"]{border:1px solid rgba(39,199,255,.34)!important;border-radius:10px!important;background:#06131f!important;overflow:hidden}
[data-testid="stDataFrame"] canvas{filter:invert(.92) hue-rotate(165deg) saturate(1.45) brightness(.95)}

/* Matchup-first team sheets */
.dd-game-tabs{display:flex;gap:9px;overflow-x:auto;padding:4px 2px 11px;scrollbar-width:thin}
.dd-game-tab{flex:0 0 164px;display:grid;grid-template-columns:28px 1fr 28px;align-items:center;gap:7px;padding:9px;border:1px solid #234a66;border-radius:9px;background:linear-gradient(180deg,#081926,#05101a);color:#fff!important;text-decoration:none!important;transition:.18s ease}
.dd-game-tab img{width:27px;height:27px;object-fit:contain}.dd-game-tab div{text-align:center}.dd-game-tab b,.dd-game-tab span,.dd-game-tab small{display:block}.dd-game-tab b{font-size:.62rem;font-weight:900}.dd-game-tab span{color:#35f29a;font-size:.68rem;font-weight:900}.dd-game-tab small{color:#bfe9ff!important;font-size:.46rem;font-weight:800}
.dd-game-tab:hover,.dd-game-tab.active{transform:translateY(-3px);border-color:#ff4df2;box-shadow:0 0 18px rgba(255,77,242,.22),inset 0 0 18px rgba(39,199,255,.06)}
.dd-game-tab.active{background:linear-gradient(135deg,rgba(42,53,96,.92),rgba(21,25,52,.96))}
.dd-matchup-sheet-grid{display:grid;grid-template-columns:1fr;gap:14px}
.dd-matchup-team{overflow:hidden;border:1px solid color-mix(in srgb,var(--team-a) 58%,#24445e);border-radius:11px;background:linear-gradient(180deg,#071724,#030d16);box-shadow:inset 0 0 24px rgba(0,0,0,.35),0 0 18px color-mix(in srgb,var(--team-a) 10%,transparent)}
.dd-matchup-team-head{display:flex;align-items:center;justify-content:space-between;gap:14px;padding:13px 15px;background:linear-gradient(90deg,color-mix(in srgb,var(--team-a) 20%,#07131f),#081523 52%,color-mix(in srgb,var(--team-b) 14%,#07131f));border-bottom:1px solid color-mix(in srgb,var(--team-a) 35%,transparent)}
.dd-matchup-team-brand{display:flex;align-items:center;gap:11px}.dd-matchup-team-brand img{width:48px;height:48px;object-fit:contain}.dd-matchup-team-brand b,.dd-matchup-team-brand span{display:block}.dd-matchup-team-brand b{color:#fff;font-size:1rem;font-weight:900}.dd-matchup-team-brand span{color:#c8efff;font-size:.62rem;font-weight:800}
.dd-team-summary{display:flex;gap:8px}.dd-team-summary>div{min-width:100px;padding:7px 10px;border:1px solid rgba(39,199,255,.23);border-radius:7px;background:rgba(2,10,18,.58);text-align:center}.dd-team-summary b,.dd-team-summary span{display:block}.dd-team-summary b{color:var(--team-a);font-size:1.05rem;font-weight:900;text-shadow:0 0 10px color-mix(in srgb,var(--team-a) 50%,transparent)}.dd-team-summary span{color:#c8efff;font-size:.48rem;font-weight:800;text-transform:uppercase}
.dd-matchup-columns,.dd-matchup-player-row{display:grid;grid-template-columns:32px minmax(190px,1.55fr) minmax(135px,1.1fr) repeat(4,minmax(92px,.82fr)) minmax(74px,.65fr);align-items:center;gap:8px;padding:8px 11px}
.dd-matchup-columns{background:rgba(39,199,255,.055);border-bottom:1px solid rgba(39,199,255,.2);color:#9fe5ff;font-size:.49rem;font-weight:900;text-transform:uppercase}
.dd-matchup-player-row{border-bottom:1px solid rgba(87,141,176,.14);transition:.15s ease}.dd-matchup-player-row:hover{background:linear-gradient(90deg,color-mix(in srgb,var(--team-accent) 10%,transparent),rgba(255,77,242,.025))}
.dd-matchup-rank{display:flex;width:24px;height:24px;align-items:center;justify-content:center;border-radius:5px;background:var(--team-accent);color:#03101a;font-weight:900}
.dd-matchup-player{display:flex;align-items:center;gap:9px}.dd-matchup-player img{width:46px;height:46px;object-fit:contain}.dd-matchup-player b,.dd-matchup-player span,.dd-matchup-player small,.dd-matchup-pitcher b,.dd-matchup-pitcher span,.dd-matchup-price b,.dd-matchup-price span{display:block}.dd-matchup-player b{color:#fff;font-size:.72rem;font-weight:900}.dd-matchup-player span{color:#a8e8ff;font-size:.51rem;font-weight:800}.dd-matchup-player small{color:#dff6ff!important;font-size:.46rem;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;max-width:280px}.dd-matchup-pitcher b{color:#fff;font-size:.62rem;font-weight:900}.dd-matchup-pitcher span{color:#ffd83d;font-size:.49rem;font-weight:800}.dd-matchup-price{text-align:center}.dd-matchup-price b{color:#35f29a;font-size:.75rem;font-weight:900}.dd-matchup-price span{color:#bfe9ff;font-size:.46rem;font-weight:800}

/* Game simulation engine */
.dd-sim-matchup{display:grid;grid-template-columns:1fr minmax(220px,.55fr) 1fr;gap:13px;align-items:stretch;margin:10px 0 20px}
.dd-sim-team{position:relative;overflow:hidden;border:1px solid rgba(39,199,255,.34);border-radius:12px;padding:15px;background:linear-gradient(145deg,#081a2a,#040d16);box-shadow:inset 0 0 28px rgba(0,0,0,.36)}
.dd-sim-away{border-color:rgba(39,199,255,.48)}.dd-sim-home{border-color:rgba(255,77,242,.46)}
.dd-sim-team-head{display:flex;align-items:center;gap:12px}.dd-sim-team-head img{width:62px;height:62px;object-fit:contain}.dd-sim-team-head small,.dd-sim-team-head b,.dd-sim-team-head span{display:block}.dd-sim-team-head small{color:#ffd83d!important;font-size:.5rem;font-weight:900}.dd-sim-team-head b{color:#fff;font-size:1.1rem;font-weight:900}.dd-sim-team-head span{color:#c8efff;font-size:.58rem;font-weight:800}
.dd-sim-score{position:absolute;right:15px;top:14px;text-align:right}.dd-sim-score b,.dd-sim-score span{display:block}.dd-sim-score b{color:#fff;font-size:2rem;font-weight:900;text-shadow:0 0 13px rgba(39,199,255,.35)}.dd-sim-score span{color:#9fe5ff;font-size:.46rem;font-weight:900;text-transform:uppercase}
.dd-sim-win{margin:14px 0}.dd-sim-win-track{height:8px;border-radius:99px;background:#102839;overflow:hidden}.dd-sim-win-track i{display:block;height:100%;background:linear-gradient(90deg,#27c7ff,#ff4df2);box-shadow:0 0 12px #27c7ff}.dd-sim-win b{display:block;margin-top:4px;color:#fff;font-size:.58rem;font-weight:900;text-align:right}
.dd-sim-stat-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.dd-sim-stat-grid>div{padding:8px 5px;border:1px solid rgba(39,199,255,.17);border-radius:7px;background:rgba(2,9,16,.5);text-align:center}.dd-sim-stat-grid b,.dd-sim-stat-grid span{display:block}.dd-sim-stat-grid b{color:#35f29a;font-size:1rem;font-weight:900}.dd-sim-stat-grid>div:nth-child(2) b{color:#ff4df2}.dd-sim-stat-grid>div:nth-child(3) b{color:#ffd83d}.dd-sim-stat-grid>div:nth-child(4) b{color:#a85cff}.dd-sim-stat-grid span{color:#c8efff;font-size:.45rem;font-weight:800;text-transform:uppercase}.dd-sim-source{margin-top:8px;color:#bfe9ff;font-size:.47rem;font-weight:800;text-align:right}
.dd-sim-center{display:flex;flex-direction:column;align-items:center;justify-content:center;border:1px solid rgba(255,216,61,.35);border-radius:12px;background:radial-gradient(circle,rgba(255,216,61,.08),transparent 65%),#050e17;text-align:center}.dd-sim-center small,.dd-sim-center b,.dd-sim-center span{display:block}.dd-sim-center small{color:#ffd83d!important;font-weight:900}.dd-sim-center b{margin:6px 0;color:#fff;font-size:1.25rem;font-weight:900}.dd-sim-center span{color:#c8efff;font-size:.55rem;font-weight:800}

/* Parlay locks and blended tickets */
.dd-parlay-mode.v15{position:relative;min-height:86px;border-color:color-mix(in srgb,var(--accent) 50%,#24435a);background:radial-gradient(circle at 95% 0,color-mix(in srgb,var(--accent) 11%,transparent),transparent 50%),#07131f;box-shadow:0 0 15px color-mix(in srgb,var(--accent) 9%,transparent)}
.dd-parlay-mode.v15 b,.dd-parlay-mode.v15 span{display:block}.dd-parlay-mode.v15 b{color:var(--accent);font-size:.9rem;font-weight:900;text-shadow:0 0 9px color-mix(in srgb,var(--accent) 50%,transparent)}.dd-parlay-mode.v15 span{margin-top:5px;color:#d8f4ff;font-size:.58rem;font-weight:800;line-height:1.3}
.dd-inline-note,.dd-provider-line,.dd-disclaimer{color:#d9f5ff!important;font-weight:800!important}.dd-inline-note b{color:#ffd83d}.dd-provider-line{margin-top:8px;font-size:.68rem}.dd-disclaimer{border-color:rgba(255,216,61,.32)!important;background:rgba(31,24,6,.35)!important}
[data-testid="stCheckbox"] label p{color:#fff!important;font-weight:900!important}

/* Multicolor form and chart accents */
.stButton>button{font-weight:900!important;color:#fff!important;background:linear-gradient(135deg,#08243a,#121735)!important;border-color:#2e7eaa!important}
.stButton>button:hover{border-color:#ff4df2!important;box-shadow:0 0 15px rgba(255,77,242,.20),inset 0 0 13px rgba(39,199,255,.08)!important}
[data-testid="stVegaLiteChart"]{border-color:rgba(168,92,255,.38)!important;background:radial-gradient(circle at 100% 0,rgba(255,77,242,.055),transparent 32%),linear-gradient(180deg,#071521,#03101a)!important;box-shadow:inset 0 0 24px rgba(0,0,0,.34),0 0 24px rgba(168,92,255,.065)!important}

/* Readable information panels */
.dd-insight,.dd-empty,.stAlert{color:#eaf8ff!important;font-weight:700!important}.dd-insight li{color:#dff5ff!important;font-weight:700!important}.dd-insight strong{color:#fff!important;font-weight:900!important}

@media(max-width:1280px){
 .dd-picks-grid.v15{grid-template-columns:repeat(3,1fr)}
 .dd-pick-card.v15{height:265px}
 .dd-matchup-columns,.dd-matchup-player-row{grid-template-columns:30px minmax(180px,1.5fr) minmax(125px,1fr) repeat(4,minmax(82px,.8fr)) minmax(70px,.65fr);min-width:980px}
 .dd-matchup-team{overflow-x:auto}
}
@media(max-width:900px){
 .dd-picks-grid.v15{display:flex;overflow-x:auto;scroll-snap-type:x mandatory;padding-bottom:8px}
 .dd-pick-card-link{flex:0 0 250px;scroll-snap-align:start}
 .dd-sim-matchup{grid-template-columns:1fr}.dd-sim-center{min-height:110px;order:2}.dd-sim-home{order:3}
 .dd-matchup-team-head{align-items:flex-start;flex-direction:column}.dd-team-summary{width:100%}.dd-team-summary>div{flex:1}
}
@media(max-width:560px){
 .dd-pick-card-link{flex-basis:225px}.dd-pick-card.v15{height:268px}
 .dd-game-tab{flex-basis:145px}
 .dd-sim-stat-grid{grid-template-columns:repeat(2,1fr)}
 .dd-neon-grid{min-width:780px}
}

.dd-weather-setup{margin:12px 0;padding:16px 18px;border:1px solid rgba(255,216,61,.44);border-radius:10px;background:radial-gradient(circle at 100% 0,rgba(255,77,242,.07),transparent 45%),linear-gradient(135deg,rgba(39,29,5,.68),rgba(5,18,29,.96));box-shadow:0 0 20px rgba(255,216,61,.08)}.dd-weather-setup b,.dd-weather-setup span{display:block}.dd-weather-setup b{color:#ffd83d;font-size:.9rem;font-weight:900;text-shadow:0 0 10px rgba(255,216,61,.35)}.dd-weather-setup span{margin-top:6px;color:#e9f8ff;font-size:.72rem;font-weight:800;line-height:1.45}.dd-weather-setup code{color:#35f29a;background:#04130d;border:1px solid rgba(53,242,154,.25);padding:2px 5px;border-radius:4px}
</style>
''',
        unsafe_allow_html=True,
    )

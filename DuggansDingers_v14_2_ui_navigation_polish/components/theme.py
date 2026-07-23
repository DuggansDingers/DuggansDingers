from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,500;0,600;0,700;0,800;0,900;1,700;1,800;1,900&family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#020812;--panel:#07131f;--panel2:#0a1928;--line:#17354c;--line2:#0875c9;
  --text:#f6fbff;--muted:#91a6b9;--blue:#29a5ff;--cyan:#31c8ff;--green:#43ef6c;
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
[data-testid="stMetricLabel"]{color:#8fa7ba!important;font-size:.68rem!important;text-transform:uppercase!important;font-weight:800!important}
[data-testid="stMetricValue"]{color:#fff!important}
[data-testid="stDataFrame"]{border:1px solid #1c415d;border-radius:8px;overflow:hidden}
hr{border-color:#183248}

/* Home section heading */
.dd-home-section-title{display:flex;align-items:center;gap:10px;margin:3px 0 4px}
.dd-home-section-title>i{font-style:normal;color:#ffd000;font-size:1.35rem;filter:drop-shadow(0 0 7px #ffb800)}
.dd-home-section-title b{display:block;font-size:1rem;line-height:1.1;text-transform:uppercase;letter-spacing:.025em}
.dd-home-section-title span{display:block;color:#8095a8;font-size:.7rem;margin-top:2px}

/* Six compact player cards */
.dd-picks-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:10px;margin:0 0 12px}
.dd-pick-card{position:relative;height:160px;overflow:hidden;border:1px solid #1b3145;border-radius:8px;background:linear-gradient(145deg,#0a1928 0%,#07111c 60%,#08131f 100%);box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}
.dd-pick-rank{position:absolute;z-index:4;left:10px;top:9px;width:25px;height:25px;display:flex;align-items:center;justify-content:center;border-radius:4px;background:#286ea8;color:#fff;font-weight:900;font-size:.76rem;box-shadow:0 0 10px rgba(26,141,255,.25)}
.dd-pick-rank.rank-1{background:linear-gradient(135deg,#9c50ee,#6120bd)}
.dd-pick-photo{position:absolute;z-index:1;left:-2px;bottom:28px;width:112px;height:128px;object-fit:contain;object-position:center bottom;filter:drop-shadow(0 5px 7px rgba(0,0,0,.65))}
.dd-pick-copy{position:absolute;z-index:2;left:112px;right:7px;top:15px}
.dd-pick-name{min-height:42px;color:#fff;font-size:.92rem;font-weight:800;line-height:1.14}
.dd-pick-team{margin-top:3px;color:#9eb0c1;font-size:.67rem}
.dd-pick-prob{margin-top:8px;font-size:1.45rem;font-weight:900;line-height:1}
.dd-pick-label{margin-top:3px;color:#24a9ff;font-size:.58rem;font-weight:800;text-transform:uppercase}
.dd-pick-footer{position:absolute;z-index:3;left:0;right:0;bottom:0;height:29px;display:flex;align-items:center;justify-content:space-around;border-top:1px solid #1a2d3d;background:rgba(3,10,17,.88);color:#a9b7c4;font-size:.64rem;text-transform:uppercase}
.dd-pick-footer b{color:#fff;margin-right:4px}
.dd-pick-card:first-child .dd-pick-footer b{color:#b461ff}
.dd-pick-card:nth-child(5) .dd-pick-footer b{color:#42e875}

/* Weather panel */
.dd-weather-shell{margin:10px 0 12px;border:1px solid #123858;border-radius:9px;overflow:hidden;background:#06111b}
.dd-weather-heading{height:53px;display:flex;align-items:center;padding:9px 14px;border-bottom:1px solid #17364e;background:linear-gradient(90deg,#081a2a,#06131f)}
.dd-weather-heading>div{display:flex;align-items:center;gap:9px}
.dd-weather-heading b{display:block;text-transform:uppercase;font-size:1rem}
.dd-weather-heading small{display:block;margin-left:7px;color:#8297a8;font-size:.68rem;text-transform:none;font-weight:500}
.dd-weather-cloud{color:#31afff;font-size:1.45rem}
.dd-weather-layout{display:grid;grid-template-columns:29% 50.5% 20.5%;min-height:365px}
.dd-weather-summary,.dd-field-panel,.dd-forecast-panel{position:relative;padding:12px;border-right:1px solid #17364e;background:linear-gradient(180deg,#07141f,#05101a)}
.dd-forecast-panel{border-right:0}
.dd-stadium-row{display:flex;justify-content:space-between;align-items:center;padding:8px 10px;border:1px solid #18364d;border-radius:6px;background:#07131d}
.dd-stadium-row b{display:block;font-size:1.05rem;text-transform:uppercase}.dd-stadium-row span{display:block;color:#8195a7;font-size:.62rem;margin-top:2px}
.dd-stadium-row em{min-width:94px;padding:6px 8px;border:1px solid #24513b;border-radius:6px;background:#082014;color:#54f178;text-align:center;font-style:normal;font-weight:900;font-size:.78rem}.dd-stadium-row em small{display:block;color:#b3c1ca;font-size:.49rem;font-weight:500;margin-top:2px}.dd-stadium-row em.poor{color:#ff5a49;border-color:#6b2d2a;background:#25100f}.dd-stadium-row em.neutral{color:#ffd323;border-color:#6b5b1d;background:#201c0b}.dd-stadium-row em.unavailable{color:#9aabba;border-color:#384958;background:#101720}
.dd-big-temp{height:82px;display:flex;align-items:center;gap:28px;padding:5px 8px;border-bottom:1px solid #19364c}
.dd-big-temp>strong{font-family:'Barlow Condensed',sans-serif;font-size:3.15rem;line-height:1;color:#fff}
.dd-big-temp>div{display:grid;grid-template-columns:44px 1fr;align-items:center}.dd-big-temp i{grid-row:1/3;font-style:normal;font-size:2.3rem}.dd-big-temp b{font-size:.76rem}.dd-big-temp span{color:#8194a5;font-size:.59rem;margin-top:2px}
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
.dd-table-shell{overflow:auto;border:1px solid #1c4564;border-radius:8px}.dd-rank-table{width:100%;min-width:1050px;border-collapse:collapse;background:#06111b}.dd-rank-table th{padding:9px;background:#0a1928;color:#8fa8bb;font-size:.56rem;text-transform:uppercase}.dd-rank-table td{padding:8px;border-bottom:1px solid #152e42;color:#fff;font-size:.68rem}.dd-player-wrap,.dd-team-wrap{display:flex;align-items:center;gap:8px}.dd-player-wrap>img{width:40px;height:40px;object-fit:contain}.dd-team-wrap img{width:25px;height:25px}.dd-player-text strong,.dd-player-text span{display:block}.dd-player-text span{color:#8195a5;font-size:.55rem}.dd-rank-badge{display:inline-flex;width:24px;height:24px;align-items:center;justify-content:center;border-radius:5px;background:#1e5d91;font-weight:900}.dd-score-ring{font-weight:900}.dd-mini-stat small{margin-left:2px;color:#7890a3}.dd-num,.dd-odds{text-align:center}.dd-book-price{display:flex;flex-direction:column;align-items:center;color:#43ef6c}.dd-book-price small,.dd-book-price em{font-size:.47rem}.dd-spark{display:flex;align-items:flex-end;gap:2px;height:24px}.dd-spark i{display:block;width:3px;background:var(--spark)}.dd-trend-label{font-size:.48rem;text-align:center}
.dd-player-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.dd-player-card{position:relative;padding:12px;border:1px solid #1b4564;border-radius:9px;background:#07131f}.dd-player-card-score{position:absolute;right:12px;top:12px;color:var(--accent);font-size:1.5rem;font-weight:900}.dd-player-card-score small{display:block;color:#7f93a4;font-size:.48rem;text-transform:uppercase}.dd-player-card-head{display:flex;align-items:center;gap:10px}.dd-player-card-head>img{width:64px;height:64px;object-fit:contain}.dd-player-card-name{font-weight:900}.dd-player-card-team{display:flex;align-items:center;gap:5px;color:#8fa1b0;font-size:.59rem}.dd-player-card-team img{width:20px;height:20px}.dd-card-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:10px}.dd-card-stat{padding:7px;border:1px solid #173248;border-radius:5px;text-align:center}.dd-card-stat b,.dd-card-stat span{display:block}.dd-card-stat span{color:#8093a3;font-size:.48rem;text-transform:uppercase}.dd-card-footer{display:flex;justify-content:space-between;margin-top:9px;color:#8ea1b0;font-size:.55rem}.dd-risk-chip{padding:2px 6px;border:1px solid var(--accent);border-radius:99px;color:var(--accent)}
.dd-cheat-grid,.dd-weather-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:12px}.dd-cheat-card,.dd-weather-card{border:1px solid #1b4564;border-radius:9px;background:#07131f;overflow:hidden}.dd-cheat-head,.dd-weather-card-head{display:flex;justify-content:space-between;padding:12px;border-bottom:1px solid #173248}.dd-cheat-row{display:grid;grid-template-columns:32px minmax(130px,1.4fr) repeat(5,.65fr);align-items:center;gap:6px;padding:8px;border-bottom:1px solid #152e42}.dd-cheat-player{display:flex;align-items:center;gap:7px}.dd-cheat-player img{width:35px;height:35px;object-fit:contain}.dd-cheat-metric{text-align:center}.dd-cheat-metric b,.dd-cheat-metric span{display:block}.dd-cheat-metric span{font-size:.48rem;color:#8194a5}.dd-weather-grade{color:#43ef6c;font-weight:900}.dd-weather-metrics{display:grid;grid-template-columns:repeat(4,1fr)}.dd-weather-metrics>div{padding:9px;text-align:center;border-right:1px solid #173248}.dd-weather-metrics b,.dd-weather-metrics span{display:block}.dd-weather-metrics span{font-size:.48rem;color:#8194a5}
.dd-profile{position:relative;min-height:390px;overflow:hidden;border:1px solid #1c5a83;border-radius:10px;background:linear-gradient(90deg,rgba(3,12,20,.94),rgba(3,12,20,.36)),var(--profile-bg);background-size:cover}.dd-profile-inner{padding:32px}.dd-profile-copy{position:relative;z-index:2}.dd-player-name{font-family:'Barlow Condensed',sans-serif;font-size:3.2rem;font-weight:900;text-transform:uppercase}.dd-profile-score{font-size:2rem;color:#38b7ff;font-weight:900}.dd-profile-score small{display:block;color:#8ba0b0;font-size:.55rem;text-transform:uppercase}.dd-headshot{position:absolute;right:2%;bottom:0;height:88%;object-fit:contain}.dd-meter{height:7px;border-radius:99px;background:#132e42}.dd-meter span{display:block;height:100%;border-radius:99px;background:#2cafff}.dd-ribbon{display:flex;gap:7px;flex-wrap:wrap;margin-top:12px}.dd-ribbon span{padding:5px 8px;border:1px solid #1b5276;border-radius:99px;font-size:.56rem;text-transform:uppercase}
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
</style>
''',
        unsafe_allow_html=True,
    )

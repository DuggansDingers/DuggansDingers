from __future__ import annotations

import streamlit as st


def apply_theme() -> None:
    st.markdown(
        r'''
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:ital,wght@0,500;0,600;0,700;0,800;0,900;1,700;1,800;1,900&family=Inter:wght@400;500;600;700;800;900&display=swap');
:root{
  --bg:#01050d;--panel:#061426;--panel2:#0a2140;--line:#1b63a6;--line2:#35b8ff;
  --text:#ffffff;--muted:#c2d4e8;--blue:#178cff;--cyan:#43e7ff;--green:#4dff9b;
  --orange:#ff8a1f;--red:#ff334d;--purple:#b75cff;--gold:#ffd34a;--pink:#ff3be7;
  --glow-blue:0 0 12px rgba(40,183,255,.55),0 0 28px rgba(20,120,255,.28);
}
html,body,[class*="css"]{font-family:'Inter','Segoe UI',Arial,sans-serif;color:var(--text);font-size:16px;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
body,p,span,div,label,input,button,table{letter-spacing:.005em}

.stApp{
  background:
    radial-gradient(ellipse at 92% 4%,rgba(22,140,255,.34),transparent 28%),
    radial-gradient(ellipse at 12% 47%,rgba(255,53,45,.20),transparent 26%),
    radial-gradient(ellipse at 58% 100%,rgba(166,77,255,.13),transparent 33%),
    linear-gradient(180deg,#020611 0%,#031225 48%,#020a18 100%);
}
.stApp:before{content:'';position:fixed;inset:0;pointer-events:none;opacity:.22;background-image:linear-gradient(rgba(36,113,180,.07) 1px,transparent 1px),linear-gradient(90deg,rgba(36,113,180,.05) 1px,transparent 1px);background-size:34px 34px;mask-image:linear-gradient(to bottom,transparent,#000 30%,#000 80%,transparent)}
#MainMenu,footer{visibility:hidden}
header[data-testid="stHeader"]{visibility:visible;background:transparent!important;height:3rem;pointer-events:none}
header[data-testid="stHeader"] *{pointer-events:auto}
[data-testid="stSidebarCollapsedControl"],[data-testid="stSidebarCollapseButton"]{visibility:visible!important;display:flex!important;opacity:1!important;z-index:100000!important}
[data-testid="stSidebarCollapsedControl"] button,[data-testid="stSidebarCollapseButton"] button{background:linear-gradient(135deg,#0a84ff,#7a2cff)!important;border:1px solid #63d7ff!important;color:#fff!important;border-radius:999px!important;box-shadow:0 0 12px #19bfff,0 0 24px rgba(122,44,255,.7)!important}
[data-testid="stSidebarCollapsedControl"] button:hover,[data-testid="stSidebarCollapseButton"] button:hover{transform:scale(1.08);box-shadow:0 0 16px #49e6ff,0 0 32px rgba(255,39,214,.75)!important}

.block-container{max-width:1820px;padding:.62rem 1rem 2rem}
[data-testid="stSidebar"]{background:linear-gradient(180deg,#020812 0%,#071a32 100%)!important;border-right:1px solid #1e78c7;box-shadow:8px 0 28px rgba(0,107,255,.14);min-width:248px!important;max-width:248px!important}
[data-testid="stSidebar"] .block-container{padding:.35rem 0 1rem}
.dd-sidebar-logo{width:100%;max-height:250px;object-fit:contain;display:block;margin:-22px auto -16px;filter:drop-shadow(0 12px 25px rgba(255,78,0,.38))}
[data-testid="stSidebar"] [data-testid="stDateInput"]{padding:0 14px 10px}
[data-testid="stSidebar"] [data-testid="stDateInput"] label{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;letter-spacing:.08em;font-weight:800;color:#c4d5e8!important}
[data-testid="stSidebar"] .stButton{margin:0}
[data-testid="stSidebar"] .stButton>button{border:0;border-bottom:1px solid rgba(22,72,123,.38);border-radius:0;background:transparent;color:#f5fbff;justify-content:flex-start;padding:.73rem 1.05rem;min-height:44px;font-family:'Barlow Condensed',sans-serif;font-size:1.05rem;font-weight:800;letter-spacing:.025em;box-shadow:none;text-transform:uppercase}
[data-testid="stSidebar"] .stButton>button:hover{background:linear-gradient(90deg,rgba(20,129,255,.26),rgba(20,129,255,.03));color:#fff;transform:none}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{background:linear-gradient(90deg,#087cff 0%,#1747b8 62%,rgba(172,39,255,.14) 100%);border-left:4px solid #4ee6ff;color:#fff;text-shadow:0 0 8px rgba(255,255,255,.55);box-shadow:0 0 14px rgba(30,179,255,.65),inset 0 0 18px rgba(82,40,255,.25)}
.stButton>button{border:1px solid #1a4c7d;background:linear-gradient(180deg,#0a2441,#06182b);color:#edf6ff;border-radius:8px;font-weight:800;min-height:38px;transition:.16s ease}
.stButton>button:hover{border-color:#42abff;color:#fff;box-shadow:0 0 18px rgba(45,154,255,.22);transform:translateY(-1px)}
.stButton>button[kind="primary"]{background:linear-gradient(180deg,#0e76ed,#0758b8);border-color:#2d9cff;box-shadow:0 0 18px rgba(21,129,255,.22)}
[data-testid="stMetric"]{background:linear-gradient(180deg,#07192d,#05111e);border:1px solid #164778;border-radius:10px;padding:10px 13px;box-shadow:inset 0 1px 0 rgba(255,255,255,.025)}
[data-testid="stMetricLabel"]{color:#8fa6c1!important;font-family:'Barlow Condensed',sans-serif;font-weight:800;text-transform:uppercase;letter-spacing:.07em;font-size:.72rem!important}
[data-testid="stMetricValue"]{font-family:'Barlow Condensed',sans-serif;color:#fff!important;font-weight:800}
.stSelectbox label,.stMultiSelect label,.stSlider label,.stTextInput label,.stNumberInput label,.stToggle label{font-weight:800;color:#f2f7ff!important}
[data-baseweb="select"]>div,[data-testid="stTextInput"] input,[data-testid="stNumberInput"] input,[data-testid="stDateInput"] input{background:#06182b;border-color:#1a4b7d;color:#fff;border-radius:8px}
[data-testid="stDataFrame"]{border:1px solid #174b7d;border-radius:9px;overflow:hidden}
hr{border-color:#14385f}

.dd-side-meta{margin:13px 14px 0;padding:12px;border:1px solid #10365e;border-radius:8px;background:linear-gradient(180deg,#06172a,#030d19);box-shadow:0 0 16px rgba(17,109,194,.12)}
.dd-side-meta-label{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;color:#c5d7ea;font-size:.73rem;letter-spacing:.05em}.dd-side-meta-value{font-weight:800;font-size:.82rem;margin-top:2px}.dd-side-rule{height:1px;background:#12375d;margin:9px 0}.dd-live-line{margin-top:5px;color:#35e27e;font-size:.72rem;font-weight:800}.dd-live-dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#35e27e;box-shadow:0 0 10px #35e27e;margin-right:6px}.dd-side-counts{margin-top:7px;color:#c0d2e6;font-size:.69rem}

.dd-topbar{display:grid;grid-template-columns:1fr auto 1fr;align-items:center;gap:18px;min-height:98px;padding:0 4px 8px}
.dd-wordmark{grid-column:2;text-align:center;line-height:.9}
.dd-wordmark-main{font-family:'Barlow Condensed',sans-serif;font-size:clamp(2.7rem,4.25vw,4.8rem);font-weight:900;font-style:italic;letter-spacing:.012em;text-transform:uppercase;color:#fff;background:linear-gradient(180deg,#fff 0%,#f9f9f9 44%,#9fa7b0 100%);-webkit-background-clip:text;background-clip:text;-webkit-text-fill-color:transparent;filter:drop-shadow(0 5px 4px #000)}
.dd-wordmark-sub{font-family:'Barlow Condensed',sans-serif;margin-top:10px;font-size:1.08rem;font-weight:800;letter-spacing:.31em;color:#269fff;text-transform:uppercase}
.dd-wordmark-sub:before,.dd-wordmark-sub:after{content:'';display:inline-block;width:96px;height:1px;background:linear-gradient(90deg,transparent,#138aff);vertical-align:middle;margin:0 13px}.dd-wordmark-sub:after{background:linear-gradient(90deg,#138aff,transparent)}
.dd-top-actions{justify-self:end;display:flex;gap:10px}.dd-top-control{display:flex;align-items:center;gap:8px;border:1px solid #0d72cf;border-radius:8px;background:#041222;color:#fff;padding:10px 13px;font-weight:700;font-size:.82rem}

.dd-alert-ribbon{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:-3px 0 11px;padding:7px 11px;border:1px solid #143f6d;border-radius:7px;background:linear-gradient(90deg,rgba(9,50,91,.72),rgba(4,16,29,.78));font-size:.72rem;color:#9fb2c9}.dd-alert-ribbon strong{color:#fff}.dd-source-pills{display:flex;gap:6px;flex-wrap:wrap}.dd-source-pill{padding:3px 7px;border-radius:99px;border:1px solid #20588c;background:#071b2f;font-weight:800;text-transform:uppercase;font-size:.61rem}.dd-source-pill.live{color:#42e68a;border-color:#1f6f47}.dd-source-pill.pending{color:#ffbd2f;border-color:#735b1f}

.dd-feature-grid{display:grid;grid-template-columns:repeat(6,minmax(0,1fr));gap:12px;margin-top:3px}
.dd-feature-card{position:relative;overflow:hidden;min-height:348px;border:1px solid var(--accent);border-radius:8px;background:radial-gradient(circle at 50% 30%,color-mix(in srgb,var(--accent) 30%,transparent),transparent 37%),linear-gradient(180deg,rgba(10,25,47,.98),rgba(1,6,15,.99));box-shadow:0 0 12px color-mix(in srgb,var(--accent) 44%,transparent),0 0 30px color-mix(in srgb,var(--accent) 18%,transparent),inset 0 0 20px rgba(255,255,255,.025);transition:.18s ease}
.dd-feature-card:hover{transform:translateY(-4px);box-shadow:0 0 18px color-mix(in srgb,var(--accent) 70%,transparent),0 0 42px color-mix(in srgb,var(--accent) 34%,transparent)}
.dd-feature-title{position:relative;z-index:3;font-family:'Barlow Condensed',sans-serif;font-style:italic;text-transform:uppercase;text-align:center;font-size:1.38rem;font-weight:900;padding:10px 5px 4px;color:#fff;text-shadow:0 0 11px var(--accent)}
.dd-feature-brand{position:absolute;z-index:1;width:62%;left:19%;top:43px;opacity:.82;filter:drop-shadow(0 11px 12px rgba(0,0,0,.72))}
.dd-feature-player{position:absolute;z-index:2;width:45%;height:156px;object-fit:contain;right:-2%;top:83px;filter:drop-shadow(0 9px 8px #000)}
.dd-feature-shade{position:absolute;inset:0;z-index:2;background:linear-gradient(180deg,transparent 44%,rgba(0,0,0,.96) 72%);pointer-events:none}
.dd-feature-content{position:absolute;z-index:4;left:9px;right:9px;bottom:9px;text-align:center}
.dd-feature-name{font-family:'Barlow Condensed',sans-serif;font-size:1.18rem;line-height:1.05;text-transform:uppercase;font-weight:800;color:#fff}.dd-feature-meta{font-size:.78rem;color:#eef6ff;margin-top:3px}
.dd-feature-value{font-family:'Barlow Condensed',sans-serif;font-size:2.15rem;font-weight:900;color:var(--accent);margin-top:6px;line-height:1}.dd-feature-caption{font-family:'Barlow Condensed',sans-serif;font-size:.74rem;text-transform:uppercase;font-weight:800;color:var(--accent);margin-top:3px}
.dd-feature-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:3px;margin-top:8px;padding-top:7px;border-top:1px solid color-mix(in srgb,var(--accent) 35%,transparent)}.dd-feature-stat b{display:block;font-family:'Barlow Condensed',sans-serif;color:#fff;font-size:.83rem}.dd-feature-stat span{display:block;color:#d0dced;font-size:.62rem;text-transform:uppercase;font-weight:800}

.dd-sectionbar{display:flex;align-items:center;justify-content:space-between;gap:12px;margin:15px 0 8px;padding:8px 12px;border:1px solid #174e80;border-radius:7px;background:linear-gradient(180deg,#07192d,#040d18)}.dd-sectionbar-title{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;font-size:1.25rem;font-weight:800}.dd-sectionbar-title span{color:#ffc43a;margin-right:7px}.dd-sectionbar-sub{font-size:.7rem;color:#c4d7ea}
.dd-table-shell{border:1px solid #1d8ee7;border-radius:8px;overflow:hidden;background:#04101f;box-shadow:0 0 16px rgba(28,164,255,.35),0 0 34px rgba(111,46,255,.12)}
.dd-rank-table{width:100%;border-collapse:collapse;table-layout:fixed}.dd-rank-table th{padding:7px 6px;background:#030b15;color:#d7e7f8;border-bottom:1px solid #133d67;border-right:1px solid rgba(20,60,97,.45);font-family:'Barlow Condensed',sans-serif;font-size:.80rem;text-transform:uppercase;letter-spacing:.025em;text-align:center}.dd-rank-table td{padding:4px 6px;border-bottom:1px solid #102d4d;border-right:1px solid rgba(20,60,97,.42);height:57px;text-align:center;background:linear-gradient(180deg,#061423,#040f1c)}.dd-rank-table tbody tr:hover td{background:#08203a}
.dd-rank-badge{display:inline-grid;place-items:center;width:27px;height:27px;border-radius:5px;background:#0b2f5f;border:1px solid #1b5ca5;color:#dcecff;font-weight:900}.dd-rank-badge.gold{background:linear-gradient(180deg,#ffd34f,#eaa300);color:#161009;border-color:#ffda5e}.dd-rank-badge.silver{background:linear-gradient(180deg,#c9d7e6,#8298ad);color:#07101a}.dd-rank-badge.bronze{background:linear-gradient(180deg,#dc7f31,#824013);color:#fff}
.dd-player-wrap{display:flex;align-items:center;gap:8px;text-align:left}.dd-player-wrap img{width:48px;height:48px;object-fit:contain;align-self:end}.dd-player-text strong{display:block;font-size:.76rem;line-height:1.05}.dd-player-text span{display:block;color:#a7b6c8;font-size:.61rem;margin-top:2px}.dd-team-wrap{display:flex;align-items:center;justify-content:center;gap:6px}.dd-team-wrap img{width:30px;height:30px;object-fit:contain}.dd-team-wrap span{font-weight:700;font-size:.74rem}.dd-score-ring{font-family:'Barlow Condensed',sans-serif;font-size:1.48rem;font-weight:900;color:var(--score-color);text-shadow:0 0 10px color-mix(in srgb,var(--score-color) 42%,transparent)}.dd-num{font-family:'Barlow Condensed',sans-serif;font-size:.98rem;font-weight:800}.dd-odds{font-family:'Barlow Condensed',sans-serif;font-size:1rem;font-weight:900;color:#38e37e}.dd-mini-stat{font-family:'Barlow Condensed',sans-serif;font-size:.82rem;font-weight:800}.dd-mini-stat small{display:block;color:#7f94ab;font-size:.55rem;text-transform:uppercase}.dd-spark{height:30px;display:flex;align-items:flex-end;justify-content:center;gap:2px}.dd-spark i{display:block;width:5px;min-height:3px;border-radius:1px 1px 0 0;background:linear-gradient(180deg,var(--spark),color-mix(in srgb,var(--spark) 40%,#07111e));box-shadow:0 0 6px color-mix(in srgb,var(--spark) 30%,transparent)}.dd-trend-label{font-family:'Barlow Condensed',sans-serif;font-size:.65rem;font-weight:900;text-transform:uppercase}

.dd-bottom-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:8px;margin-top:0;padding:11px 16px;border:1px solid #174f83;border-top:0;border-radius:0 0 8px 8px;background:linear-gradient(180deg,#06182b,#030d18)}.dd-bottom-stat{display:flex;align-items:center;justify-content:center;gap:8px}.dd-bottom-icon{font-size:1.65rem;text-shadow:0 0 13px var(--accent)}.dd-bottom-label{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;color:var(--accent);font-size:.72rem;font-weight:800}.dd-bottom-value{font-family:'Barlow Condensed',sans-serif;color:#fff;font-size:1.18rem;font-weight:900}

.dd-hero{margin:6px 0 16px;padding:20px 22px;border:1px solid #154a7d;border-radius:10px;background:radial-gradient(circle at 85% 20%,rgba(23,129,255,.15),transparent 28%),linear-gradient(135deg,#07182b,#030b15);box-shadow:0 0 26px rgba(22,140,255,.12)}.dd-eyebrow{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;font-size:.72rem;letter-spacing:.17em;color:#2e9fff;font-weight:800}.dd-hero-title{font-family:'Barlow Condensed',sans-serif;text-transform:uppercase;font-style:italic;font-size:clamp(2.15rem,4vw,3.9rem);font-weight:900;line-height:.95;color:#fff}.dd-hero-title span{color:#2f9fff}.dd-hero-sub{margin-top:8px;color:#9db0c6;max-width:850px}

.dd-player-grid{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:12px}.dd-player-card{position:relative;overflow:hidden;border:1px solid var(--accent);border-radius:10px;background:radial-gradient(circle at 85% 15%,color-mix(in srgb,var(--accent) 15%,transparent),transparent 35%),linear-gradient(155deg,#081a2e,#030b15);min-height:248px;padding:13px;box-shadow:0 0 17px color-mix(in srgb,var(--accent) 12%,transparent)}.dd-player-card-head{display:flex;align-items:center;gap:10px}.dd-player-card-head img{width:76px;height:76px;object-fit:contain}.dd-player-card-name{font-family:'Barlow Condensed',sans-serif;font-size:1.38rem;font-weight:900;text-transform:uppercase;line-height:1}.dd-player-card-team{display:flex;align-items:center;gap:5px;margin-top:5px;color:#9db0c6;font-size:.72rem}.dd-player-card-team img{width:24px;height:24px}.dd-player-card-score{position:absolute;right:11px;top:12px;font-family:'Barlow Condensed',sans-serif;font-size:1.85rem;font-weight:900;color:var(--accent)}.dd-player-card-score small{display:block;font-family:'Inter',sans-serif;font-size:.49rem;color:#c4d5e8;text-transform:uppercase;text-align:right}.dd-card-stats{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-top:11px}.dd-card-stat{padding:6px 4px;border:1px solid #123a62;border-radius:6px;background:#04111f;text-align:center}.dd-card-stat b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:1rem}.dd-card-stat span{display:block;font-size:.53rem;text-transform:uppercase;color:#8196ad;font-weight:800}.dd-card-footer{display:flex;justify-content:space-between;gap:7px;align-items:center;margin-top:10px;padding-top:8px;border-top:1px solid #12395f;font-size:.66rem;color:#90a6bd}.dd-risk-chip{padding:3px 7px;border:1px solid var(--accent);border-radius:99px;color:var(--accent);font-weight:900;text-transform:uppercase}

.dd-cheat-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:14px}.dd-cheat-card{border:1px solid var(--team-a);border-radius:10px;overflow:hidden;background:linear-gradient(150deg,color-mix(in srgb,var(--team-a) 24%,#061323),#020a13 65%);box-shadow:0 0 20px color-mix(in srgb,var(--team-a) 18%,transparent)}.dd-cheat-head{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:11px 13px;border-bottom:1px solid color-mix(in srgb,var(--team-a) 50%,#14395f)}.dd-cheat-team{display:flex;align-items:center;gap:10px}.dd-cheat-team img{width:47px;height:47px;object-fit:contain}.dd-cheat-team b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:1.45rem;text-transform:uppercase}.dd-cheat-team span{font-size:.66rem;color:#9aadc2}.dd-cheat-date{text-align:right;font-family:'Barlow Condensed',sans-serif;font-weight:800;color:var(--team-b)}.dd-cheat-list{padding:5px 11px 10px}.dd-cheat-row{display:grid;grid-template-columns:28px minmax(150px,1.7fr) repeat(5,.65fr);align-items:center;gap:6px;padding:6px 3px;border-bottom:1px solid rgba(35,83,125,.45)}.dd-cheat-row:last-child{border-bottom:0}.dd-cheat-rank{display:grid;place-items:center;width:23px;height:23px;border-radius:5px;background:var(--team-b);color:#06101c;font-weight:900}.dd-cheat-player{display:flex;align-items:center;gap:6px}.dd-cheat-player img{width:38px;height:38px;object-fit:contain}.dd-cheat-player b{font-size:.71rem}.dd-cheat-player span{display:block;color:#8196ac;font-size:.57rem}.dd-cheat-metric{text-align:center;font-family:'Barlow Condensed',sans-serif;font-size:.83rem;font-weight:800}.dd-cheat-metric small{display:block;font-family:'Inter',sans-serif;color:#8296ac;font-size:.48rem;text-transform:uppercase}

.dd-profile{position:relative;overflow:hidden;min-height:360px;border:1px solid #1a609c;border-radius:12px;background-image:linear-gradient(90deg,rgba(1,6,13,.97) 0%,rgba(1,6,13,.82) 46%,rgba(1,6,13,.20) 100%),var(--profile-bg);background-size:cover;background-position:center;box-shadow:0 0 32px rgba(21,130,227,.18)}.dd-profile-inner{position:relative;z-index:2;padding:34px}.dd-player-name{font-family:'Barlow Condensed',sans-serif;font-size:clamp(2.8rem,5vw,5.5rem);font-weight:900;font-style:italic;text-transform:uppercase;line-height:.9}.dd-profile-score{font-family:'Barlow Condensed',sans-serif;font-size:4rem;color:#38c7ff;font-weight:900;margin-top:18px;line-height:.85}.dd-profile-score small{display:block;font-family:'Inter',sans-serif;font-size:.62rem;color:#d0deed;text-transform:uppercase;letter-spacing:.14em;margin-top:7px}.dd-meter{height:8px;border-radius:99px;background:#071522;overflow:hidden}.dd-meter span{display:block;height:100%;background:linear-gradient(90deg,#1d86ff,#35e27e);box-shadow:0 0 13px #31a9ff}.dd-ribbon{display:flex;gap:7px;flex-wrap:wrap;margin-top:15px}.dd-ribbon span{padding:5px 9px;border:1px solid #20578a;border-radius:99px;background:rgba(3,14,26,.75);font-size:.65rem;font-weight:900}.dd-headshot{position:absolute;z-index:1;right:4%;bottom:-2px;height:95%;object-fit:contain;filter:drop-shadow(0 15px 18px #000)}
.dd-insight{padding:15px;border:1px solid #174b7d;border-radius:9px;background:linear-gradient(145deg,#071b30,#04101d);color:#aebfd2}.dd-insight strong{font-family:'Barlow Condensed',sans-serif;color:#fff;font-size:1.35rem;text-transform:uppercase}.dd-insight li{margin:8px 0}

.dd-parlay-mode{border:1px solid var(--accent);border-radius:10px;padding:12px;background:radial-gradient(circle at 90% 10%,color-mix(in srgb,var(--accent) 16%,transparent),transparent 35%),linear-gradient(145deg,#07192d,#030b15);min-height:118px}.dd-parlay-mode b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:1.35rem;color:var(--accent);text-transform:uppercase}.dd-parlay-mode span{display:block;color:#d1dfef;font-size:.72rem;margin-top:5px}.dd-parlay-ticket{border:1px solid var(--accent);border-radius:12px;overflow:hidden;background:linear-gradient(160deg,#071a2f,#020811);box-shadow:0 0 28px color-mix(in srgb,var(--accent) 18%,transparent)}.dd-ticket-head{display:flex;justify-content:space-between;gap:12px;padding:14px 16px;background:linear-gradient(90deg,color-mix(in srgb,var(--accent) 22%,#071427),#071427);border-bottom:1px dashed color-mix(in srgb,var(--accent) 60%,#234)}.dd-ticket-head b{font-family:'Barlow Condensed',sans-serif;font-size:1.5rem;text-transform:uppercase;color:var(--accent)}.dd-ticket-leg{display:grid;grid-template-columns:42px minmax(180px,1.6fr) repeat(4,.7fr);align-items:center;gap:8px;padding:8px 14px;border-bottom:1px solid #12385f}.dd-ticket-leg img{width:40px;height:40px;object-fit:contain}.dd-ticket-player b{display:block;font-size:.76rem}.dd-ticket-player span{display:block;color:#8499af;font-size:.61rem}.dd-ticket-metric{text-align:center;font-family:'Barlow Condensed',sans-serif;font-weight:800}.dd-ticket-metric small{display:block;font-family:'Inter',sans-serif;color:#8195ab;font-size:.5rem;text-transform:uppercase}.dd-ticket-summary{display:grid;grid-template-columns:repeat(5,1fr);gap:6px;padding:12px}.dd-ticket-summary>div{text-align:center;padding:8px;border:1px solid #123b65;border-radius:7px;background:#04111f}.dd-ticket-summary b{display:block;font-family:'Barlow Condensed',sans-serif;font-size:1.18rem;color:var(--accent)}.dd-ticket-summary span{font-size:.52rem;text-transform:uppercase;color:#8195ac;font-weight:800}
.dd-disclaimer{margin-top:10px;padding:9px 11px;border-left:3px solid #ffbd2f;background:#151205;color:#d4c47a;font-size:.68rem}

.dd-empty{padding:26px;border:1px dashed #245987;border-radius:9px;text-align:center;color:#88a0ba;background:#05111f}

@media (max-width:1450px){.dd-feature-grid{grid-template-columns:repeat(3,1fr)}.dd-player-grid{grid-template-columns:repeat(3,1fr)}.dd-feature-card{min-height:330px}}
@media (max-width:1050px){.dd-topbar{grid-template-columns:1fr}.dd-wordmark{grid-column:1}.dd-top-actions{justify-self:center}.dd-cheat-grid{grid-template-columns:1fr}.dd-player-grid{grid-template-columns:repeat(2,1fr)}.dd-rank-table th:nth-child(n+9),.dd-rank-table td:nth-child(n+9){display:none}.dd-bottom-strip{grid-template-columns:repeat(3,1fr)}}
@media (max-width:760px){.block-container{padding:.5rem}.dd-feature-grid{grid-template-columns:1fr}.dd-player-grid{grid-template-columns:1fr}.dd-bottom-strip{grid-template-columns:1fr}.dd-wordmark-sub:before,.dd-wordmark-sub:after{width:35px}.dd-profile{min-height:450px}.dd-profile-inner{padding:22px}.dd-headshot{height:58%;right:-8%}.dd-cheat-row{grid-template-columns:28px minmax(130px,1.5fr) repeat(3,.6fr)}.dd-cheat-row>*:nth-child(n+6){display:none}.dd-ticket-leg{grid-template-columns:40px minmax(150px,1.5fr) repeat(2,.7fr)}.dd-ticket-leg>*:nth-child(n+5){display:none}.dd-ticket-summary{grid-template-columns:repeat(2,1fr)}}

/* v9 neon readability pass — layout intentionally unchanged */
.dd-wordmark-main{text-shadow:0 0 9px rgba(255,255,255,.40),0 0 24px rgba(69,182,255,.28)}
.dd-wordmark-sub{color:#4dc8ff;text-shadow:0 0 10px #168cff,0 0 22px rgba(166,77,255,.55)}
.dd-alert-ribbon{color:#d7e4f2;border-color:#267cc5;box-shadow:0 0 18px rgba(30,142,255,.16)}
.dd-sectionbar{border-color:#238fe4;background:linear-gradient(180deg,#0b2442,#061426);box-shadow:0 0 16px rgba(31,156,255,.20)}
.dd-sectionbar-title{color:#fff;text-shadow:0 0 8px rgba(255,255,255,.18)}
.dd-rank-table td{color:#f7fbff;font-size:.82rem}
.dd-rank-table tbody tr:hover{background:linear-gradient(90deg,rgba(17,130,255,.20),rgba(168,50,255,.10))}
.dd-rank-table th{background:linear-gradient(180deg,#07172a,#030c18)}
.dd-feature-caption,.dd-feature-value{text-shadow:0 0 10px var(--accent),0 0 22px color-mix(in srgb,var(--accent) 55%,transparent)}
.dd-feature-title{letter-spacing:.02em}
.dd-side-meta{border-color:#2277bd;background:linear-gradient(180deg,#0a203b,#061324);box-shadow:0 0 18px rgba(25,145,255,.18)}
.dd-live-line{color:#64ffad;text-shadow:0 0 10px rgba(53,255,140,.7)}
.dd-profile{border-color:#32b7ff;box-shadow:0 0 20px rgba(41,193,255,.36),0 0 45px rgba(125,45,255,.12)}
.dd-insight{color:#d7e3f0;border-color:#277cc4}
[data-testid="stMetric"]{border-color:#277fca;background:linear-gradient(180deg,#0b2442,#061426);box-shadow:0 0 14px rgba(31,160,255,.18)}
[data-testid="stMetricLabel"]{color:#d3e2f2!important;font-size:.78rem!important}
[data-testid="stMetricValue"]{text-shadow:0 0 10px rgba(60,190,255,.25)}
/* Keep the sidebar reopen control above the app when collapsed. */
[data-testid="stSidebarCollapsedControl"]{position:fixed!important;top:.55rem!important;left:.55rem!important}

/* v10 live weather module */
.dd-weather-line{display:flex;align-items:center;justify-content:space-between;gap:14px;margin:8px 0 12px;padding:9px 12px;border:1px solid var(--weather);border-radius:8px;background:linear-gradient(90deg,color-mix(in srgb,var(--weather) 18%,#061426),#04101d);box-shadow:0 0 18px color-mix(in srgb,var(--weather) 22%,transparent)}
.dd-weather-line b{color:var(--weather);font-family:'Barlow Condensed',sans-serif;font-size:1rem;text-transform:uppercase;text-shadow:0 0 10px var(--weather)}
.dd-weather-line span{color:#d5e4f3;font-size:.72rem;text-align:right}

/* v11 sportsbook odds module */
.dd-book-price{display:inline-flex;flex-direction:column;align-items:center;line-height:1.02;color:#64ffad;text-shadow:0 0 10px rgba(53,226,126,.45)}
.dd-book-price small{font-family:'Inter',sans-serif;font-size:.48rem;color:#d6e6f5;text-transform:uppercase;margin-top:2px}
.dd-book-price em{font-family:'Inter',sans-serif;font-style:normal;font-size:.46rem;margin-top:2px;text-transform:uppercase}
.dd-odds-upload{padding:14px;border:1px solid #2a91e6;border-radius:10px;background:linear-gradient(145deg,#08203a,#04111f);box-shadow:0 0 22px rgba(40,156,255,.16)}
.dd-edge-positive{color:#64ffad!important;text-shadow:0 0 10px rgba(53,226,126,.42)}
.dd-edge-negative{color:#ff7b7b!important}


/* v12.5 readability and spacing pass */
html,body,[class*="css"]{font-family:'Inter','Segoe UI',Arial,sans-serif;font-size:16px;line-height:1.48;letter-spacing:0}
p,span,div,label,input,button,table{letter-spacing:0}
.stApp{background:linear-gradient(180deg,#020711 0%,#061426 52%,#020a15 100%)}
.stApp:before{opacity:.10}
.block-container{padding:.85rem 1.25rem 2.5rem}

/* Make sections feel distinct instead of visually blending together. */
.dd-alert-ribbon,.dd-weather-line,[data-testid="stMetric"],.dd-sectionbar,.dd-side-meta,.dd-insight,.dd-parlay-mode,.dd-odds-upload{
  background:#07182b!important;
  border-color:#245b8d!important;
  box-shadow:0 6px 18px rgba(0,0,0,.22)!important;
}
.dd-alert-ribbon,.dd-weather-line{margin-bottom:16px}
.dd-feature-grid{gap:16px;margin:8px 0 18px}
.dd-feature-card{min-height:326px;background:linear-gradient(180deg,#0a1d32 0%,#040b14 100%);box-shadow:0 8px 20px rgba(0,0,0,.35)}
.dd-feature-card:hover{transform:translateY(-2px);box-shadow:0 10px 24px rgba(0,0,0,.42)}
.dd-feature-title,.dd-feature-name,.dd-feature-value,.dd-sectionbar-title,.dd-player-card-name{
  font-family:'Inter','Segoe UI',Arial,sans-serif;
  font-style:normal;
  letter-spacing:.01em;
}
.dd-feature-title{font-size:1.05rem;font-weight:800;padding-top:13px;text-shadow:none}
.dd-feature-name{font-size:1rem;font-weight:800;text-transform:none}
.dd-feature-meta,.dd-feature-caption{color:#b8c8da;line-height:1.35}
.dd-feature-value{font-size:1.85rem;text-shadow:none}
.dd-feature-caption{font-family:'Inter',sans-serif;text-shadow:none}
.dd-feature-stats{border-top:1px solid #244866;padding-top:9px;margin-top:9px}

/* Smaller dashboard headshots so the data remains the focus. */
.dd-feature-player{width:34%;height:126px;right:2%;top:88px}
.dd-player-wrap>img{width:38px!important;height:38px!important}
.dd-player-card-head>img{width:58px!important;height:58px!important}
.dd-rank-table td{padding-top:10px!important;padding-bottom:10px!important}
.dd-rank-table tbody tr{border-bottom:1px solid #183b5c}
.dd-rank-table tbody tr:nth-child(even){background:rgba(11,34,56,.42)}

/* Cleaner typography and calmer emphasis. */
.dd-wordmark-main{filter:none;text-shadow:none}
.dd-wordmark-sub{letter-spacing:.20em;text-shadow:none}
[data-testid="stMetricLabel"]{font-family:'Inter',sans-serif;font-size:.70rem!important;letter-spacing:.04em}
[data-testid="stMetricValue"]{font-family:'Inter',sans-serif;text-shadow:none}
.stButton>button,[data-testid="stSidebar"] .stButton>button{font-family:'Inter',sans-serif;letter-spacing:.01em}
.dd-side-meta-label,.dd-weather-line b{font-family:'Inter',sans-serif;letter-spacing:.03em}

/* More breathing room between Streamlit blocks. */
[data-testid="stVerticalBlock"]{gap:.85rem}
[data-testid="stHorizontalBlock"]{gap:1rem}

@media (max-width:760px){
  .block-container{padding:.65rem}
  .dd-feature-card{min-height:305px}
  .dd-feature-player{width:31%;height:112px;right:3%;top:82px}
}


/* v12.6 brighter pro broadcast redesign */
html,body,[class*="css"]{font-size:17.5px!important;line-height:1.55!important}
.stApp{
  background:
    radial-gradient(circle at 82% 5%,rgba(38,166,255,.30),transparent 28%),
    radial-gradient(circle at 15% 72%,rgba(70,88,255,.18),transparent 32%),
    linear-gradient(135deg,#0b1e35 0%,#12345a 42%,#071a31 100%)!important;
}
.stApp:before{opacity:.18!important;background-size:42px 42px!important}
.block-container{padding:1.05rem 1.5rem 3rem!important}
[data-testid="stSidebar"]{
  background:linear-gradient(180deg,#102c4d 0%,#071b31 58%,#061523 100%)!important;
  border-right:1px solid rgba(97,192,255,.72)!important;
  box-shadow:12px 0 34px rgba(0,0,0,.30)!important;
  min-width:276px!important;max-width:276px!important;
}
.dd-sidebar-logo{max-height:190px!important;margin:-10px auto -2px!important;filter:drop-shadow(0 8px 18px rgba(0,0,0,.35))!important}
.dd-nav-kicker{margin:0 17px;color:#5fd6ff;font-size:.70rem;font-weight:900;letter-spacing:.18em;text-transform:uppercase}
.dd-nav-title{margin:2px 17px 0;font-size:1.42rem;font-weight:900;color:#fff}
.dd-nav-sub{margin:0 17px 14px;color:#a9c7df;font-size:.76rem}
.dd-nav-section{margin:10px 14px 6px;padding:7px 8px;border-top:1px solid rgba(112,188,242,.25);color:#7ddcff;font-size:.67rem;font-weight:900;letter-spacing:.14em;text-transform:uppercase}
.dd-nav-section-bottom{margin-top:16px}
[data-testid="stSidebar"] [data-testid="stDateInput"]{padding:0 16px 8px!important}
[data-testid="stSidebar"] .stButton>button{
  margin:3px 11px!important;width:calc(100% - 22px)!important;border:1px solid transparent!important;border-radius:10px!important;
  background:rgba(7,27,49,.72)!important;padding:.78rem .95rem!important;min-height:48px!important;font-size:.92rem!important;
  box-shadow:inset 0 1px 0 rgba(255,255,255,.025)!important;
}
[data-testid="stSidebar"] .stButton>button:hover{background:rgba(26,83,132,.72)!important;border-color:rgba(87,184,255,.42)!important}
[data-testid="stSidebar"] .stButton>button[kind="primary"]{
  background:linear-gradient(90deg,#1596f2,#3157d5)!important;border-color:#70d9ff!important;border-left:4px solid #8beaff!important;
  box-shadow:0 8px 18px rgba(8,94,190,.30)!important;
}
.dd-side-meta{margin:14px 14px 4px!important;padding:14px!important;border-radius:12px!important;background:rgba(9,35,62,.95)!important}
.dd-side-meta-value{font-size:.94rem!important}.dd-side-counts,.dd-live-line{font-size:.76rem!important}
.dd-alert-ribbon,.dd-weather-line,[data-testid="stMetric"],.dd-sectionbar,.dd-side-meta,.dd-insight,.dd-parlay-mode,.dd-odds-upload{
  background:rgba(13,42,70,.96)!important;border-color:rgba(91,174,235,.52)!important;box-shadow:0 9px 24px rgba(0,0,0,.24)!important;
}
[data-testid="stMetric"]{padding:14px 16px!important;border-radius:12px!important}
[data-testid="stMetricLabel"]{font-size:.77rem!important;color:#c7dff2!important}
[data-testid="stMetricValue"]{font-size:1.75rem!important}
.dd-sectionbar{padding:12px 15px!important;margin-top:18px!important;border-radius:11px!important}
.dd-sectionbar-title{font-size:1.15rem!important}.dd-sectionbar-sub{font-size:.75rem!important}
.dd-feature-card{background:linear-gradient(180deg,rgba(20,61,98,.98),rgba(6,20,35,.98))!important;border-color:rgba(94,181,242,.48)!important}
.dd-feature-title{font-size:1.12rem!important}.dd-feature-name{font-size:1.08rem!important}.dd-feature-meta{font-size:.76rem!important}.dd-feature-value{font-size:2rem!important}
.dd-feature-player{width:29%!important;height:108px!important;right:4%!important;top:92px!important}
.dd-player-wrap>img{width:34px!important;height:34px!important}.dd-player-card-head>img{width:50px!important;height:50px!important}
.dd-rank-table{font-size:.90rem!important}.dd-rank-table th{font-size:.72rem!important}.dd-rank-table td{padding:12px 9px!important}
.dd-table-shell{border:1px solid rgba(92,178,239,.45)!important;border-radius:12px!important;box-shadow:0 10px 25px rgba(0,0,0,.22)!important}
.stButton>button{font-size:.94rem!important;min-height:44px!important}
.stSelectbox label,.stMultiSelect label,.stSlider label,.stTextInput label,.stNumberInput label,.stToggle label{font-size:.92rem!important}
@media (max-width:760px){html,body,[class*="css"]{font-size:16.5px!important}.block-container{padding:.7rem!important}.dd-feature-player{width:27%!important;height:98px!important}}


/* v13 responsive desktop + mobile shell */
[data-testid="stSidebar"],[data-testid="stSidebarCollapsedControl"],[data-testid="stSidebarCollapseButton"]{display:none!important}
.block-container{max-width:1600px!important;padding:.7rem 1rem 3rem!important}
.dd-app-header{display:flex;align-items:center;justify-content:space-between;gap:18px;padding:5px 4px 8px;border-bottom:1px solid rgba(73,171,235,.24)}
.dd-top-logo{width:230px;max-height:92px;object-fit:contain;object-position:left center;filter:drop-shadow(0 8px 16px rgba(0,0,0,.35))}
.dd-logo-text{font-family:Impact,'Arial Black',sans-serif;font-style:italic;font-size:2.1rem;color:#fff}.dd-logo-text span{color:#51b8ff}
.dd-header-status{font-size:.76rem;color:#b9cbe0;white-space:nowrap}.dd-live-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:#43ff95;box-shadow:0 0 12px #43ff95;margin-right:7px}
[data-testid="stSegmentedControl"]{margin:7px 0 8px;overflow-x:auto;scrollbar-width:none}
[data-testid="stSegmentedControl"]>div{display:flex;min-width:max-content;background:#061527;border:1px solid #1d527e;border-radius:14px;padding:4px}
[data-testid="stSegmentedControl"] button{min-height:42px!important;border-radius:10px!important;font-weight:800!important;white-space:nowrap}
.dd-updated{height:42px;padding:4px 10px;border:1px solid #23577e;border-radius:10px;background:#07182a;color:#9fb8cc;font-size:.62rem;line-height:1.1}.dd-updated b{color:#fff;font-size:.72rem}
.dd-feature-grid{grid-template-columns:repeat(6,minmax(0,1fr))!important;gap:10px!important}
.dd-feature-card{min-height:242px!important;overflow:hidden!important;border-radius:13px!important}
.dd-feature-brand{display:none!important}
.dd-feature-player{width:68%!important;height:150px!important;right:-3%!important;top:34px!important;object-fit:contain!important;object-position:center bottom!important}
.dd-feature-shade{background:linear-gradient(90deg,rgba(3,11,20,.96) 0%,rgba(3,11,20,.70) 48%,rgba(3,11,20,.10) 78%),linear-gradient(0deg,#030b14 0%,transparent 54%)!important}
.dd-feature-content{position:relative!important;z-index:3!important;padding-top:70px!important;max-width:68%!important}
.dd-feature-name{font-size:.92rem!important;line-height:1.05!important}.dd-feature-meta{font-size:.62rem!important}.dd-feature-value{font-size:1.45rem!important}.dd-feature-caption{font-size:.56rem!important}
.dd-feature-stats{grid-template-columns:repeat(2,1fr)!important;gap:3px!important}.dd-feature-stat:nth-child(n+3){display:none}
.dd-rank-table{min-width:1080px!important}.dd-table-shell{overflow-x:auto!important;-webkit-overflow-scrolling:touch}
.dd-cheat-grid{display:grid!important;grid-template-columns:repeat(2,minmax(0,1fr))!important;gap:14px!important}
@media(max-width:900px){
  .dd-top-logo{width:190px}.dd-header-status{display:none}
  .dd-feature-grid{display:flex!important;overflow-x:auto!important;scroll-snap-type:x mandatory;padding-bottom:8px}
  .dd-feature-card{flex:0 0 215px!important;scroll-snap-align:start}
  .dd-cheat-grid{grid-template-columns:1fr!important}
  [data-testid="stHorizontalBlock"]{flex-wrap:wrap!important}
  [data-testid="column"]{min-width:calc(50% - .5rem)!important;flex:1 1 calc(50% - .5rem)!important}
}
@media(max-width:600px){
  html,body,[class*="css"]{font-size:15px!important}
  .block-container{padding:.45rem .65rem 5rem!important}
  .dd-app-header{padding-top:2px}.dd-top-logo{width:168px;max-height:70px}
  [data-testid="stSegmentedControl"]{position:sticky;top:0;z-index:999;background:#04101d;padding:4px 0}
  [data-testid="stHorizontalBlock"]{gap:.55rem!important}
  [data-testid="column"]{min-width:100%!important;flex:1 1 100%!important}
  .dd-feature-card{flex-basis:205px!important;min-height:235px!important}
  .dd-feature-player{height:140px!important}
  .dd-sectionbar-title{font-size:1rem!important}.dd-sectionbar-sub{font-size:.65rem!important}
  .dd-rank-table{min-width:940px!important;font-size:.78rem!important}
}

</style>
''',
        unsafe_allow_html=True,
    )

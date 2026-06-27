#!/usr/bin/env python3
"""
Demon-Slayer / wisteria-garden anime panels for Dearie Eburu's profile README.

Same trick as the F1 build: GitHub strips <script> + inline style=, but renders
<img>-embedded SVG. The SVG carries its own <style>, gradients and CSS keyframe
animation (falling sakura, swaying wisteria, flickering flame, EQ bars), all
rendered client-side — so the "real website" look survives the sanitizer.

Run:  python build_svgs.py
"""
import pathlib, base64, datetime, os, json, urllib.request

ROOT = pathlib.Path(__file__).parent
ASSETS = ROOT / "assets"

# ---- palette (from the design's CSS vars) ----------------------------------
INK="#0c0a0d"; PANEL="#15111a"; PANEL2="#1d1622"; BORDER="#2f2636"
TEXT="#f1eaef"; MUT="#a99fb0"; ROSE="#f48fb1"; ROSED="#d76a93"
WIS="#b69ce0"; EMBER="#e8a86a"; BAMBOO="#8fc07a"; GOLD="#d9b86a"
SERIF="'Yu Mincho','Hiragino Mincho ProN','Zen Old Mincho','Songti SC',serif"
SANS="'Yu Gothic','Hiragino Kaku Gothic ProN','Zen Kaku Gothic New',system-ui,sans-serif"
MONO="'Cascadia Code','Consolas','SFMono-Regular',ui-monospace,monospace"

def esc(s):
    return s.replace("&","&amp;").replace("<","&lt;").replace(">","&gt;")

def b64(name):
    return base64.b64encode((ASSETS/name).read_bytes()).decode()

def write(name, svg):
    (ASSETS/name).write_text(svg, encoding="utf-8")
    print(f"  wrote assets/{name}  ({len(svg)//1024 or 1}kb)")

# ---- shared bits ------------------------------------------------------------
def base_defs(extra=""):
    return f"""<defs>
  <linearGradient id="title" x1="0" y1="0" x2="1" y2="0.4">
    <stop offset="0" stop-color="{TEXT}"/><stop offset="0.45" stop-color="{ROSE}"/>
    <stop offset="0.72" stop-color="{ROSED}"/><stop offset="1" stop-color="{EMBER}"/>
  </linearGradient>
  <linearGradient id="rosefade" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{ROSE}" stop-opacity="0"/><stop offset="1" stop-color="{ROSE}"/>
  </linearGradient>
  <linearGradient id="petal" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="#fcdfe8"/><stop offset="1" stop-color="{ROSE}"/>
  </linearGradient>
  <linearGradient id="petal2" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0" stop-color="{ROSE}"/><stop offset="1" stop-color="{ROSED}"/>
  </linearGradient>
  <radialGradient id="glowR" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{ROSE}" stop-opacity="0.18"/><stop offset="1" stop-color="{ROSE}" stop-opacity="0"/>
  </radialGradient>
  <radialGradient id="glowW" cx="0.5" cy="0.5" r="0.5">
    <stop offset="0" stop-color="{WIS}" stop-opacity="0.16"/><stop offset="1" stop-color="{WIS}" stop-opacity="0"/>
  </radialGradient>
  {extra}
</defs>"""

def panel_bg(x,y,w,h,rx=18,fill=PANEL,stroke=BORDER):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" '
            f'stroke="{stroke}" stroke-width="1"/>')

def dotgrid(w,h):
    return (f'<defs><pattern id="dots" width="22" height="22" patternUnits="userSpaceOnUse">'
            f'<circle cx="1" cy="1" r="1" fill="#ffffff" fill-opacity="0.022"/></pattern></defs>'
            f'<rect width="{w}" height="{h}" fill="url(#dots)"/>')

# A single sakura petal path (~13x15 local units), teardrop with a soft notch.
PETAL_PATH = "M6.5,0 C11,3 11.5,10 6.5,15 C1.5,10 2,3 6.5,0 Z"

def sakura(count, w, h, fill="url(#petal)", base_dur=9, top=-20, seed=0):
    """Falling-sakura layer: `count` petals drifting top->bottom on a CSS loop.
    Subtle by default (low opacity, slow, few petals)."""
    css = f""".pf{{animation-name:fall;animation-timing-function:linear;animation-iteration-count:infinite}}
    @keyframes fall{{
      0%{{transform:translate(0,{top}px) rotate(0deg);opacity:0}}
      12%{{opacity:.7}}
      88%{{opacity:.7}}
      100%{{transform:translate(var(--dx,18px),{h+24}px) rotate(var(--rot,320deg));opacity:0}}
    }}"""
    pet = []
    for i in range(count):
        x   = round(((i*9.7+seed*3.1)+5) % (w-12), 1)
        s   = round(0.55 + (i % 4)*0.22, 2)           # scale
        dur = round(base_dur + (i % 5)*1.9, 1)
        dly = round(-(i*1.6 + seed), 2)
        op  = round(0.30 + (i % 3)*0.16, 2)
        dx  = (18 if i % 2 else -16) + (i % 3)*6
        rot = 280 + (i % 4)*40
        pet.append(
            f'<g class="pf" style="animation-duration:{dur}s;animation-delay:{dly}s;'
            f'--dx:{dx}px;--rot:{rot}deg" transform="translate({x},0)">'
            f'<path d="{PETAL_PATH}" fill="{fill}" fill-opacity="{op}" '
            f'transform="scale({s})"/></g>')
    return css, "\n".join(pet)

def section_head(kanji, title, sub, cx=500, y=40):
    """Centered anime section header: kanji · Title · SUB · diamond rule."""
    return f"""<text x="{cx}" y="{y}" font-family="{SERIF}" font-size="30" fill="{ROSE}" text-anchor="middle">{kanji}</text>
<text x="{cx}" y="{y+44}" font-family="{SERIF}" font-size="38" font-weight="700" fill="{TEXT}" text-anchor="middle">{esc(title)}</text>
<text x="{cx}" y="{y+66}" font-family="{MONO}" font-size="12" letter-spacing="4" fill="{MUT}" text-anchor="middle">{esc(sub.upper())}</text>
<g transform="translate({cx},{y+84})">
  <rect x="-110" y="0" width="90" height="1.4" fill="url(#rosefade)"/>
  <rect x="-4" y="-4" width="9" height="9" rx="1.5" transform="rotate(45 0 0)" fill="{ROSE}"/>
  <rect x="20" y="0" width="90" height="1.4" fill="url(#rosefade)" transform="scale(-1,1)"/>
</g>"""

def wisteria(x, y, n=5, scale=1.0, delay=0.0):
    """A drooping wisteria (藤) cluster that sways gently — Demon Slayer motif."""
    beads=[]
    for i in range(n):
        by = i*16
        bx = (i%2)*5 - 2
        r  = 7 - i*0.7
        beads.append(f'<circle cx="{bx}" cy="{by+22}" r="{r:.1f}" fill="url(#wisg)" opacity="{0.9-i*0.08:.2f}"/>')
        beads.append(f'<circle cx="{bx-7}" cy="{by+30}" r="{r*0.8:.1f}" fill="url(#wisg)" opacity="{0.8-i*0.08:.2f}"/>')
        beads.append(f'<circle cx="{bx+7}" cy="{by+30}" r="{r*0.8:.1f}" fill="url(#wisg)" opacity="{0.8-i*0.08:.2f}"/>')
    return (f'<g class="sway" style="animation-delay:{delay}s" transform="translate({x},{y}) scale({scale})">'
            f'<line x1="0" y1="0" x2="0" y2="22" stroke="{BAMBOO}" stroke-width="1.6" opacity="0.5"/>'
            + "".join(beads) + "</g>")


# =============================================================================
# HERO
# =============================================================================
def hero():
    extra = f"""<radialGradient id="wisg" cx="0.5" cy="0.3" r="0.7">
      <stop offset="0" stop-color="#d9c2f2"/><stop offset="0.6" stop-color="{WIS}"/>
      <stop offset="1" stop-color="#7d5fb0"/></radialGradient>
    <clipPath id="hclip"><rect width="1000" height="360" rx="20"/></clipPath>"""
    scss, petals = sakura(13, 1000, 360, base_dur=10, seed=1)
    css = f""".sway{{transform-box:fill-box;transform-origin:top center;animation:sway 6s ease-in-out infinite}}
    @keyframes sway{{0%,100%{{transform:rotate(-4deg)}}50%{{transform:rotate(4deg)}}}}
    .sheen{{animation:sheen 8s ease-in-out infinite}}
    @keyframes sheen{{0%,100%{{transform:translateX(-12px)}}50%{{transform:translateX(12px)}}}}
    .pulse{{animation:pulse 2.4s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
    @keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.35}}}}
    .cur{{animation:blink 1.05s step-end infinite}}
    @keyframes blink{{0%,49%{{opacity:1}}50%,100%{{opacity:0}}}}
    {scss}"""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 360" width="1000" height="360">
{base_defs(extra)}
<style>{css}</style>
<g clip-path="url(#hclip)">
  <rect width="1000" height="360" fill="{INK}"/>
  <ellipse cx="150" cy="40" rx="430" ry="300" fill="url(#glowW)"/>
  <ellipse cx="950" cy="120" rx="430" ry="320" fill="url(#glowR)"/>
  {dotgrid(1000,360)}
  <!-- giant faint kanji watermark: 鬼を斬る = slay demons -->
  <text x="980" y="300" font-family="{SERIF}" font-size="300" fill="{ROSE}" fill-opacity="0.05" text-anchor="end">鬼</text>

  <!-- wisteria drooping from top-right -->
  <g class="sway">{wisteria(0,0,6,1.0)}</g>
  <g transform="translate(872,-6)">{wisteria(0,0,6,1.15,0.8)}</g>
  <g transform="translate(936,-2)">{wisteria(0,0,5,0.95,1.6)}</g>
  <g transform="translate(812,-4)">{wisteria(0,0,5,0.85,0.4)}</g>

  <!-- falling sakura -->
  <g>{petals}</g>

  <!-- text block -->
  <g transform="translate(56,118)">
    <rect x="0" y="-26" width="20" height="7" rx="3" fill="{BAMBOO}"/>
    <text x="30" y="-19" font-family="{MONO}" font-size="13" letter-spacing="2" fill="{ROSE}">// kisatsutai · software engineer</text>
    <text x="-2" y="78" font-family="{SERIF}" font-size="116" font-weight="700" fill="url(#title)" letter-spacing="-1">Dearie</text>
    <text x="2" y="120" font-family="{SERIF}" font-size="23" fill="{TEXT}">Full-stack developer &amp; interface artisan</text>
    <text x="2" y="156" font-family="{MONO}" font-size="14.5" fill="{ROSE}">I build calm systems under pressure<tspan class="cur" fill="{EMBER}">▌</tspan></text>
    <g transform="translate(2,184)" font-family="{MONO}" font-size="12.5">
      <circle class="pulse" cx="6" cy="-4" r="5" fill="{BAMBOO}"/>
      <text x="18" y="0" fill="{MUT}">open to missions · total concentration · remote-first</text>
    </g>
  </g>
  <rect x="0" y="0" width="1000" height="360" rx="20" fill="none" stroke="{BORDER}"/>
</g>
</svg>"""


# =============================================================================
# SAKURA DIVIDER (thin full-width strip)
# =============================================================================
def divider():
    scss, petals = sakura(16, 1000, 60, base_dur=7, seed=4)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 60" width="1000" height="60">
{base_defs()}<style>{scss}</style>
<rect width="1000" height="60" fill="none"/>
<line x1="40" y1="30" x2="430" y2="30" stroke="{BORDER}"/>
<line x1="570" y1="30" x2="960" y2="30" stroke="{BORDER}"/>
<rect x="495" y="25" width="10" height="10" rx="2" transform="rotate(45 500 30)" fill="{ROSE}"/>
<g>{petals}</g>
</svg>"""


# =============================================================================
# ABOUT
# =============================================================================
def about():
    img=b64("nezuko-1.jpg")
    scss, petals = sakura(6, 1000, 400, base_dur=11, seed=2)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 400" width="1000" height="400">
{base_defs()}
<defs>
  <clipPath id="aclip"><rect width="1000" height="400" rx="20"/></clipPath>
  <clipPath id="np"><rect x="648" y="150" width="320" height="234" rx="14"/></clipPath>
  <linearGradient id="pshade" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0.55" stop-color="{INK}" stop-opacity="0"/><stop offset="1" stop-color="{INK}" stop-opacity="0.82"/></linearGradient>
</defs>
<style>{scss}</style>
{panel_bg(0,0,1000,400,20,PANEL)}
<g clip-path="url(#aclip)">
  <ellipse cx="120" cy="380" rx="320" ry="240" fill="url(#glowR)"/>
  <g opacity="0.55">{petals}</g>
</g>
{section_head('心','About','Slayer Profile')}
<image x="648" y="150" width="320" height="234" href="data:image/jpeg;base64,{img}" preserveAspectRatio="xMidYMin slice" clip-path="url(#np)"/>
<rect x="648" y="150" width="320" height="234" rx="14" fill="url(#pshade)"/>
<rect x="648" y="150" width="320" height="234" rx="14" fill="none" stroke="{BORDER}"/>
<text x="666" y="372" font-family="{MONO}" font-size="11" fill="{ROSE}">竈門禰豆子 · bamboo resolve</text>
<rect x="56" y="158" width="3" height="176" rx="2" fill="url(#petal2)"/>
<text x="74" y="186" font-family="{SANS}" font-size="16.5" fill="#e3dbe6">
  <tspan x="74" dy="0">I’m <tspan font-weight="700" fill="{ROSE}">Dearie</tspan> — a developer who treats the</tspan>
  <tspan x="74" dy="28">interface like a discipline, not a decoration.</tspan>
  <tspan x="74" dy="28">I design and engineer systems that stay calm</tspan>
  <tspan x="74" dy="28">under pressure: graceful motion, accessibility</tspan>
  <tspan x="74" dy="28">as a baseline, and code the next person can</tspan>
  <tspan x="74" dy="28">read at a glance.</tspan>
</text>
<text x="74" y="360" font-family="{MONO}" font-size="13" fill="{MUT}">
  <tspan x="74" dy="0">Like Nezuko — fangs sheathed until it matters,</tspan>
  <tspan x="74" dy="18">then <tspan fill="{EMBER}">total concentration</tspan>.</tspan>
</text>
</svg>"""


# =============================================================================
# SECTORS (where I fight)  — 4 breathing styles
# =============================================================================
def sectors():
    data=[("水","Frontend","Mizu no Kokyuu","Interfaces that flow — React, motion, and design systems with care.",ROSE),
          ("炎","Backend","Honoo no Kokyuu","APIs and services that hold the line under heavy load.",EMBER),
          ("雷","AI & ML","Kaminari no Kokyuu","Fast, focused models — retrieval, agents, inference at the edge.",GOLD),
          ("風","Infra","Kaze no Kokyuu","Scale, reliability, and pipelines that never sleep.",BAMBOO)]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 360" width="1000" height="360">',
         base_defs(), section_head('戦','Sectors','Where I Fight')]
    cw,gap,x0,y0=487,26,0,148
    for i,(k,en,br,bl,clr) in enumerate(data):
        x=x0+(i%2)*(cw+gap); y=y0+(i//2)*108
        out.append(panel_bg(x,y,cw,94,16,PANEL))
        out.append(f'<text x="{x+30}" y="{y+62}" font-family="{SERIF}" font-size="42" fill="{clr}">{k}</text>')
        out.append(f'<text x="{x+82}" y="{y+34}" font-family="{SANS}" font-size="18" font-weight="700" fill="{TEXT}">{esc(en)}</text>')
        out.append(f'<text x="{x+82}" y="{y+53}" font-family="{MONO}" font-size="12" fill="{EMBER}">{esc(br)}</text>')
        # wrap blurb to ~46 chars
        words=bl.split(); lines=[""]
        for wd in words:
            if len(lines[-1])+len(wd)+1<=48: lines[-1]=(lines[-1]+" "+wd).strip()
            else: lines.append(wd)
        for j,ln in enumerate(lines[:2]):
            out.append(f'<text x="{x+82}" y="{y+72+j*16}" font-family="{SANS}" font-size="12.5" fill="{MUT}">{esc(ln)}</text>')
    out.append("</svg>"); return "\n".join(out)


# =============================================================================
# ARSENAL (blades & breathing) — restrained, NOT rainbow pills
# =============================================================================
def arsenal():
    groups=[("Languages",["TypeScript","Python","Go","Rust"]),
            ("Frameworks",["React","Next.js","Node","FastAPI"]),
            ("Data & AI",["PostgreSQL","Redis","PyTorch","LangChain"]),
            ("Cloud",["AWS","Docker","Kubernetes","Terraform"]),
            ("Craft",["Figma","Accessibility","Motion","Design Systems"])]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 430" width="1000" height="430">',
         base_defs(), section_head('刃','Arsenal','Blades & Breathing')]
    out.append(panel_bg(0,148,1000,270,18,PANEL))
    y=190
    for gi,(label,items) in enumerate(groups):
        out.append(f'<text x="40" y="{y+14}" font-family="{MONO}" font-size="12" letter-spacing="2" fill="{MUT}">{esc(label.upper())}</text>')
        x=210
        for it in items:
            w=20+len(it)*8.4+18
            out.append(f'<g transform="translate({x},{y})">'
                       f'<rect width="{w:.0f}" height="28" rx="8" fill="{PANEL2}" stroke="{BORDER}"/>'
                       f'<rect x="12" y="10" width="7" height="7" rx="1.5" transform="rotate(45 15.5 13.5)" fill="{ROSE}"/>'
                       f'<text x="28" y="19" font-family="{MONO}" font-size="13" fill="{TEXT}">{esc(it)}</text></g>')
            x+=w+10
        y+=46
        if gi<len(groups)-1:
            out.append(f'<rect x="40" y="{y-12}" width="920" height="1" fill="{BORDER}" fill-opacity="0.6"/>')
    out.append("</svg>"); return "\n".join(out)


# =============================================================================
# INTERMISSION (cinematic band)
# =============================================================================
def intermission():
    img=b64("nezuko-2.jpg")
    scss, petals = sakura(8, 1000, 220, base_dur=8, seed=5)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 220" width="1000" height="220">
{base_defs()}
<defs>
  <clipPath id="iclip"><rect width="1000" height="220" rx="20"/></clipPath>
  <clipPath id="ip"><rect x="16" y="16" width="300" height="188" rx="14"/></clipPath>
</defs>
<style>{scss}</style>
<g clip-path="url(#iclip)">
  <rect width="1000" height="220" fill="{PANEL2}"/>
  <rect width="1000" height="220" fill="{INK}" opacity="0.30"/>
  <ellipse cx="170" cy="110" rx="520" ry="260" fill="url(#glowW)"/>
  <ellipse cx="900" cy="60" rx="360" ry="240" fill="url(#glowR)"/>
  {dotgrid(1000,220)}
  <text x="942" y="200" font-family="{SERIF}" font-size="190" fill="{ROSE}" fill-opacity="0.05" text-anchor="end">斬</text>
  <g opacity="0.7">{petals}</g>
</g>
<image x="16" y="16" width="300" height="188" href="data:image/jpeg;base64,{img}" preserveAspectRatio="xMidYMid slice" clip-path="url(#ip)"/>
<rect x="16" y="16" width="300" height="188" rx="14" fill="none" stroke="{BORDER}"/>
<text x="356" y="86" font-family="{MONO}" font-size="12" letter-spacing="4" fill="{EMBER}">立ち止まるな</text>
<rect x="356" y="100" width="64" height="2" fill="{ROSE}"/>
<text x="356" y="138" font-family="{SERIF}" font-size="32" font-weight="600" fill="{TEXT}">Never stop. Keep moving forward.</text>
<text x="356" y="172" font-family="{SANS}" font-size="14" fill="{MUT}">Tucked away until the moment comes — then I move.</text>
<rect width="1000" height="220" rx="20" fill="none" stroke="{BORDER}"/>
</svg>"""


# =============================================================================
# LIVE GITHUB STATS  — fetched in the daily Action (GH_USER + GH_TOKEN env).
# Falls back to placeholders when no token/username (e.g. local builds).
# =============================================================================
def fmt(n):
    return f"{n:,}"

_GQL = """query($login:String!){ user(login:$login){
  repositories(first:100, ownerAffiliations:OWNER, isFork:false, orderBy:{field:STARGAZERS,direction:DESC}){
    nodes{ stargazerCount languages(first:8){edges{size node{name color}}} } }
  pullRequests{totalCount} issues{totalCount}
  repositoriesContributedTo(includeUserRepositories:false, contributionTypes:[COMMIT,PULL_REQUEST,ISSUE,REPOSITORY]){totalCount}
  contributionsCollection{ totalCommitContributions totalPullRequestReviewContributions
    contributionCalendar{ weeks{ contributionDays{ date contributionCount } } } }
}}"""

def fetch_stats():
    user=os.environ.get("GH_USER"); token=os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if not user or not token:
        return None
    try:
        body=json.dumps({"query":_GQL,"variables":{"login":user}}).encode()
        req=urllib.request.Request("https://api.github.com/graphql", data=body, headers={
            "Authorization":f"bearer {token}","Content-Type":"application/json","User-Agent":"dearie-readme"})
        with urllib.request.urlopen(req, timeout=25) as r:
            u=json.load(r)["data"]["user"]
        if not u: return None
        repos=u["repositories"]["nodes"]
        cc=u["contributionsCollection"]
        # languages -> top 5 + Other
        sizes={}; cols={}
        for n in repos:
            for e in n["languages"]["edges"]:
                nm=e["node"]["name"]; sizes[nm]=sizes.get(nm,0)+e["size"]; cols[nm]=e["node"]["color"]
        tot=sum(sizes.values()) or 1
        fb=[ROSE,WIS,"#3fc7d8",EMBER,BAMBOO]; langs=[]; acc=0
        for i,(nm,sz) in enumerate(sorted(sizes.items(), key=lambda x:-x[1])[:5]):
            pct=round(sz/tot*100); acc+=pct; langs.append((nm,pct,cols.get(nm) or fb[i%5]))
        if langs and acc<100: langs.append(("Other",100-acc,BAMBOO))
        # streak from calendar
        days=[d["contributionCount"] for w in cc["contributionCalendar"]["weeks"] for d in w["contributionDays"]]
        cur=0
        for i in range(len(days)-1,-1,-1):
            if days[i]>0: cur+=1
            elif i==len(days)-1: continue   # today not committed yet — streak still alive
            else: break
        longest=run=0
        for c in days:
            run=run+1 if c>0 else 0; longest=max(longest,run)
        return {
            "stats":[("Total Stars",fmt(sum(n["stargazerCount"] for n in repos))),
                     ("Commits (1y)",fmt(cc["totalCommitContributions"])),
                     ("Pull Requests",fmt(u["pullRequests"]["totalCount"])),
                     ("Issues",fmt(u["issues"]["totalCount"])),
                     ("Contributed to",fmt(u["repositoriesContributedTo"]["totalCount"])),
                     ("Reviews",fmt(cc["totalPullRequestReviewContributions"]))],
            "langs":langs or None, "streak":cur, "longest":longest, "recent":days[-30:]}
    except Exception as ex:
        print("  stats fetch failed — using placeholders:", ex); return None


# =============================================================================
# TELEMETRY (脈) — stats + streak + langs + activity
# =============================================================================
def telemetry():
    d=fetch_stats()
    stats=d["stats"] if d else [("Total Stars","2.6k"),("Commits (2026)","1,284"),("Pull Requests","312"),
           ("Issues Closed","148"),("Contributed to","27"),("Reviews","410")]
    langs=(d and d["langs"]) or [("TypeScript",34,"#56a8e8"),("Python",24,WIS),("Go",18,"#3fc7d8"),
           ("Rust",14,EMBER),("Other",10,BAMBOO)]
    streak=d["streak"] if d else 47
    longest=d["longest"] if d else 96
    # activity path — real recent contributions when available, else a calm synthetic wave
    import math
    pad,H=10,150
    if d and d.get("recent"):
        rc=d["recent"]; mx=max(rc) or 1; vals=[8+(c/mx)*120 for c in rc]
    else:
        vals=[55+44*abs(math.sin(i*0.55))+i*1.4+abs(math.sin(i*3.3))*14 for i in range(26)]
    n=len(vals); W=920
    X=lambda i:(i/(n-1))*(W-pad*2)+pad
    Y=lambda v:H-pad-min(H-pad,v)*0.82
    line=f"M {X(0):.1f} {Y(vals[0]):.1f}"
    for i in range(1,n):
        xc=(X(i-1)+X(i))/2
        line+=f" Q {X(i-1):.1f} {Y(vals[i-1]):.1f} {xc:.1f} {(Y(vals[i-1])+Y(vals[i]))/2:.1f} T {X(i):.1f} {Y(vals[i]):.1f}"
    area=line+f" L {X(n-1):.1f} {H-pad} L {X(0):.1f} {H-pad} Z"

    extra=f"""<linearGradient id="actFill" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{ROSE}" stop-opacity="0.42"/><stop offset="1" stop-color="{ROSE}" stop-opacity="0"/></linearGradient>
    <linearGradient id="actLine" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0" stop-color="{WIS}"/><stop offset="0.55" stop-color="{ROSE}"/><stop offset="1" stop-color="{EMBER}"/></linearGradient>"""
    css=f""".flame{{animation:flick 1.6s ease-in-out infinite;transform-box:fill-box;transform-origin:center}}
    @keyframes flick{{0%,100%{{transform:scale(1) rotate(-2deg);opacity:1}}50%{{transform:scale(1.12) rotate(2deg);opacity:.85}}}}
    .draw{{stroke-dasharray:2600;stroke-dashoffset:2600;animation:draw 3.2s ease-out forwards}}
    @keyframes draw{{to{{stroke-dashoffset:0}}}}"""
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 720" width="1000" height="720">',
         base_defs(extra), f'<style>{css}</style>', section_head('脈','Telemetry','Live GitHub Data')]
    # stats card
    out.append(panel_bg(0,148,600,180,16,PANEL))
    out.append(f'<text x="34" y="186" font-family="{SERIF}" font-size="18" font-weight="600" fill="{ROSE}">Dearie’s GitHub Stats</text>')
    out.append(f'<circle cx="556" cy="180" r="22" fill="none" stroke="{BORDER}" stroke-width="4"/>')
    out.append(f'<circle cx="556" cy="180" r="22" fill="none" stroke="{ROSE}" stroke-width="4" stroke-dasharray="122 138" transform="rotate(-90 556 180)" stroke-linecap="round"/>')
    out.append(f'<text x="556" y="185" font-family="{MONO}" font-size="14" font-weight="700" fill="{ROSE}" text-anchor="middle">A+</text>')
    for i,(lb,vl) in enumerate(stats):
        cx=34+(i%2)*286; cy=224+(i//2)*34
        out.append(f'<text x="{cx}" y="{cy}" font-family="{SANS}" font-size="13" fill="{MUT}">{esc(lb)}</text>')
        out.append(f'<text x="{cx+252}" y="{cy}" font-family="{MONO}" font-size="14" font-weight="700" fill="{TEXT}" text-anchor="end">{esc(vl)}</text>')
        out.append(f'<rect x="{cx}" y="{cy+7}" width="252" height="1" fill="{BORDER}" stroke-dasharray="3 3"/>')
    # streak card
    out.append(panel_bg(626,148,374,180,16,PANEL))
    out.append(f'<text x="813" y="180" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{MUT}" text-anchor="middle">CURRENT STREAK</text>')
    out.append(f'<text class="flame" x="813" y="236" font-family="{SERIF}" font-size="58" fill="{EMBER}" text-anchor="middle">火</text>')
    out.append(f'<circle cx="813" cy="216" r="40" fill="none" stroke="{EMBER}" stroke-width="2" stroke-opacity="0.6"/>')
    out.append(f'<text x="813" y="286" font-family="{MONO}" font-size="30" font-weight="700" fill="{EMBER}" text-anchor="middle">{streak}</text>')
    out.append(f'<text x="813" y="308" font-family="{SANS}" font-size="12" fill="{MUT}" text-anchor="middle">days · longest {longest}</text>')
    # languages
    out.append(panel_bg(0,352,1000,150,16,PANEL))
    out.append(f'<text x="34" y="388" font-family="{SERIF}" font-size="18" font-weight="600" fill="{ROSE}">Most Used Breathing — Top Languages</text>')
    bx=34; bw=932
    out.append(f'<clipPath id="bar"><rect x="{bx}" y="404" width="{bw}" height="12" rx="6"/></clipPath>')
    cur=bx
    for nm,pct,c in langs:
        wseg=bw*pct/100
        out.append(f'<rect x="{cur:.1f}" y="404" width="{wseg:.1f}" height="12" fill="{c}" clip-path="url(#bar)"/>')
        cur+=wseg
    for i,(nm,pct,c) in enumerate(langs):
        cx=34+(i%3)*330; cy=448+(i//3)*26
        out.append(f'<circle cx="{cx+5}" cy="{cy-4}" r="5.5" fill="{c}"/>')
        out.append(f'<text x="{cx+18}" y="{cy}" font-family="{SANS}" font-size="13" fill="{TEXT}">{esc(nm)}</text>')
        out.append(f'<text x="{cx+300}" y="{cy}" font-family="{MONO}" font-size="12" fill="{MUT}" text-anchor="end">{pct}%</text>')
    # activity
    out.append(panel_bg(0,526,1000,180,16,PANEL))
    out.append(f'<text x="34" y="562" font-family="{SERIF}" font-size="18" font-weight="600" fill="{ROSE}">Contribution Activity</text>')
    out.append(f'<g transform="translate(40,556)"><path d="{area}" fill="url(#actFill)"/>'
               f'<path class="draw" d="{line}" fill="none" stroke="url(#actLine)" stroke-width="2.5" stroke-linejoin="round" stroke-linecap="round"/></g>')
    out.append("</svg>"); return "\n".join(out)


# =============================================================================
# MISSION BOARD (任)
# =============================================================================
def mission():
    rows=[(True,"Ship the asanoha design system v2"),
          (True,"Reach Hashira rank on the platform team"),
          (False,"Open-source the kokyuu realtime engine"),
          (False,"Publish the “Breathing Forms” essay series"),
          (False,"Mentor two new slayers through Final Selection")]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 380" width="1000" height="380">',
         base_defs(), section_head('任','Mission Board','Objectives This Arc')]
    out.append(panel_bg(0,148,1000,210,18,PANEL))
    for i,(done,t) in enumerate(rows):
        y=190+i*34
        if done:
            out.append(f'<rect x="40" y="{y-15}" width="22" height="22" rx="6" fill="url(#petal2)"/>')
            out.append(f'<text x="51" y="{y+1}" font-family="{SANS}" font-size="13" font-weight="700" fill="#fff" text-anchor="middle">✓</text>')
            out.append(f'<text x="78" y="{y}" font-family="{SANS}" font-size="15" fill="{MUT}" text-decoration="line-through">{esc(t)}</text>')
        else:
            out.append(f'<rect x="40" y="{y-15}" width="22" height="22" rx="6" fill="none" stroke="{BORDER}" stroke-width="1.5"/>')
            out.append(f'<text x="78" y="{y}" font-family="{SANS}" font-size="15" fill="{TEXT}">{esc(t)}</text>')
    out.append("</svg>"); return "\n".join(out)


# =============================================================================
# CROW RADIO (音) — now playing card, animated EQ
# =============================================================================
def radio():
    css=f""".eq span{{}}
    .b{{animation:eq 0.9s ease-in-out infinite;transform-box:fill-box;transform-origin:bottom}}
    @keyframes eq{{0%,100%{{transform:scaleY(0.3)}}50%{{transform:scaleY(1)}}}}"""
    bars=[(0,40,ROSE),(0.15,70,ROSE),(0.3,50,EMBER),(0.45,85,ROSE),(0.6,35,WIS),(0.75,60,ROSE),(0.9,45,EMBER)]
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 360" width="1000" height="360">',
         base_defs(), f'<style>{css}</style>', section_head('音','Crow Radio','Now Playing')]
    out.append(panel_bg(0,148,1000,200,18,PANEL2))
    # album art
    out.append('<defs><clipPath id="art"><rect x="40" y="186" width="120" height="120" rx="14"/></clipPath></defs>')
    out.append(f'<rect x="40" y="186" width="120" height="120" rx="14" fill="{INK}" stroke="{BORDER}"/>')
    out.append(f'<g clip-path="url(#art)"><ellipse cx="100" cy="200" rx="90" ry="70" fill="url(#glowR)"/>'
               f'<text x="100" y="280" font-family="{SERIF}" font-size="92" fill="{ROSE}" fill-opacity="0.85" text-anchor="middle">音</text></g>')
    # meta
    out.append(f'<text x="190" y="206" font-family="{MONO}" font-size="11" letter-spacing="2" fill="{BAMBOO}">CROW RADIO · NOW PLAYING — click to open the playlist</text>')
    out.append(f'<text x="190" y="240" font-family="{SERIF}" font-size="26" font-weight="700" fill="{TEXT}">Gurenge</text>')
    out.append(f'<text x="190" y="264" font-family="{SANS}" font-size="14" fill="{MUT}">LiSA · Demon Slayer OST</text>')
    out.append(f'<rect x="190" y="284" width="600" height="6" rx="3" fill="{BORDER}"/>')
    out.append(f'<rect x="190" y="284" width="252" height="6" rx="3" fill="url(#petal2)"/>')
    # eq bars
    out.append('<g transform="translate(890,256)">')
    for i,(d,h,c) in enumerate(bars):
        out.append(f'<rect class="b" style="animation-delay:{d}s" x="{i*11}" y="-{h*0.5:.0f}" width="5" height="{h}" rx="2.5" fill="{c}"/>')
    out.append('</g>')
    out.append("</svg>"); return "\n".join(out)


# =============================================================================
# FOOTER
# =============================================================================
def footer():
    scss, petals = sakura(10, 1000, 120, base_dur=8, seed=7)
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 130" width="1000" height="130">
{base_defs()}<style>{scss}</style>
<g opacity="0.7">{petals}</g>
<g transform="translate(500,40)">
  <rect x="-90" y="0" width="70" height="1.2" fill="url(#rosefade)"/>
  <rect x="-8" y="-8" width="16" height="16" rx="4" transform="rotate(45 0 0)" fill="url(#petal2)"/>
  <rect x="20" y="0" width="70" height="1.2" fill="url(#rosefade)" transform="scale(-1,1)"/>
</g>
<text x="500" y="86" font-family="{MONO}" font-size="12.5" letter-spacing="3" fill="{MUT}" text-anchor="middle">SLAYING BUGS, ONE COMMIT AT A TIME</text>
<text x="500" y="110" font-family="{MONO}" font-size="12.5" letter-spacing="3" fill="{ROSE}" text-anchor="middle">· FROM THE WISTERIA GARDEN ·</text>
</svg>"""


def head(kanji,title,sub):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 122" width="1000" height="122">'
            f'{base_defs()}{section_head(kanji,title,sub,cx=500,y=40)}</svg>')


# =============================================================================
# DAILY JAPANESE QUOTE (言)  — rotates by date; refreshed by a GitHub Action
# =============================================================================
# (jp, romaji, english) — authentic kotowaza / proverbs
QUOTES = [
 ("七転び八起き","Nana korobi ya oki","Fall seven times, stand up eight."),
 ("継続は力なり","Keizoku wa chikara nari","Perseverance is strength."),
 ("一期一会","Ichi-go ichi-e","One life, one encounter — treasure every meeting."),
 ("石の上にも三年","Ishi no ue ni mo san-nen","Sit three years on a rock and even it grows warm."),
 ("初心忘るべからず","Shoshin wasuru bekarazu","Never forget your beginner's mind."),
 ("千里の道も一歩から","Senri no michi mo ippo kara","A journey of a thousand miles begins with one step."),
 ("急がば回れ","Isogaba maware","When in a hurry, take the long road."),
 ("塵も積もれば山となる","Chiri mo tsumoreba yama to naru","Even dust, piled up, becomes a mountain."),
 ("案ずるより産むが易し","Anzuru yori umu ga yasushi","The doing is easier than the worrying."),
 ("能ある鷹は爪を隠す","Nō aru taka wa tsume o kakusu","The able hawk hides its talons."),
 ("猿も木から落ちる","Saru mo ki kara ochiru","Even monkeys fall from trees."),
 ("出る杭は打たれる","Deru kui wa utareru","The stake that sticks out gets hammered down."),
 ("雨降って地固まる","Ame futte ji katamaru","After the rain, the ground hardens."),
 ("笑う門には福来る","Warau kado ni wa fuku kitaru","Fortune comes to the cheerful door."),
 ("虎穴に入らずんば虎子を得ず","Koketsu ni irazunba koji o ezu","Without entering the tiger's den, you won't catch its cub."),
 ("二兎を追う者は一兎をも得ず","Nito o ou mono wa itto o mo ezu","Chase two rabbits and you catch neither."),
 ("井の中の蛙大海を知らず","I no naka no kawazu taikai o shirazu","A frog in a well knows nothing of the great sea."),
 ("過ぎたるは猶及ばざるが如し","Sugitaru wa nao oyobazaru ga gotoshi","Too much is as bad as too little."),
 ("善は急げ","Zen wa isoge","Make haste to do good."),
 ("明日は明日の風が吹く","Ashita wa ashita no kaze ga fuku","Tomorrow the winds of tomorrow will blow."),
 ("十人十色","Jūnin to-iro","Ten people, ten colors."),
 ("花より団子","Hana yori dango","Substance over appearance."),
 ("三人寄れば文殊の知恵","Sannin yoreba Monju no chie","Three heads together hold a sage's wisdom."),
 ("ローマは一日にして成らず","Rōma wa ichinichi ni shite narazu","Rome was not built in a day."),
 ("猫に小判","Neko ni koban","Gold coins to a cat — wasted on the unappreciative."),
 ("七転八倒","Shichiten battō","Fall and rise through a hundred struggles."),
 ("天は自ら助くる者を助く","Ten wa mizukara tasukuru mono o tasuku","Heaven helps those who help themselves."),
 ("習うより慣れろ","Narau yori narero","Practice beats theory."),
 ("好きこそ物の上手なれ","Suki koso mono no jōzu nare","What one loves, one does well."),
 ("水を得た魚","Mizu o eta uo","Like a fish that has found water."),
]

def quote_svg():
    idx = datetime.date.today().timetuple().tm_yday % len(QUOTES)
    jp, ro, en = QUOTES[idx]
    today = datetime.date.today().isoformat()
    # wrap english to <= ~58 chars, max 2 lines
    words=en.split(); lines=[""]
    for w in words:
        if len(lines[-1])+len(w)+1<=58: lines[-1]=(lines[-1]+" "+w).strip()
        else: lines.append(w)
    en_lines=lines[:2]
    jp_size = 40 if len(jp)<=11 else (32 if len(jp)<=15 else 26)
    out=[f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1000 300" width="1000" height="300">',
         base_defs()]
    scss,petals=sakura(6,1000,300,base_dur=12,seed=9)
    out.append(f'<style>{scss}</style>')
    out.append(panel_bg(0,0,1000,300,20,PANEL))
    out.append(f'<g clip-path="url(#qclip)"><defs><clipPath id="qclip"><rect width="1000" height="300" rx="20"/></clipPath></defs>'
               f'<ellipse cx="500" cy="-20" rx="520" ry="220" fill="url(#glowR)"/>'
               f'<text x="60" y="280" font-family="{SERIF}" font-size="190" fill="{WIS}" fill-opacity="0.05">言</text>'
               f'<g opacity="0.5">{petals}</g></g>')
    out.append(section_head('言','Word of the Day','Kotoba'))
    out.append(f'<text x="500" y="196" font-family="{SERIF}" font-size="{jp_size}" font-weight="700" fill="{TEXT}" text-anchor="middle">{esc(jp)}</text>')
    out.append(f'<text x="500" y="226" font-family="{MONO}" font-size="14" font-style="italic" fill="{EMBER}" text-anchor="middle">{esc(ro)}</text>')
    for i,ln in enumerate(en_lines):
        out.append(f'<text x="500" y="{256+i*22}" font-family="{SANS}" font-size="15" fill="{MUT}" text-anchor="middle">{esc(ln)}</text>')
    out.append(f'<text x="40" y="290" font-family="{MONO}" font-size="10.5" letter-spacing="1" fill="{MUT}" fill-opacity="0.5">ことわざ</text>')
    out.append(f'<text x="960" y="290" font-family="{MONO}" font-size="10.5" letter-spacing="1" fill="{MUT}" fill-opacity="0.5" text-anchor="end">{today} · refreshed daily</text>')
    out.append("</svg>")
    return "\n".join(out)

if __name__=="__main__":
    ASSETS.mkdir(exist_ok=True)
    write("hero.svg",hero())
    write("divider.svg",divider())
    write("about.svg",about())
    write("sectors.svg",sectors())
    write("arsenal.svg",arsenal())
    write("intermission.svg",intermission())
    write("telemetry.svg",telemetry())
    write("mission.svg",mission())
    write("quote.svg",quote_svg())
    write("footer.svg",footer())
    write("connect_head.svg",head('烏','Crow','Connect'))
    print("done.")

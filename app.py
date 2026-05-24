
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlparse
from pathlib import Path
import os
import sqlite3, datetime, html, json, mimetypes

HOST="0.0.0.0"; PORT=int(os.environ.get("PORT","8080")); DB_PATH=Path("wagners_pizza.sqlite3"); ASSET_DIR=Path("assets")
PIZZAS=[("salami","Salami",6.90),("schinken","Schinken",6.90),("diavolo","Diavolo",7.50),("vegetarisch","Vegetarisch",7.20),("trueffel","Trüffel",8.90)]
SIZES=[("small","Klein 22 cm",0),("medium","Mittel 28 cm",2.00),("large","Groß 32 cm",3.50),("family","Familie 40 cm",6.00)]
TOPPINGS=[("kaese","Extra Käse",1.00),("salami_extra","Extra Salami",1.20),("peperoni","Peperoni",0.90),("champignons","Champignons",0.80),("paprika","Paprika",0.80),("rucola","Rucola",0.90),("oliven","Oliven",0.80)]
ORDER_STEPS=[("neu","Neue Bestellung"),("tk_holen","Pizza aus TK holen"),("antauen","Antauen / vorbereiten"),("belegen","Toppings ergänzen"),("backen","Backen"),("abholfach","Abholfach"),("fertig","Fertig / geliefert")]
def esc(x): return html.escape(str(x), quote=True)
def now(): return datetime.datetime.now().isoformat(timespec="seconds")
def init_db():
    con=sqlite3.connect(DB_PATH); cur=con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS orders(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,customer TEXT,pizza TEXT,size TEXT,toppings TEXT,total REAL,comment TEXT,status TEXT DEFAULT 'neu')")
    cur.execute("CREATE TABLE IF NOT EXISTS feedback(id INTEGER PRIMARY KEY AUTOINCREMENT,created_at TEXT,tester TEXT,observation TEXT,must_have TEXT,willingness TEXT,result TEXT)")
    con.commit(); con.close()
CSS = """
body{font-family:Arial,sans-serif;margin:0;background:#090909;color:#fff}a{text-decoration:none}.nav{position:sticky;top:0;z-index:30;background:rgba(8,8,10,.96);display:flex;gap:16px;justify-content:space-between;align-items:center;padding:14px 28px;border-bottom:1px solid rgba(244,176,0,.28)}
.logo{font-weight:900;font-size:26px;color:#fff}.logo span{display:block;font-size:15px;color:#f4b000;letter-spacing:5px}.navlinks{display:flex;gap:10px;flex-wrap:wrap}.navlinks a{color:#fff;background:#1f2937;border-radius:999px;padding:9px 13px;font-weight:bold}.navlinks a.gold{background:#f4b000;color:#111}
.hero{min-height:78vh;display:grid;grid-template-columns:1.02fr .98fr;gap:20px;align-items:center;padding:54px 7vw;background:radial-gradient(circle at 40% 48%,rgba(244,176,0,.22),transparent 22%),linear-gradient(135deg,#0b0b0d 0%,#1e1209 55%,#050505 100%)}.hero h1{font-size:64px;line-height:.95;margin:0 0 18px;font-weight:950;text-transform:uppercase}.hero h1 span{color:#f4b000}.hero p{font-size:21px;color:#e5e7eb;line-height:1.45}.hero-img{border:1px solid rgba(244,176,0,.35);border-radius:26px;overflow:hidden;box-shadow:0 30px 90px rgba(0,0,0,.65);background:#111}.hero-img img{width:100%;height:100%;object-fit:cover;display:block}
.cta{display:flex;gap:14px;flex-wrap:wrap;margin-top:28px}.btn{display:inline-block;padding:15px 20px;border-radius:14px;background:#f4b000;color:#111;font-weight:900}.btn.outline{background:transparent;border:1px solid #f4b000;color:#f4b000}.icons{display:grid;grid-template-columns:repeat(4,1fr);gap:12px;margin:26px 0}.iconbox{border:1px solid rgba(244,176,0,.45);border-radius:18px;padding:14px;text-align:center;color:#f6d98e}.iconbox b{display:block;color:#f4b000;margin-top:7px}
section{padding:38px 7vw}.section-title{text-align:center;color:#f4b000;letter-spacing:6px;text-transform:uppercase;margin-bottom:24px}.grid{display:grid;grid-template-columns:repeat(3,1fr);gap:18px}.card{background:#151515;border:1px solid rgba(244,176,0,.35);border-radius:20px;padding:20px;box-shadow:0 10px 30px rgba(0,0,0,.35)}.card h3{color:#f4b000;margin-top:0}.card img{width:100%;height:190px;object-fit:cover;border-radius:14px;margin-bottom:12px}.footerline{border-top:1px solid rgba(244,176,0,.28);padding:24px 7vw;color:#cbd5e1;display:flex;justify-content:space-between;gap:16px;flex-wrap:wrap}
.app{max-width:460px;margin:0 auto;min-height:100vh;background:#151b2b}.mnav{position:sticky;top:0;z-index:10;background:#0b1020;padding:8px;display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.mnav a{text-align:center;background:#263044;color:white;border-radius:10px;padding:10px 4px;font-size:13px;font-weight:700}.mnav a.active{background:#f4b000;color:#111827}.mhero{padding:24px 18px;background:linear-gradient(135deg,#111827,#2b1d12)}.mhero h1{margin:0;font-size:30px}.mcard{background:#fff;color:#111827;margin:14px;border-radius:18px;padding:16px;box-shadow:0 4px 16px rgba(0,0,0,.25)}
input,select,textarea,button{width:100%;box-sizing:border-box;padding:13px;margin:8px 0 14px;font-size:17px;border-radius:12px;border:1px solid #d1d5db}textarea{min-height:90px}button{background:#f4b000;color:#111;border:0;font-weight:800}.secondary{background:#111827;color:white}.price{font-size:30px;font-weight:900}.small{color:#6b7280;font-size:13px}.checks label{display:block;background:#f8fafc;padding:10px;border-radius:10px;margin:6px 0}
.adminbody{background:#f3f4f6;color:#111}.admin header{background:#111827;color:white;padding:22px 30px}.admin main{padding:22px;max-width:1200px;margin:0 auto}.admin .card{background:white;color:#111;border-radius:16px;padding:18px;margin-bottom:16px;border:0}.admin table{width:100%;border-collapse:collapse}.admin td,.admin th{border:1px solid #ddd;padding:7px;font-size:13px}.status{display:inline-block;padding:5px 10px;border-radius:999px;background:#f4b000;color:#111;font-weight:bold}@media(max-width:900px){.hero{grid-template-columns:1fr}.hero h1{font-size:42px}.grid,.icons{grid-template-columns:1fr}.nav{align-items:flex-start;flex-direction:column}.card img{height:auto}}
"""
def page(title,body,admin=False): return f"<!doctype html><html lang='de'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>{esc(title)}</title><style>{CSS}</style></head><body class='{'adminbody' if admin else ''}'>{body}</body></html>"
def nav_web(): return "<div class='nav'><div class='logo'>Wagner's<span>PIZZERIA</span></div><div class='navlinks'><a href='/wagner/website'>Startseite</a><a class='gold' href='/wagner/app'>Wagner App starten</a><a href='/wagner/kitchen'>Küche/Ofen</a><a href='/wagner/admin'>Buchung</a></div></div>"
def website():
    body=f"""{nav_web()}<div class='hero'><div><h1>TK Pizza. <span>Frisch gebacken.</span><br>Unschlagbar einfach.</h1><p>Wagner’s Pizza Shop verbindet gekühlte Produktauswahl, frisches Backen, individuelle Toppings und einen klaren Abholprozess.</p><div class='icons'><div class='iconbox'>❄️<b>TK auswählen</b></div><div class='iconbox'>🔥<b>Frisch backen</b></div><div class='iconbox'>➕<b>Toppings</b></div><div class='iconbox'>📦<b>Abholen</b></div></div><div class='cta'><a class='btn' href='/wagner/app'>Wagner App starten →</a><a class='btn outline' href='/wagner/kitchen'>Küche / Ofen öffnen</a></div></div><div class='hero-img'><img src='/assets/wagner_web_mockup.png' onerror=\"this.src='/assets/wagner_board_1.png'\"></div></div>
<section><h2 class='section-title'>Wagner App – alles an einem Ort</h2><div class='grid'><div class='card'><img src='/assets/wagner_board_1.png'><h3>Kunden-App</h3><p>Bestellen, Toppings wählen und Feedback geben.</p><a class='btn' href='/wagner/app'>App öffnen →</a></div><div class='card'><img src='/assets/wagner_product.png'><h3>Küche / Ofen</h3><p>Backprozess steuern: TK holen, antauen, belegen, backen, Abholfach.</p><a class='btn' href='/wagner/kitchen'>Öffnen →</a></div><div class='card'><img src='/assets/wagner_fridge.png'><h3>Buchungssystem</h3><p>Bestellungen, Status, Umsatz und Feedback im Überblick.</p><a class='btn' href='/wagner/admin'>Öffnen →</a></div></div></section>
<section><h2 class='section-title'>So funktioniert&apos;s</h2><div class='grid'><div class='card'><h3>1. Pizza auswählen</h3><p>Kunde wählt Sorte und Größe.</p></div><div class='card'><h3>2. Toppings ergänzen</h3><p>Optional individuelle Ergänzungen.</p></div><div class='card'><h3>3. Frisch backen</h3><p>Prozess landet direkt im Küchen-/Ofen-GUI.</p></div><div class='card'><h3>4. Abholen</h3><p>Pizza wird dem Abholfach zugeordnet.</p></div><div class='card'><h3>5. Feedback</h3><p>Nach der Bestellung folgt Design-Sprint-Feedback.</p></div><div class='card'><h3>6. Auswerten</h3><p>Bestellungen und Rückmeldungen im Buchungssystem.</p></div></div></section><div class='footerline'><b>Wagner’s Pizzeria – die Zukunft des Pizzagenusses.</b><span>Pizza. Neu gedacht.</span></div>"""
    return page("Wagner's Pizza Shop",body)
def mnav(active="app"):
    items=[("web","/wagner/website","Web"),("app","/wagner/app","Kunde"),("kitchen","/wagner/kitchen","Küche"),("admin","/wagner/admin","Buchung")]
    return '<div class="mnav">'+''.join(f'<a class="{"active" if k==active else ""}" href="{u}">{l}</a>' for k,u,l in items)+'</div>'
def feedback_form(customer=""): return f"<div class='mcard'><h2>Kurzes Feedback nach der Bestellung</h2><p class='small'>Für den Design-Sprint: erst bestellen, dann bewerten.</p><form method='POST' action='/wagner/api/feedback'><label>Tester</label><input name='tester' value='{esc(customer)}'><label>Was war verständlich oder unklar?</label><textarea name='observation'></textarea><label>Was fehlt zwingend?</label><textarea name='must_have'></textarea><label>Kaufbereitschaft</label><select name='willingness'><option>hoch</option><option>mittel</option><option>niedrig</option><option>unklar</option></select><label>Ergebnis</label><select name='result'><option>weiter testen</option><option>ändern</option><option>verwerfen</option><option>verkaufsfähig</option></select><button class='secondary'>Feedback speichern</button></form></div>"
def app_view(result=""):
    pizza_opts=''.join(f'<option value="{pid}">{name} – {base:.2f} €</option>' for pid,name,base in PIZZAS); size_opts=''.join(f'<option value="{sid}">{name} + {add:.2f} €</option>' for sid,name,add in SIZES); tops=''.join(f'<label><input type="checkbox" name="topping" value="{tid}"> {name} +{price:.2f} €</label>' for tid,name,price in TOPPINGS)
    body=f"<div class='app'>{mnav('app')}<div class='mhero'><h1>Wagner's <span style='color:#f4b000'>Pizza</span></h1><p>TK-Pizza. Frisch gebacken. Individuell.</p></div>{result}<div class='mcard'><h2>Pizza bestellen</h2><form method='POST' action='/wagner/api/order'><label>Name / Testperson</label><input name='customer'><label>Pizza</label><select name='pizza'>{pizza_opts}</select><label>Größe</label><select name='size'>{size_opts}</select><label>Toppings</label><div class='checks'>{tops}</div><label>Kommentar</label><textarea name='comment'></textarea><button>Bestellung simulieren</button></form></div></div>"
    return page("Wagner Kunden-App",body)
def calc_order(form):
    pid=form.get("pizza",["salami"])[0]; sid=form.get("size",["medium"])[0]; selected=form.get("topping",[])
    pizza=next((p for p in PIZZAS if p[0]==pid),PIZZAS[0]); size=next((s for s in SIZES if s[0]==sid),SIZES[1]); toppings=[t for t in TOPPINGS if t[0] in selected]; total=pizza[2]+size[2]+sum(t[2] for t in toppings)+0.50
    return pizza,size,toppings,round(total,2)
def save_order(form):
    customer=form.get("customer",[""])[0]; comment=form.get("comment",[""])[0]; pizza,size,toppings,total=calc_order(form); con=sqlite3.connect(DB_PATH); cur=con.cursor()
    cur.execute("INSERT INTO orders(created_at,customer,pizza,size,toppings,total,comment,status) VALUES(?,?,?,?,?,?,?,?)",(now(),customer,pizza[1],size[1],", ".join(t[1] for t in toppings),total,comment,"neu")); oid=cur.lastrowid; con.commit(); con.close()
    tops=''.join(f"<li>{esc(t[1])}</li>" for t in toppings) or "<li>keine</li>"
    return f"<div class='mcard'><h2>Bestellung #{oid} simuliert</h2><p><b>{esc(pizza[1])}</b><br>{esc(size[1])}</p><ul>{tops}</ul><div class='price'>{total:.2f} €</div><p class='small'>Diese Bestellung erscheint im Küchen-/Ofen-GUI und im Buchungssystem.</p></div>"+feedback_form(customer)
def save_feedback(form):
    con=sqlite3.connect(DB_PATH); con.execute("INSERT INTO feedback(created_at,tester,observation,must_have,willingness,result) VALUES(?,?,?,?,?,?)",(now(),form.get("tester",[""])[0],form.get("observation",[""])[0],form.get("must_have",[""])[0],form.get("willingness",[""])[0],form.get("result",[""])[0])); con.commit(); con.close()
def label(status): return dict(ORDER_STEPS).get(status,status or "Neue Bestellung")
def next_status(s):
    ids=[x[0] for x in ORDER_STEPS]; return ids[min(ids.index(s)+1,len(ids)-1)] if s in ids else "tk_holen"
def update_status(form):
    oid=form.get("order_id",[""])[0]; action=form.get("action",["next"])[0]; con=sqlite3.connect(DB_PATH); row=con.execute("SELECT status FROM orders WHERE id=?",(oid,)).fetchone()
    if row: con.execute("UPDATE orders SET status=? WHERE id=?",("fertig" if action=="done" else next_status(row[0] or "neu"),oid)); con.commit()
    con.close()
def kitchen():
    con=sqlite3.connect(DB_PATH); rows=con.execute("SELECT id,created_at,customer,pizza,size,toppings,total,comment,COALESCE(status,'neu') FROM orders WHERE COALESCE(status,'neu')!='fertig' ORDER BY id ASC").fetchall(); done=con.execute("SELECT id,customer,pizza,total FROM orders WHERE COALESCE(status,'neu')='fertig' ORDER BY id DESC LIMIT 10").fetchall(); con.close()
    cards=""
    for r in rows:
        oid,created,customer,pizza,size,toppings,total,comment,status=r
        cards += f"<div class='card'><h2>Bestellung #{oid} <span class='status'>{esc(label(status))}</span></h2><p><b>Kunde:</b> {esc(customer or 'Testkunde')}<br><b>Pizza:</b> {esc(pizza)}<br><b>Größe:</b> {esc(size)}<br><b>Toppings:</b> {esc(toppings or 'keine')}<br><b>Betrag:</b> {total:.2f} €</p><form method='POST' action='/wagner/api/order_status'><input type='hidden' name='order_id' value='{oid}'><button>Nächster Arbeitsschritt</button></form><form method='POST' action='/wagner/api/order_status'><input type='hidden' name='order_id' value='{oid}'><input type='hidden' name='action' value='done'><button>Als fertig / geliefert markieren</button></form></div>"
    if not cards: cards="<div class='card'><h2>Keine offenen Bestellungen</h2></div>"
    done_html=''.join(f"<div class='card'>#{r[0]} – {esc(r[2])} – {esc(r[1])} – {r[3]:.2f} €</div>" for r in done) or "<p>Noch keine fertigen Bestellungen.</p>"
    return page("Küche",f"<div class='admin'><header><h1>Wagner Küchen-/Ofen-GUI</h1></header>{nav_web()}<main>{cards}<div class='card'><h2>Zuletzt fertig/geliefert</h2>{done_html}</div></main></div>",True)
def admin():
    con=sqlite3.connect(DB_PATH); orders=con.execute("SELECT id,created_at,customer,pizza,size,toppings,total,comment,COALESCE(status,'neu') FROM orders ORDER BY id DESC LIMIT 100").fetchall(); feedback=con.execute("SELECT created_at,tester,observation,must_have,willingness,result FROM feedback ORDER BY id DESC LIMIT 50").fetchall(); stats=[con.execute("SELECT COUNT(*) FROM orders").fetchone()[0],con.execute("SELECT COUNT(*) FROM orders WHERE COALESCE(status,'neu')!='fertig'").fetchone()[0],con.execute("SELECT COUNT(*) FROM orders WHERE COALESCE(status,'neu')='fertig'").fetchone()[0],con.execute("SELECT COALESCE(SUM(total),0) FROM orders").fetchone()[0],con.execute("SELECT COALESCE(SUM(total),0) FROM orders WHERE COALESCE(status,'neu')='fertig'").fetchone()[0]]; con.close()
    order_rows=''.join(f"<tr><td>#{r[0]}</td><td>{esc(r[1])}</td><td>{esc(r[2])}</td><td>{esc(r[3])}</td><td>{esc(r[4])}</td><td>{esc(r[5])}</td><td>{r[6]:.2f} €</td><td>{esc(label(r[8]))}</td><td>{esc(r[7])}</td></tr>" for r in orders)
    fb_rows=''.join(f"<tr><td>{esc(r[0])}</td><td>{esc(r[1])}</td><td>{esc(r[4])}</td><td>{esc(r[5])}</td><td>{esc(r[2])}</td><td>{esc(r[3])}</td></tr>" for r in feedback)
    body=f"<div class='admin'><header><h1>Wagner Buchungssystem / Betriebsansicht</h1></header>{nav_web()}<main><div class='grid'><div class='card'><h2>Bestellungen gesamt</h2><div class='price'>{stats[0]}</div></div><div class='card'><h2>Offen in Produktion</h2><div class='price'>{stats[1]}</div></div><div class='card'><h2>Fertig / geliefert</h2><div class='price'>{stats[2]}</div></div></div><div class='grid'><div class='card'><h2>Umsatz gebucht</h2><div class='price'>{stats[3]:.2f} €</div></div><div class='card'><h2>Umsatz fertig</h2><div class='price'>{stats[4]:.2f} €</div></div><div class='card'><h2>Testsystem</h2><p>Design-Sprint- und Buchungsansicht.</p></div></div><div class='card'><h2>Buchungsliste / Bestellungen</h2><table><tr><th>Nr.</th><th>Zeit</th><th>Kunde</th><th>Pizza</th><th>Größe</th><th>Toppings</th><th>Betrag</th><th>Status</th><th>Kommentar</th></tr>{order_rows}</table></div><div class='card'><h2>Design-Sprint-Feedback nach Bestellung</h2><table><tr><th>Zeit</th><th>Tester</th><th>Bereitschaft</th><th>Ergebnis</th><th>Beobachtung</th><th>Must-have</th></tr>{fb_rows}</table></div></main></div>"
    return page("Wagner Buchungssystem",body,True)
class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        path=urlparse(self.path).path
        if path in ["/","/wagner","/wagner/website"]: self.send_html(website())
        elif path in ["/wagner/app","/mobile/wagners"]: self.send_html(app_view())
        elif path in ["/wagner/kitchen","/kitchen"]: self.send_html(kitchen())
        elif path in ["/wagner/admin","/admin"]: self.send_html(admin())
        elif path.startswith("/assets/"): self.send_asset(path)
        elif path=="/manifest.json": self.send_json({"name":"Wagner's Pizza","short_name":"WagnerPizza","start_url":"/wagner/app","display":"standalone"})
        else: self.send_error(404)
    def do_POST(self):
        path=urlparse(self.path).path; form=parse_qs(self.rfile.read(int(self.headers.get("Content-Length",0))).decode("utf-8"))
        if path in ["/wagner/api/order","/api/order"]: self.send_html(app_view(save_order(form)))
        elif path in ["/wagner/api/feedback","/api/feedback"]: save_feedback(form); self.send_html(app_view("<div class='mcard'><b>Feedback gespeichert.</b></div>"))
        elif path in ["/wagner/api/order_status","/api/order_status"]: update_status(form); self.send_html(kitchen())
        else: self.send_error(404)
    def send_html(self,p):
        d=p.encode("utf-8"); self.send_response(200); self.send_header("Content-Type","text/html; charset=utf-8"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d)
    def send_json(self,o):
        d=json.dumps(o,ensure_ascii=False).encode("utf-8"); self.send_response(200); self.send_header("Content-Type","application/json; charset=utf-8"); self.send_header("Content-Length",str(len(d))); self.end_headers(); self.wfile.write(d)
    def send_asset(self,path):
        name = Path(path).name
        candidates = [
            ASSET_DIR / name,
            Path(name),
            Path.cwd() / "assets" / name,
            Path.cwd() / name,
        ]
        fp = next((p for p in candidates if p.exists()), None)
        if fp is None:
            self.send_error(404)
            return
        data = fp.read_bytes()
        ctype = mimetypes.guess_type(str(fp))[0] or "application/octet-stream"
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)
if __name__=="__main__":
    init_db(); print(f"Wagner's Pizza Shop Webseite + App läuft unter http://127.0.0.1:{PORT}/wagner/website"); print(f"Kunden-App: http://127.0.0.1:{PORT}/wagner/app"); print(f"Küchen-/Ofen-GUI: http://127.0.0.1:{PORT}/wagner/kitchen"); print(f"Buchungssystem: http://127.0.0.1:{PORT}/wagner/admin"); HTTPServer((HOST,PORT),Handler).serve_forever()

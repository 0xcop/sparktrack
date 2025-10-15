from fastapi import FastAPI, Request, Form, HTTPException, Response
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .db import get_conn, init_db
from .auth import create_token, current_user

app = FastAPI(title="sparktrack")
templates = Jinja2Templates(directory="app/templates")
app.mount("/static", StaticFiles(directory="app/static"), name="static")

@app.on_event("startup")
def startup():
    init_db()

# ---------- HTML UI ----------
@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    user = current_user(request)
    conn = get_conn()
    cur = conn.cursor()
    projects = []; me = None
    if user:
        cur.execute("SELECT id, username FROM users WHERE username=?", (user,))
        me = cur.fetchone()
        cur.execute("SELECT * FROM projects WHERE owner_id=?", (me["id"],))
        projects = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("home.html", {"request": request, "user": user, "projects": projects, "me": me})

@app.get("/signup", response_class=HTMLResponse)
def signup_form(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

@app.post("/signup")
def signup(username: str = Form(...), password: str = Form(...)):
    conn = get_conn(); cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users(username, password) VALUES(?,?)", (username, password))
        conn.commit()
    except Exception:
        raise HTTPException(status_code=400, detail="Username taken")
    finally:
        conn.close()
    return RedirectResponse("/login", status_code=303)

@app.get("/login", response_class=HTMLResponse)
def login_form(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@app.post("/login")
def login(response: Response, username: str = Form(...), password: str = Form(...)):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username=? AND password=?", (username, password))
    row = cur.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=401, detail="Bad credentials")
    token = create_token(username)
    r = RedirectResponse("/", status_code=303)
    r.set_cookie("token", token, httponly=True, max_age=60*60*24*7, samesite="lax")
    return r

@app.post("/logout")
def logout():
    r = RedirectResponse("/", status_code=303)
    r.delete_cookie("token")
    return r

@app.post("/projects")
def create_project(request: Request, name: str = Form(...)):
    user = current_user(request)
    if not user: raise HTTPException(401, "Login required")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT id FROM users WHERE username=?", (user,))
    me = cur.fetchone()
    cur.execute("INSERT INTO projects(name, owner_id) VALUES(?,?)", (name, me["id"]))
    conn.commit(); conn.close()
    return RedirectResponse("/", status_code=303)

@app.get("/project/{pid}", response_class=HTMLResponse)
def project_view(pid: int, request: Request):
    user = current_user(request)
    if not user:
        return RedirectResponse("/login", status_code=303)
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT * FROM projects WHERE id=?", (pid,))
    proj = cur.fetchone()
    cur.execute("SELECT * FROM issues WHERE project_id=? ORDER BY id DESC", (pid,))
    issues = cur.fetchall()
    conn.close()
    return templates.TemplateResponse("project.html", {"request": request, "project": proj, "issues": issues})

@app.post("/issues")
def create_issue(request: Request, project_id: int = Form(...), title: str = Form(...)):
    user = current_user(request)
    if not user: raise HTTPException(401, "Login required")
    conn = get_conn(); cur = conn.cursor()
    cur.execute("INSERT INTO issues(project_id, title) VALUES(?,?)", (project_id, title))
    conn.commit(); conn.close()
    return RedirectResponse(f"/project/{project_id}", status_code=303)

@app.post("/issues/{iid}/toggle")
def toggle_issue(iid: int):
    conn = get_conn(); cur = conn.cursor()
    cur.execute("SELECT status, project_id FROM issues WHERE id=?", (iid,))
    row = cur.fetchone()
    if not row: raise HTTPException(404, "Issue not found")
    new = "closed" if row["status"] == "open" else "open"
    cur.execute("UPDATE issues SET status=? WHERE id=?", (new, iid))
    conn.commit(); conn.close()
    return RedirectResponse(f"/project/{row['project_id']}", status_code=303)

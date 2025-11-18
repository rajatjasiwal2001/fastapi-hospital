from fastapi import Depends, FastAPI, Form, HTTPException, Request, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
import pymysql

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.add_middleware(SessionMiddleware, secret_key="super-secret-session-key")

USERS_DB = {
    "admin": "admin123",
    "rajat.jaiswalmgs2@gmail.com": "rajat123",
}


def get_current_user(request: Request):
    user = request.session.get("user")
    if not user:
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Not authenticated",
            headers={"Location": "/login"},
        )
    return user


def connection():
    conn = pymysql.connect(
        host="localhost",
        user="rajatjaiswal",
        password="rajat@2004",
        database="hospital",
        cursorclass=pymysql.cursors.DictCursor
    )
    return conn


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = request.session.get("user")
    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "message": "Hospital Patient Record System",
            "user": user,
        },
    )


@app.get("/login", response_class=HTMLResponse)
async def login_form(request: Request):
    if request.session.get("user"):
        return RedirectResponse("/patients", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request, "error": None})


@app.post("/login", response_class=HTMLResponse)
async def login(request: Request, username: str = Form(...), password: str = Form(...)):
    username = username.strip().lower()
    password = password.strip()
    expected_password = USERS_DB.get(username)
    if not expected_password or expected_password != password:
        return templates.TemplateResponse(
            "login.html",
            {"request": request, "error": "Invalid username or password."},
            status_code=400,
        )
    request.session["user"] = username
    return RedirectResponse("/patients", status_code=303)


@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/patients", response_class=HTMLResponse)
async def get_patients(request: Request):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients")
    patients = cursor.fetchall()
    conn.close()
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "patients": patients, "user": request.session.get("user")},
    )


@app.get("/patients/add", response_class=HTMLResponse)
async def add_patient_form(request: Request, user: str = Depends(get_current_user)):
    return templates.TemplateResponse("form.html", {
        "request": request,
        "action_url": "/patients/add",
        "patient": None,
        "title": "Add Patient",
        "user": user,
    })


@app.post("/patients/add", response_class=HTMLResponse)
async def add_patient(
    request: Request,
    user: str = Depends(get_current_user),
    name: str = Form(...),
    age: int = Form(...),
    disease: str = Form(...),
    address: str = Form(...)
):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO patients (name, age, disease, address) VALUES (%s,%s,%s,%s)",
        (name, age, disease, address),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/patients", status_code=303)


@app.get("/patients/{patient_id}", response_class=HTMLResponse)
async def get_patient(request: Request, patient_id: int):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return templates.TemplateResponse(
        "view.html",
        {"request": request, "patient": patient, "user": request.session.get("user")},
    )


@app.get("/patients/update/{patient_id}", response_class=HTMLResponse)
async def update_patient_form(
    request: Request, patient_id: int, user: str = Depends(get_current_user)
):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id=%s", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    if not patient:
        raise HTTPException(status_code=404, detail="Patient not found")
    return templates.TemplateResponse(
        "form.html",
        {
            "request": request,
            "action_url": f"/patients/update/{patient_id}",
            "patient": patient,
            "title": "Update Patient",
            "user": user,
        },
    )


@app.post("/patients/update/{patient_id}", response_class=HTMLResponse)
async def update_patient(
    request: Request,
    patient_id: int,
    user: str = Depends(get_current_user),
    name: str = Form(...),
    age: int = Form(...),
    disease: str = Form(...),
    address: str = Form(...)
):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE patients SET name=%s, age=%s, disease=%s, address=%s WHERE id=%s",
        (name, age, disease, address, patient_id),
    )
    conn.commit()
    conn.close()
    return RedirectResponse("/patients", status_code=303)


@app.post("/patients/delete/{patient_id}", response_class=HTMLResponse)
async def delete_patient(request: Request, patient_id: int, user: str = Depends(get_current_user)):
    conn = connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM patients WHERE id=%s", (patient_id,))
    conn.commit()
    conn.close()
    return RedirectResponse("/patients", status_code=303)


if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main1:app", host="0.0.0.0", port=port)


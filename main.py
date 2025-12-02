from operator import itemgetter

from fastapi import FastAPI, HTTPException

import pyodbc
from pydantic import BaseModel
from pydantic import BaseModel, constr, condecimal
from typing import Optional
def connect():
    conn = pyodbc.connect(
        "Driver={ODBC Driver 18 for SQL Server};"
        "Server=tcp:studentdataserver.database.windows.net,1433;"
        "Database=StudentDatabaseSysA;"
        "Uid=databaseAdmin;"
        "Pwd=Piisgood12;"
        "Encrypt=yes;"
        "TrustServerCertificate=no;"
        "Connection Timeout=30;"
    )
    return conn



print("Connected!")

def getCursor():
    conn = connect()
    return conn.cursor(), conn
app = FastAPI()

#Database Design
#ID -

class Student(BaseModel):
    first_name: constr(min_length=1, max_length=50)
    last_name: constr(min_length=1, max_length=50)
    grade: constr(min_length=2, max_length=2)          # FR, SO, JR, SR
    credit_hours: int
    gpa: condecimal(max_digits=3, decimal_places=2)

class StudentUpdate(BaseModel):
    first_name: Optional[str]
    last_name: Optional[str]
    grade: Optional[str]
    credit_hours: Optional[int]
    gpa: Optional[condecimal(max_digits=3, decimal_places=2)]
@app.post("/addstudent")
def create_student(student: Student):
    cursor, conn = getCursor()
    try:
        # INSERT and get new ID immediately
        cursor.execute(
            "INSERT INTO Students (first_name, last_name, grade, credit_hours, gpa) "
            "OUTPUT INSERTED.id "
            "VALUES (?, ?, ?, ?, ?)",
            student.first_name,
            student.last_name,
            student.grade,
            student.credit_hours,
            student.gpa
        )
        row = cursor.fetchone()
        if not row or row[0] is None:
            raise HTTPException(status_code=500, detail="Failed to get new ID from database")

        new_id = int(row[0])

        # Generate student_id
        generated_student_id = f"A{new_id:05d}"

        # Update student_id in the table
        cursor.execute(
            "UPDATE Students SET student_id=? WHERE id=?",
            generated_student_id,
            new_id
        )
        conn.commit()

        return {"id": new_id, "student_id": generated_student_id}

    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        cursor.close()
        conn.close()
@app.get("/getstudents")
def get_all_students():
    cursor, conn = getCursor()
    cursor.execute("SELECT * FROM Students")
    rows = cursor.fetchall()
    return [
        {
        "student_id": row[1],

        "first_name": row[2],
        "last_name": row[3],

        }
        for row in rows
    ]

@app.get("/getstudent/{student_id}")
def get_student(student_id: str):
    cursor, conn = getCursor()
    try:
        cursor.execute(
            "SELECT id, student_id, first_name, last_name, grade, credit_hours, gpa"
            " FROM Students WHERE student_id=?",
            student_id

        )
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail=f"A student with {student_id} was not found")

        student_data = {
            "student_id": row[1],
            "first_name": row[2],
            "last_name": row[3],
            "grade": row[4],
            "credit_hours": row[5],
            "gpa": float(row[6])  # convert Decimal to float for JSON
        }
        return student_data
    finally:
        cursor.close()
        conn.close()

@app.put("/editstudent/{student_id}")
def update_student(student_id: str, student: StudentUpdate):
    cursor, conn = getCursor()
    try:

        setClauses = []
        values = []

        if student.first_name is not None:
            setClauses.append("first_name=?")
            values.append(student.first_name)
        if student.last_name is not None:
            setClauses.append("last_name=?")
            values.append(student.last_name)
        if student.grade is not None:
            setClauses.append("grade=?")
            values.append(student.grade)
        if student.credit_hours is not None:
            setClauses.append("credit_hours=?")
            values.append(student.credit_hours)
        if student.gpa is not None:
            setClauses.append("gpa=?")
            values.append(student.gpa)

        if not setClauses:
            raise HTTPException(status_code=400, detail="No fields to update")

        values.append(student_id)  # for WHERE clause
        sql = f"UPDATE Students SET {', '.join(setClauses)} WHERE student_id=?"
        cursor.execute(sql, *values)
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")

        return {"message": f"Student {student_id} updated successfully"}

    finally:
        cursor.close()
        conn.close()

@app.delete("/deletestudent/{student_id}")
def delete_student(student_id: str):

    cursor, conn = getCursor()
    try:
        cursor.execute(
            "DELETE FROM Students WHERE student_id=?", student_id
        )
        conn.commit()

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail=f"Student {student_id} not found")
        return {"message": f"Student {student_id} deleted successfully"}
    finally:
        cursor.close()
        conn.close()


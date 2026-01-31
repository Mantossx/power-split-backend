import os
import shutil
from typing import List, Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import desc
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import engine, Base, get_db
from app.services import ocr_core
from app import models, schemas

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Power Split Bill API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    price: Optional[float] = None

@app.post("/scan-and-save/")
async def scan_and_save(file: UploadFile = File(...), db: Session = Depends(get_db)):
    temp_filename = f"temp_{file.filename}"
    with open(temp_filename, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    with open(temp_filename, "rb") as f:
        extracted_items = ocr_core.process_receipt(f.read())

    sub_total = sum(item['price'] for item in extracted_items)
    new_bill = models.Bill(title=f"Struk {file.filename}", sub_total=sub_total)
    db.add(new_bill)
    db.commit()
    db.refresh(new_bill)

    file_ext = file.filename.split(".")[-1]
    saved_filename = f"{new_bill.id}.{file_ext}"
    shutil.move(temp_filename, os.path.join(UPLOAD_DIR, saved_filename))

    for item in extracted_items:
        new_item = models.BillItem(
            bill_id=new_bill.id, name=item['name'],
            price=item['price'], quantity=item.get('qty', 1)
        )
        db.add(new_item)
    db.commit()
    return {"bill_id": new_bill.id}

@app.get("/bills/")
def get_all_bills(db: Session = Depends(get_db)):
    bills = db.query(models.Bill).order_by(desc(models.Bill.id)).all()
    return bills


@app.put("/bill-items/{item_id}")
def update_item(item_id: int, item_data: ItemUpdate, db: Session = Depends(get_db)):
    item = db.query(models.BillItem).filter(models.BillItem.id == item_id).first()
    if not item: raise HTTPException(status_code=404, detail="Item not found")

    if item_data.name: item.name = item_data.name
    if item_data.price is not None: item.price = item_data.price

    bill = db.query(models.Bill).filter(models.Bill.id == item.bill_id).first()
    all_items = db.query(models.BillItem).filter(models.BillItem.bill_id == item.bill_id).all()
    db.commit()

    # Recalculate Bill Subtotal
    bill.sub_total = sum(i.price for i in all_items)
    db.commit()

    return item
@app.delete("/bill-items/{item_id}")
def delete_item(item_id: int, db: Session = Depends(get_db)):
    item = db.query(models.BillItem).filter(models.BillItem.id == item_id).first()
    if not item: raise HTTPException(status_code=404, detail="Item not found")

    bill_id = item.bill_id
    db.delete(item)
    db.commit()

    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    remaining_items = db.query(models.BillItem).filter(models.BillItem.bill_id == bill_id).all()
    bill.sub_total = sum(i.price for i in remaining_items)
    db.commit()

    return {"status": "deleted"}

@app.delete("/bills/{bill_id}")
def delete_bill(bill_id: int, db: Session = Depends(get_db)):
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill:
        raise HTTPException(status_code=404, detail="Bill tidak ditemukan")

    # 1. Hapus File Gambar Fisik (Cleanup)
    for ext in ["jpg", "jpeg", "png", "webp"]:
        file_path = os.path.join(UPLOAD_DIR, f"{bill_id}.{ext}")
        if os.path.exists(file_path):
            os.remove(file_path) # Hapus file dari laptop

    # 2. Hapus Data dari Database
    # Karena kita pakai SQLAlchemy, items/participants biasanya terhapus otomatis (Cascade)
    # atau kita hapus manual parent-nya:
    db.delete(bill)
    db.commit()

    return {"status": "deleted", "bill_id": bill_id}

@app.post("/bills/{bill_id}/participants/")
def add_participant(bill_id: int, participant: schemas.ParticipantCreate, db: Session = Depends(get_db)):
    new_user = models.Participant(bill_id=bill_id, name=participant.name)
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.post("/assignments/")
def assign_item(assignment: schemas.AssignmentCreate, db: Session = Depends(get_db)):
    existing = db.query(models.ItemAssignment).filter(
        models.ItemAssignment.bill_item_id == assignment.bill_item_id,
        models.ItemAssignment.participant_id == assignment.participant_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed"}
    else:
        new_assign = models.ItemAssignment(bill_item_id=assignment.bill_item_id,
                                           participant_id=assignment.participant_id)
        db.add(new_assign)
        db.commit()
        return {"status": "added"}


@app.post("/bills/{bill_id}/calculate-split/")
def calculate_split(bill_id: int, tax_rate: float = 0.11, service_rate: float = 0.05, db: Session = Depends(get_db)):
    items = db.query(models.BillItem).filter(models.BillItem.bill_id == bill_id).all()
    total_multiplier = 1 + tax_rate + service_rate
    final_result = {}

    for item in items:
        assignments = db.query(models.ItemAssignment).filter(models.ItemAssignment.bill_item_id == item.id).all()
        if not assignments: continue

        splitter_count = len(assignments)
        price_per_person = item.price / splitter_count

        for assign in assignments:
            p_id = assign.participant_id
            participant = db.query(models.Participant).filter(models.Participant.id == p_id).first()
            if not participant: continue

            if participant.name not in final_result:
                final_result[participant.name] = {"base_price": 0, "final_price": 0, "items": []}

            final_result[participant.name]["base_price"] += price_per_person
            final_result[participant.name]["items"].append(f"{item.name} (1/{splitter_count})")

    grand_total_calculated = 0
    for name, data in final_result.items():
        data["final_price"] = round(data["base_price"] * total_multiplier, 2)
        grand_total_calculated += data["final_price"]

    return {
        "split_details": final_result,
        "grand_total_estimation": grand_total_calculated
    }


@app.get("/bills/{bill_id}/details/")
def get_bill_details(bill_id: int, db: Session = Depends(get_db)):
    bill = db.query(models.Bill).filter(models.Bill.id == bill_id).first()
    if not bill: raise HTTPException(status_code=404)
    items = db.query(models.BillItem).filter(models.BillItem.bill_id == bill_id).all()

    assignments_data = {}
    for item in items:
        assigns = db.query(models.ItemAssignment).filter(models.ItemAssignment.bill_item_id == item.id).all()
        assignments_data[item.id] = [a.participant_id for a in assigns]

    participants = db.query(models.Participant).filter(models.Participant.bill_id == bill_id).all()

    image_url = None
    for ext in ["jpg", "jpeg", "png", "webp"]:
        if os.path.exists(f"{UPLOAD_DIR}/{bill_id}.{ext}"):
            image_url = f"http://127.0.0.1:8000/static/{bill_id}.{ext}"
            break

    return {
        "id": bill.id,
        "title": bill.title,
        "sub_total": bill.sub_total,
        "image_url": image_url,
        "items": items,
        "assignments": assignments_data,
        "participants": participants
    }


@app.post("/system/hard-reset/")
def hard_reset_system(db: Session = Depends(get_db)):
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    for filename in os.listdir(UPLOAD_DIR):
        file_path = os.path.join(UPLOAD_DIR, filename)
        if os.path.isfile(file_path):
            os.remove(file_path)

    return {"status": "System Factory Reset Completed"}

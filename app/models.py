from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Bill(Base):
    __tablename__ = "bills"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    sub_total = Column(Float, default=0)
    tax_service_amount = Column(Float, default=0)
    grand_total = Column(Float, default=0)

    items = relationship("BillItem", back_populates="bill")
    participants = relationship("Participant", back_populates="bill")


class BillItem(Base):
    __tablename__ = "bill_items"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    name = Column(String)
    price = Column(Float)
    quantity = Column(Integer, default=1)

    bill = relationship("Bill", back_populates="items")
    assignments = relationship("ItemAssignment", back_populates="item")


class Participant(Base):
    __tablename__ = "participants"
    id = Column(Integer, primary_key=True, index=True)
    bill_id = Column(Integer, ForeignKey("bills.id"))
    name = Column(String)

    bill = relationship("Bill", back_populates="participants")
    assignments = relationship("ItemAssignment", back_populates="participant")


class ItemAssignment(Base):
    __tablename__ = "assignments"
    id = Column(Integer, primary_key=True, index=True)
    bill_item_id = Column(Integer, ForeignKey("bill_items.id"))
    participant_id = Column(Integer, ForeignKey("participants.id"))

    item = relationship("BillItem", back_populates="assignments")
    participant = relationship("Participant", back_populates="assignments")